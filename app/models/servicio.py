# filepath: app/models/servicio.py
from app import db
from datetime import datetime

class Servicio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, index=True)
    descripcion = db.Column(db.Text, nullable=True)
    precio = db.Column(db.Numeric(10, 2), nullable=False) # Para manejar decimales de dinero
    duracion_estimada = db.Column(db.String(50), nullable=True) # Ej: "30 min", "1 hora"
    activo = db.Column(db.Boolean, default=True, nullable=False) # Para mostrar/ocultar en el sitio público
    creado = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Servicio {self.nombre}>'