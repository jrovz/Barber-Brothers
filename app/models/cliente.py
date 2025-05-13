from app import db
from datetime import datetime, timedelta # Asegúrate que timedelta esté importado
from flask import current_app
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
from app.models.barbero import Barbero
from app.models.servicio import Servicio # Importar Servicio

class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False, index=True)
    telefono = db.Column(db.String(20))
    creado = db.Column(db.DateTime, default=datetime.utcnow)
    citas = db.relationship('Cita', backref='cliente', lazy='dynamic')
    mensajes = db.relationship('Mensaje', backref='cliente', lazy='dynamic')
    
    def __repr__(self):
        return f'<Cliente {self.nombre}>'

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
    confirmed_at = db.Column(db.DateTime, nullable=True) # Hora de confirmación

    # Relaciones
    # cliente_rel ya está en Cliente model via backref='cliente'
    barbero_rel = db.relationship('Barbero', backref='citas_agendadas', foreign_keys=[barbero_id]) # CAMBIADO AQUÍ
    servicio_rel = db.relationship('Servicio', backref='citas_servicio', foreign_keys=[servicio_id]) # Cambiado backref para evitar conflicto si Servicio tiene otras citas

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
