from app import db
from datetime import datetime

class Categoria(db.Model):
    __tablename__ = 'categorias'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    # Relación con productos: una categoría puede tener muchos productos
    productos = db.relationship('Producto', back_populates='categoria_rel', lazy='dynamic')
    creado = db.Column(db.DateTime, default=datetime.utcnow)
    actualizado = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Categoria {self.nombre}>'