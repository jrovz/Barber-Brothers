# Importar todos los modelos para facilitar la importación desde otros módulos
from app.models.producto import Producto
from app.models.cliente import Cliente, Mensaje, Cita
from app.models.barbero import Barbero
from app.models.barbero_servicio import BarberoServicio
from app.models.admin import User
from app.models.negocio import Negocio
from .servicio import Servicio 
from .servicio_imagen import ServicioImagen
from .pedido import Pedido, PedidoItem
try:
    from .slider import Slider
except Exception as e:
    print(f"Warning: No se pudo importar el modelo Slider: {e}")
    Slider = None
from app.models.email import send_appointment_confirmation_email
from app.models.chat import ChatMensaje
