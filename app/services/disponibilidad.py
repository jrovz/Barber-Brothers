"""Servicio de disponibilidad: horarios libres de un barbero en una fecha.

Lo usan la ruta web `GET /api/disponibilidad/<barbero_id>/<fecha>` y, más adelante, las
herramientas del chatbot. Solo lee; no sabe de HTTP.
"""
from dataclasses import dataclass, field
from datetime import date

from flask import current_app

from app.models.cliente import Cita
from app.models.servicio import Servicio
from app.utils.tiempo import ahora_negocio

DURACION_POR_DEFECTO = 30


@dataclass
class ResultadoDisponibilidad:
    barbero_nombre: str
    fecha: date
    horarios: list = field(default_factory=list)  # 'HH:MM' libres, en orden
    duracion_servicio: int = DURACION_POR_DEFECTO
    mensaje: str = ''


def horarios_libres(barbero, fecha, servicio_id=None, *, excluir_pasadas=False, etiqueta_fecha=None):
    """Horarios en que `barbero` puede atender el día `fecha` un servicio de esa duración.

    barbero: objeto Barbero ya cargado (el llamador decide qué hacer si no existe).
    servicio_id: define la duración; sin él, o si no existe, se usan 30 minutos.
    excluir_pasadas: si es True, descarta las horas que ya pasaron (según la hora local
        del negocio). La web no lo usa porque la reserva ya rechaza fechas pasadas;
        el chat sí, para no ofrecer "las 9:00" a las 3 p. m.
    etiqueta_fecha: texto de la fecha para los mensajes (por defecto YYYY-MM-DD).
    """
    etiqueta = etiqueta_fecha or fecha.isoformat()
    duracion = DURACION_POR_DEFECTO

    if servicio_id:
        servicio = Servicio.query.get(servicio_id)
        if servicio:
            duracion = servicio.get_duracion_minutos()
            current_app.logger.info(f"Servicio '{servicio.nombre}': {duracion} minutos")
        else:
            current_app.logger.warning(f"Servicio con ID {servicio_id} no encontrado. Usando duración por defecto.")
    else:
        current_app.logger.warning("No se proporcionó servicio_id. Usando duración por defecto.")

    # Limpiar citas expiradas antes de calcular, para trabajar con datos actualizados.
    try:
        limpiadas = Cita.limpiar_citas_expiradas()
        if limpiadas > 0:
            current_app.logger.info(f"Limpieza automática: {limpiadas} citas expiradas")
    except Exception as e:
        current_app.logger.warning(f"Error en limpieza automática de citas: {e}")

    current_app.logger.info(
        f"Solicitando horarios disponibles para barbero {barbero.id}, fecha {fecha}, duración {duracion}min")

    slots = barbero.obtener_horarios_disponibles(fecha, duracion)
    horarios = [slot['hora'] for slot in slots if slot['disponible']]

    if excluir_pasadas:
        ahora = ahora_negocio()
        if fecha < ahora.date():
            horarios = []
        elif fecha == ahora.date():
            horarios = [h for h in horarios if h >= ahora.strftime('%H:%M')]

    mensaje = f'Horarios disponibles para {barbero.nombre} el {etiqueta}'
    if not horarios:
        if not barbero.get_disponibilidad_por_dia(fecha.weekday()):
            mensaje = f"{barbero.nombre} no tiene horario configurado para este día."
        else:
            mensaje = f"No hay horarios disponibles para {barbero.nombre} el {etiqueta} con duración de {duracion} min."

    current_app.logger.info(
        f"Disponibilidad - Barbero: {barbero.nombre}, Fecha: {etiqueta}, Servicio: {servicio_id}, "
        f"Duración: {duracion}min, Horarios encontrados: {len(horarios)}")

    return ResultadoDisponibilidad(
        barbero_nombre=barbero.nombre,
        fecha=fecha,
        horarios=horarios,
        duracion_servicio=duracion,
        mensaje=mensaje,
    )
