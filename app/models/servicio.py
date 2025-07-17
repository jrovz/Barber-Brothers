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
    imagen_url = db.Column(db.String(255), nullable=True) # URL de la imagen del servicio (mantener por compatibilidad)
    
    orden = db.Column(db.Integer, nullable=False, default=0, index=True)  # Nuevo campo para el orden de aparición
    # Relación con múltiples imágenes
    imagenes = db.relationship('ServicioImagen', back_populates='servicio', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Servicio {self.nombre}>'
    
    def get_imagenes_activas(self):
        """Obtiene las imágenes activas ordenadas"""
        return self.imagenes.filter_by(activa=True).order_by('orden', 'creado').all()
    
    def get_imagen_principal(self):
        """Obtiene la imagen principal (primera) o fallback a imagen_url"""
        imagenes = self.get_imagenes_activas()
        if imagenes:
            return imagenes[0].ruta_imagen
        return self.imagen_url
    
    def get_duracion_minutos(self):
        """
        Extrae la duración en minutos del campo duracion_estimada
        
        Returns:
            int: Duración en minutos, 30 por defecto si no se puede parsear
        """
        if not self.duracion_estimada:
            return 30
            
        duracion_str = str(self.duracion_estimada).lower()
        
        # Extraer números del string
        import re
        numeros = re.findall(r'\d+', duracion_str)
        
        if not numeros:
            return 30
            
        numero = int(numeros[0])
        
        # Determinar si es horas o minutos
        if 'hora' in duracion_str or 'hour' in duracion_str or 'hr' in duracion_str:
            return numero * 60
        else:
            # Asumir que son minutos por defecto
            return numero

    def get_duracion_hhmm(self):
        """
        Devuelve la duración estimada en formato HH:MM (ej: 01:30)
        """
        minutos = self.get_duracion_minutos()
        horas = minutos // 60
        mins = minutos % 60
        return f"{horas:02d}:{mins:02d}"