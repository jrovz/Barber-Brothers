# Importar todos los modelos para facilitar la importación desde otros módulos
from app.models.producto import Producto
from app.models.cliente import Cliente, Mensaje, Cita
from app.models.barbero import Barbero 
from app.models.admin import User
from .servicio import Servicio 
from .servicio_imagen import ServicioImagen
from .pedido import Pedido, PedidoItem
from app.models.email import send_appointment_confirmation_email