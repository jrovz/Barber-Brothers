from datetime import datetime
from app import db

class Pedido(db.Model):
    __tablename__ = 'pedidos'
    
    id = db.Column(db.Integer, primary_key=True)
    numero_pedido = db.Column(db.String(20), unique=True, nullable=False)
    
    # Información del cliente
    cliente_nombre = db.Column(db.String(100), nullable=False)
    cliente_email = db.Column(db.String(120), nullable=False)
    cliente_telefono = db.Column(db.String(20), nullable=False)
    
    # Información del pedido
    total = db.Column(db.Numeric(10, 2), nullable=False)
    estado = db.Column(db.String(20), default='pendiente')  # pendiente, preparando, listo, entregado, cancelado
    fecha_pedido = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_entrega = db.Column(db.DateTime)
    notas = db.Column(db.Text)
    
    # Relación con productos del pedido
    items = db.relationship('PedidoItem', backref='pedido', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Pedido {self.numero_pedido}>'
    
    def generar_numero_pedido(self):
        """Genera un número único de pedido"""
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f'PED{timestamp}'

class PedidoItem(db.Model):
    __tablename__ = 'pedido_items'
    
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedidos.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    
    # Información del producto en el momento del pedido
    producto_nombre = db.Column(db.String(100), nullable=False)
    producto_precio = db.Column(db.Numeric(10, 2), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False, default=1)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Relación con producto
    producto = db.relationship('Producto', backref='pedido_items')
    
    def __repr__(self):
        return f'<PedidoItem {self.producto_nombre} x{self.cantidad}>' 