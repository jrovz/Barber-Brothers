# filepath: app/models/barbero_servicio.py
"""
Modelo BarberoServicio - Relación entre Barberos y Servicios con precios personalizados.

Este modelo permite:
- Definir qué servicios ofrece cada barbero
- Establecer precios personalizados por barbero (opcional)
- Controlar qué servicios están activos para cada barbero
"""
from app import db
from datetime import datetime


class BarberoServicio(db.Model):
    """
    Relación muchos-a-muchos entre Barbero y Servicio.
    Permite definir qué servicios ofrece cada barbero y a qué precio.
    """
    __tablename__ = 'barbero_servicio'
    
    id = db.Column(db.Integer, primary_key=True)
    barbero_id = db.Column(db.Integer, db.ForeignKey('barbero.id'), nullable=False)
    servicio_id = db.Column(db.Integer, db.ForeignKey('servicio.id'), nullable=False)
    
    # Precio personalizado (si es NULL, usa el precio base del servicio)
    precio_personalizado = db.Column(db.Numeric(10, 2), nullable=True)
    
    # Control de estado
    activo = db.Column(db.Boolean, default=True)
    creado = db.Column(db.DateTime, default=datetime.utcnow)
    modificado = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    barbero = db.relationship('Barbero', backref=db.backref('servicios_ofrecidos', lazy='dynamic'))
    servicio = db.relationship('Servicio', backref=db.backref('barberos_que_ofrecen', lazy='dynamic'))
    
    # Constraint único para evitar duplicados
    __table_args__ = (
        db.UniqueConstraint('barbero_id', 'servicio_id', name='uq_barbero_servicio'),
    )
    
    def get_precio_final(self):
        """
        Retorna el precio personalizado o el precio base del servicio.
        
        Returns:
            Decimal: Precio final a cobrar
        """
        if self.precio_personalizado is not None:
            return self.precio_personalizado
        return self.servicio.precio
    
    def tiene_precio_personalizado(self):
        """
        Indica si tiene un precio diferente al base.
        
        Returns:
            bool: True si tiene precio personalizado, False si usa el precio base
        """
        return self.precio_personalizado is not None
    
    def __repr__(self):
        precio = self.precio_personalizado if self.precio_personalizado else f"base ({self.servicio.precio})"
        return f'<BarberoServicio {self.barbero.nombre} - {self.servicio.nombre}: ${precio}>'
