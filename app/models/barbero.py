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

    def __repr__(self):
        return f'<Barbero {self.nombre}>'