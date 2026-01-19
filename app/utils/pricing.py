# filepath: app/utils/pricing.py
"""
Utilidades de precios para Barber Brothers.

Este módulo contiene funciones para calcular y obtener precios de servicios,
considerando precios personalizados por barbero.
"""
from decimal import Decimal


def obtener_precio_servicio(barbero_id: int, servicio_id: int) -> dict:
    """
    Obtiene el precio de un servicio para un barbero específico.
    
    Si el barbero tiene un precio personalizado configurado para el servicio,
    se retorna ese precio. De lo contrario, se retorna el precio base del servicio.
    
    Args:
        barbero_id: ID del barbero
        servicio_id: ID del servicio
        
    Returns:
        dict: {
            'precio': Decimal - Precio final a cobrar,
            'precio_base': Decimal - Precio base del servicio,
            'es_personalizado': bool - True si usa precio personalizado,
            'servicio_activo_para_barbero': bool - True si el barbero ofrece este servicio
        }
        None si el servicio no existe
    """
    from app.models.barbero_servicio import BarberoServicio
    from app.models.servicio import Servicio
    
    servicio = Servicio.query.get(servicio_id)
    if not servicio:
        return None
    
    # Buscar configuración específica barbero-servicio
    config = BarberoServicio.query.filter_by(
        barbero_id=barbero_id,
        servicio_id=servicio_id,
        activo=True
    ).first()
    
    if config:
        return {
            'precio': config.get_precio_final(),
            'precio_base': servicio.precio,
            'es_personalizado': config.tiene_precio_personalizado(),
            'servicio_activo_para_barbero': True
        }
    
    # Si no hay configuración específica, el barbero ofrece el servicio al precio base
    # (comportamiento por defecto para compatibilidad hacia atrás)
    return {
        'precio': servicio.precio,
        'precio_base': servicio.precio,
        'es_personalizado': False,
        'servicio_activo_para_barbero': True
    }


def obtener_servicios_barbero(barbero_id: int) -> list:
    """
    Obtiene todos los servicios que ofrece un barbero con sus precios.
    
    Args:
        barbero_id: ID del barbero
        
    Returns:
        list: Lista de diccionarios con información de cada servicio:
            - servicio: objeto Servicio
            - activo: bool
            - precio_personalizado: Decimal o None
            - precio_final: Decimal
    """
    from app.models.barbero_servicio import BarberoServicio
    from app.models.servicio import Servicio
    
    servicios = Servicio.query.filter_by(activo=True).order_by(Servicio.orden).all()
    resultado = []
    
    for servicio in servicios:
        config = BarberoServicio.query.filter_by(
            barbero_id=barbero_id,
            servicio_id=servicio.id
        ).first()
        
        if config:
            resultado.append({
                'servicio': servicio,
                'activo': config.activo,
                'precio_personalizado': config.precio_personalizado,
                'precio_final': config.get_precio_final()
            })
        else:
            # Sin configuración = activo con precio base (comportamiento por defecto)
            resultado.append({
                'servicio': servicio,
                'activo': True,
                'precio_personalizado': None,
                'precio_final': servicio.precio
            })
    
    return resultado
