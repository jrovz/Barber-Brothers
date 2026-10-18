"""Servicio de reservas: crea una cita pendiente de confirmación.

Lo usan la ruta web `POST /api/agendar-cita` y, más adelante, el chatbot. No conoce HTTP
ni cookies: recibe un diccionario con los datos y devuelve un `ResultadoReserva`; cada
canal decide cómo mostrarlo.

La regla que más importa: dos reservas simultáneas para el mismo barbero no pueden
ocupar el mismo horario. Se logra bloqueando la fila del barbero hasta el commit
(`with_for_update`), por eso TODA salida con error hace `rollback()`: así se libera
el bloqueo. No mover esos rollback sin entender esto.
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from flask import current_app

from app import db
from app.models.barbero import Barbero
from app.models.cliente import Cita, Cliente
from app.models.email import send_appointment_confirmation_email
from app.models.servicio import Servicio
from app.utils.tiempo import ahora_negocio

CAMPOS_REQUERIDOS = ['barbero_id', 'servicio_id', 'fecha', 'hora', 'nombre', 'email', 'telefono']

# Estados de cita que ocupan el horario al reservar. Ojo: Cita.ESTADOS_OCUPAN_HORARIO
# (usado al calcular los horarios libres) también incluye 'expirada'; hoy las dos reglas
# difieren y se conserva así a propósito.
ESTADOS_QUE_BLOQUEAN_RESERVA = ('confirmada', 'pendiente_confirmacion')


@dataclass
class ErrorReserva:
    codigo: str
    mensaje: str
    http: int
    extra: dict = field(default_factory=dict)

    def cuerpo(self):
        """JSON de error tal como lo devuelve la API web."""
        return {'error': self.mensaje, **self.extra}


@dataclass
class ResultadoReserva:
    cita: Cita | None = None
    token: str | None = None
    error: ErrorReserva | None = None

    @property
    def ok(self):
        return self.error is None


def _fallo(codigo, mensaje, http=400, **extra):
    return ResultadoReserva(error=ErrorReserva(codigo, mensaje, http, extra))


def crear_cita(datos, *, enviar_correo=True):
    """Crea una cita en estado `pendiente_confirmacion` y manda el correo de confirmación.

    `datos` usa las mismas claves que la API: barbero_id, servicio_id, fecha (YYYY-MM-DD),
    hora (HH:MM), nombre, email, telefono y, opcionales, fecha_nacimiento y notas.
    """
    try:
        return _crear_cita(datos, enviar_correo)
    except ValueError as ve:
        # Fecha u hora mal escritas, ids no numéricos, etc.
        db.session.rollback()
        current_app.logger.error(f"Error de formato en agendar_cita: {str(ve)}")
        return _fallo('formato_invalido', f'Formato de fecha u hora inválido: {str(ve)}')


def _crear_cita(data, enviar_correo):
    for campo in CAMPOS_REQUERIDOS:
        if campo not in data or not data[campo]:
            current_app.logger.error(f"Campo faltante o vacío: {campo}")
            return _fallo('campo_faltante', f'Falta el campo o está vacío: {campo}')

    fecha_hora = datetime.strptime(f"{data['fecha']} {data['hora']}", '%Y-%m-%d %H:%M')
    # Hora local del negocio (por defecto Colombia, UTC-5), no la del servidor.
    if fecha_hora < ahora_negocio() - timedelta(minutes=5):
        return _fallo('fecha_pasada', 'No se puede agendar una cita en una fecha u hora pasada.')

    # Bloquear la fila del barbero hasta el commit: dos reservas simultáneas para el
    # mismo barbero se atienden en fila y la segunda ve la cita de la primera.
    # (En PostgreSQL es SELECT ... FOR UPDATE; SQLite lo ignora.)
    barbero = (Barbero.query
               .filter_by(id=int(data['barbero_id']))
               .with_for_update()
               .first())
    if not barbero or not barbero.activo:
        db.session.rollback()
        return _fallo('barbero_no_disponible', 'El barbero seleccionado no está disponible.')

    servicio = db.session.get(Servicio, int(data['servicio_id']))
    if not servicio or not servicio.activo:
        db.session.rollback()
        return _fallo('servicio_no_disponible', 'El servicio seleccionado no está disponible.')

    duracion_servicio = servicio.get_duracion_minutos()
    inicio_nueva_cita = fecha_hora
    fin_nueva_cita = inicio_nueva_cita + timedelta(minutes=duracion_servicio)

    fecha_inicio_dia = datetime.combine(fecha_hora.date(), datetime.min.time())
    fecha_fin_dia = fecha_inicio_dia + timedelta(days=1)

    citas_del_dia = Cita.query.filter(
        Cita.barbero_id == int(data['barbero_id']),
        Cita.estado.in_(ESTADOS_QUE_BLOQUEAN_RESERVA),
        Cita.fecha >= fecha_inicio_dia,
        Cita.fecha < fecha_fin_dia
    ).all()

    hay_solapamiento = False
    for cita_existente in citas_del_dia:
        inicio_existente = cita_existente.fecha
        fin_existente = inicio_existente + timedelta(minutes=cita_existente.duracion or 30)

        # La nueva cita no debe empezar antes de que termine una existente
        # ni terminar después de que empiece otra existente.
        if not (fin_nueva_cita <= inicio_existente or inicio_nueva_cita >= fin_existente):
            hay_solapamiento = True
            current_app.logger.warning(f"Solapamiento detectado con cita ID {cita_existente.id}: "
                                       f"Existente: {inicio_existente} - {fin_existente}, "
                                       f"Nueva: {inicio_nueva_cita} - {fin_nueva_cita}")
            break

    if hay_solapamiento:
        db.session.rollback()  # liberar el bloqueo del barbero
        current_app.logger.warning(f"CONFLICTO DE HORARIO - Barbero {data['barbero_id']}, "
                                   f"Horario solicitado: {fecha_hora} - {fin_nueva_cita}, "
                                   f"Servicio: {data['servicio_id']} ({duracion_servicio}min)")
        return _fallo(
            'conflicto_horario',
            'Este horario se solapa con otra cita. Por favor, selecciona otro horario.',
            http=409,
            conflict_details={
                'barbero_id': data['barbero_id'],
                'horario_solicitado': fecha_hora.isoformat(),
                'duracion_servicio': duracion_servicio,
            },
        )

    fecha_nacimiento = None
    if data.get('fecha_nacimiento'):
        try:
            fecha_nacimiento = datetime.strptime(data['fecha_nacimiento'], '%Y-%m-%d').date()
            if fecha_nacimiento > datetime.utcnow().date():
                db.session.rollback()
                return _fallo('nacimiento_futuro', 'La fecha de nacimiento no puede ser futura.')
        except ValueError:
            db.session.rollback()
            return _fallo('nacimiento_invalido',
                          'Formato de fecha de nacimiento inválido. Use YYYY-MM-DD.')

    cliente = Cliente.query.filter_by(email=data['email']).first()
    if not cliente:
        cliente = Cliente(
            nombre=data['nombre'],
            email=data['email'],
            telefono=data['telefono'],
            fecha_nacimiento=fecha_nacimiento
        )
        db.session.add(cliente)
        db.session.flush()  # para obtener el ID del cliente nuevo
    else:
        # Cliente existente: se actualizan sus datos con los de esta reserva.
        cliente.nombre = data['nombre']
        cliente.telefono = data['telefono']
        if fecha_nacimiento:
            cliente.fecha_nacimiento = fecha_nacimiento

    # Precio que se cobrará según el barbero elegido (puede ser personalizado).
    from app.utils.pricing import obtener_precio_servicio
    precio_info = obtener_precio_servicio(int(data['barbero_id']), int(data['servicio_id']))

    if precio_info and not precio_info['servicio_activo_para_barbero']:
        current_app.logger.warning(
            f"Intento de reserva de servicio desactivado - Barbero: {data['barbero_id']}, "
            f"Servicio: {data['servicio_id']}"
        )
        db.session.rollback()
        return _fallo('barbero_sin_servicio', 'Este barbero no ofrece este servicio actualmente.')

    if precio_info:
        precio_cobrado = precio_info['precio']
        es_precio_personalizado = precio_info['es_personalizado']
    else:
        precio_cobrado = servicio.precio if servicio else 0
        es_precio_personalizado = False

    nueva_cita = Cita(
        cliente_id=cliente.id,
        barbero_id=int(data['barbero_id']),
        servicio_id=int(data['servicio_id']),
        fecha=fecha_hora,
        estado='pendiente_confirmacion',
        duracion=duracion_servicio,
        precio_cobrado=precio_cobrado,
        es_precio_personalizado=es_precio_personalizado,
        notas=data.get('notas', '')
    )
    db.session.add(nueva_cita)
    db.session.commit()  # commit para obtener el ID de nueva_cita

    token = nueva_cita.generate_confirmation_token()
    current_app.logger.info(f"CITA CREADA EXITOSAMENTE - ID: {nueva_cita.id}, "
                            f"Cliente ID: {cliente.id}, Barbero: {data['barbero_id']}, "
                            f"Fecha: {fecha_hora}, Servicio: {data['servicio_id']}, "
                            f"Duración: {duracion_servicio}min. Token generado, enviando correo.")

    if enviar_correo:
        send_appointment_confirmation_email(
            cliente_email=cliente.email,
            cliente_nombre=cliente.nombre,
            cita=nueva_cita,
            token=token
        )

    return ResultadoReserva(cita=nueva_cita, token=token)
