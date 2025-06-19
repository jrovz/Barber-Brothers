from datetime import datetime
from app import db

class Slider(db.Model):
    __tablename__ = 'sliders'
    
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    subtitulo = db.Column(db.String(300))
    
    # Tipo de slide: 'imagen' o 'instagram'
    tipo = db.Column(db.String(20), nullable=False, default='imagen')
    
    # Para slides de imagen
    imagen_url = db.Column(db.String(500))
    
    # Para slides de Instagram
    instagram_embed_code = db.Column(db.Text)  # Código HTML completo del embed
    
    # Control de visualización
    activo = db.Column(db.Boolean, default=True)
    orden = db.Column(db.Integer, default=0)  # Para ordenar los slides
    
    # Metadatos
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Slider {self.titulo}>'
    
    @property
    def imagen_url_or_placeholder(self):
        """Devuelve la URL de la imagen o un placeholder si no existe"""
        if self.imagen_url:
            return self.imagen_url
        return '/static/images/placeholder_slide.jpg'
    
    @classmethod
    def get_active_slides_ordered(cls):
        """Obtiene todos los slides activos ordenados por el campo orden"""
        return cls.query.filter_by(activo=True).order_by(cls.orden.asc()).all() 