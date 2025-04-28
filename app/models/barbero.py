# filepath: app/models/barbero.py
from app import db
from datetime import datetime

class Barbero(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    especialidad = db.Column(db.String(100))
    imagen_url = db.Column(db.String(255))
    activo = db.Column(db.Boolean, default=True)
    creado = db.Column(db.DateTime, default=datetime.utcnow)
    # Relación con Citas (un barbero puede tener muchas citas)
    citas = db.relationship('Cita', backref='barbero', lazy='dynamic')
    
    # Agregar esta relación
    disponibilidad = db.relationship('DisponibilidadBarbero', backref='barbero', lazy='dynamic',
                                    cascade='all, delete-orphan')
    
    def esta_disponible(self, fecha_propuesta):
        """Verifica si el barbero está disponible en una fecha específica"""
        # Obtener día de la semana (0-6, donde 0 es lunes)
        dia_semana = fecha_propuesta.weekday()
        hora = fecha_propuesta.time()
        
        # Verificar si es un día laborable (lunes a sábado)
        if dia_semana > 5:  # domingo
            return False
            
        # Buscar si existe disponibilidad para ese día y hora
        for disp in self.disponibilidad.filter_by(dia_semana=dia_semana, activo=True).all():
            if disp.hora_inicio <= hora < disp.hora_fin:
                # Verificar si ya tiene una cita en ese horario
                cita_existente = Cita.query.filter_by(
                    barbero_id=self.id,
                    fecha=fecha_propuesta,
                    estado='confirmada'
                ).first()
                return cita_existente is None
                
        return False

    def __repr__(self):
        return f'<Barbero {self.nombre}>'
    

class DisponibilidadBarbero(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    barbero_id = db.Column(db.Integer, db.ForeignKey('barbero.id'), nullable=False)
    dia_semana = db.Column(db.Integer, nullable=False)  # 0: Lunes, 1: Martes, ..., 5: Sábado
    hora_inicio = db.Column(db.Time, nullable=False)
    hora_fin = db.Column(db.Time, nullable=False)
    activo = db.Column(db.Boolean, default=True)

    def __repr__(self):
        dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado']
        return f'<Disponibilidad: {dias[self.dia_semana]} {self.hora_inicio}-{self.hora_fin}>'