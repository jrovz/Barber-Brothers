from app import db
from datetime import datetime

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


class Cita(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    barbero_id = db.Column(db.Integer, db.ForeignKey('barbero.id'), nullable=True) # Añadido, puede ser nulo si no se asigna
    fecha = db.Column(db.DateTime, nullable=False)
    servicio = db.Column(db.String(100), nullable=False)
    estado = db.Column(db.String(20), default='pendiente') # Ej: pendiente, confirmada, cancelada, completada
    creado = db.Column(db.DateTime, default=datetime.utcnow)
    duracion = db.Column(db.Integer, default=30)  # duración en minutos
    
    @staticmethod
    def crear_cita(cliente_id, barbero_id, fecha, servicio, duracion=30):
        """Crea una cita verificando disponibilidad"""
        barbero = Barbero.query.get(barbero_id)
        if not barbero or not barbero.activo:
            return False, "Barbero no disponible"
            
        if not barbero.esta_disponible(fecha):
            return False, "El barbero no está disponible en ese horario"
            
        nueva_cita = Cita(
            cliente_id=cliente_id,
            barbero_id=barbero_id,
            fecha=fecha,
            servicio=servicio,
            duracion=duracion,
            estado='pendiente'
        )
        
        db.session.add(nueva_cita)
        try:
            db.session.commit()
            return True, nueva_cita
        except Exception as e:
            db.session.rollback()
            return False, str(e)
