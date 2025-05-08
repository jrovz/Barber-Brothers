from app import db
from datetime import datetime
from .categoria import Categoria

class Producto(db.Model):
    __tablename__ = 'productos'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    precio = db.Column(db.Float, nullable=False)
    # Nuevo campo para la relación con Categoria
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.id'), nullable=True)
    categoria_rel = db.relationship('Categoria', back_populates='productos') # Cambiado de categoria a categoria_rel
    
    imagen_url = db.Column(db.String(255), nullable=True)
    activo = db.Column(db.Boolean, default=True)
    creado = db.Column(db.DateTime, default=datetime.utcnow)
    actualizado = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)