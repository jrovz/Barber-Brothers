from app import db
from datetime import datetime, timedelta # Asegúrate que timedelta esté importado
from flask import current_app
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
from app.models.barbero import Barbero
from app.models.servicio import Servicio # Importar Servicio
from sqlalchemy import event

class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False, index=True)
    telefono = db.Column(db.String(20))
    creado = db.Column(db.DateTime, default=datetime.utcnow)
    ultima_visita = db.Column(db.DateTime, nullable=True)
    total_visitas = db.Column(db.Integer, default=0)
    segmento = db.Column(db.String(50), default='nuevo')  # nuevo, ocasional, recurrente, vip
    fuente_captacion = db.Column(db.String(50), nullable=True)  # web, redes_sociales, recomendacion, walk_in
    citas = db.relationship('Cita', backref='cliente', lazy='dynamic')
    mensajes = db.relationship('Mensaje', backref='cliente', lazy='dynamic')
    
    def __repr__(self):
        return f'<Cliente {self.nombre}>'
    
    def clasificar_segmento(self):
        """Clasifica al cliente según su patrón de visitas"""
        today = datetime.utcnow()
        
        # Asegurar que total_visitas no sea None
        if self.total_visitas is None:
            self.total_visitas = 0
        
        # Sin visitas anteriores
        if not self.ultima_visita:
            self.segmento = 'nuevo'
            return self.segmento
            
        # Calcula días desde última visita
        dias_desde_ultima = (today - self.ultima_visita).days
        
        # Clasificación por frecuencia y total de visitas
        if self.total_visitas >= 10:
            self.segmento = 'vip'
        elif self.total_visitas >= 5:
            if dias_desde_ultima <= 45:
                self.segmento = 'recurrente'
            else:
                self.segmento = 'inactivo'
        elif self.total_visitas >= 2:
            if dias_desde_ultima <= 60:
                self.segmento = 'ocasional'
            else:
                self.segmento = 'inactivo'
        else:
            self.segmento = 'nuevo'
            
        return self.segmento

class Mensaje(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    asunto = db.Column(db.String(150))
    mensaje = db.Column(db.Text, nullable=False)
    leido = db.Column(db.Boolean, default=False)
    creado = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Mensaje {self.id}>'

# Corregir la clase Cita
class Cita(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    barbero_id = db.Column(db.Integer, db.ForeignKey('barbero.id'), nullable=False)
    servicio_id = db.Column(db.Integer, db.ForeignKey('servicio.id'), nullable=True)
    fecha = db.Column(db.DateTime, nullable=False)
    estado = db.Column(db.String(30), default='pendiente_confirmacion', nullable=False) # Modificado: pendiente_confirmacion, confirmada, cancelada, completada, expirada
    creado = db.Column(db.DateTime, default=datetime.utcnow)
    duracion = db.Column(db.Integer, default=30)
    notas = db.Column(db.Text, nullable=True)
    confirmed_at = db.Column(db.DateTime, nullable=True) # Hora de confirmación    # Relaciones
    # cliente ya está en Cliente model via backref='cliente'
    # barbero ya está en Barbero model via backref='barbero'
    servicio_rel = db.relationship('Servicio', backref='citas_servicio', foreign_keys=[servicio_id]) # Cambiado backref para evitar conflicto si Servicio tiene otras citas
    
    def actualizar_segmentacion_cliente(self):
        """Actualiza la segmentación del cliente cuando se completa una cita"""
        if self.estado == 'completada' and self.cliente:
            # Actualizar última visita si es más reciente
            if not self.cliente.ultima_visita or self.fecha > self.cliente.ultima_visita:
                self.cliente.ultima_visita = self.fecha
                
            # Incrementar contador de visitas si no se había contado antes
            if self.cliente.total_visitas is None:
                self.cliente.total_visitas = 1
            else:
                self.cliente.total_visitas += 1
            
            # Recalcular segmento
            self.cliente.clasificar_segmento()
            
    @classmethod
    def __commit_insert_listener__(cls, mapper, connection, target):
        """Escucha eventos de inserción"""
        if target.estado == 'completada':
            target.actualizar_segmentacion_cliente()
    
    @classmethod
    def __commit_update_listener__(cls, mapper, connection, target):
        """Escucha eventos de actualización"""
        if target.estado == 'completada':
            target.actualizar_segmentacion_cliente()

    def generate_confirmation_token(self):
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        # El token contendrá el ID de la cita. La expiración la maneja el serializador.
        return serializer.dumps(self.id, salt='email-confirmation-salt')

    @staticmethod
    def verify_confirmation_token(token, max_age_seconds=3600): # 1 hora por defecto
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            cita_id = serializer.loads(
                token,
                salt='email-confirmation-salt',
                max_age=max_age_seconds
            )
            cita = Cita.query.get(cita_id)
            # Verificar que la cita aún esté esperando confirmación
            if cita and cita.estado == 'pendiente_confirmacion':
                return cita
        except (SignatureExpired, BadTimeSignature):
            return None # Token expirado o inválido
        except Exception: # Otras posibles excepciones de itsdangerous o si la cita no existe
            return None
        return None

    def __repr__(self):
        return f'<Cita {self.id} - {self.fecha} - {self.estado}>'
    
    # El método crear_cita estático puede eliminarse si la lógica de creación se maneja completamente en la ruta.
    # O puede adaptarse para no hacer commit y devolver el objeto cita.
    # Por ahora, lo comentaremos ya que la ruta /api/agendar-cita ya maneja la creación.
    # @staticmethod
    # def crear_cita(cliente_id, barbero_id, fecha, servicio_id, duracion=30):
    #     ...

# Registrar los listeners de eventos para actualizar la segmentación de clientes
event.listen(Cita, 'after_insert', Cita.__commit_insert_listener__)
event.listen(Cita, 'after_update', Cita.__commit_update_listener__)
