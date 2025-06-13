from app import db
from datetime import datetime

class ServicioImagen(db.Model):
    __tablename__ = 'servicio_imagenes'
    
    id = db.Column(db.Integer, primary_key=True)
    servicio_id = db.Column(db.Integer, db.ForeignKey('servicio.id'), nullable=False)
    ruta_imagen = db.Column(db.String(255), nullable=False)  # Ruta del archivo subido
    orden = db.Column(db.Integer, default=0)  # Para ordenar las imágenes
    activa = db.Column(db.Boolean, default=True, nullable=False)
    creado = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relación con Servicio
    servicio = db.relationship('Servicio', back_populates='imagenes')
    
    def __repr__(self):
        return f'<ServicioImagen {self.servicio_id}:{self.orden}>' 