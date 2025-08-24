# -*- coding: utf-8 -*-
"""
Funciones de formateo para Barber Brothers
=========================================

Utilidades para formatear datos de la aplicación.

Author: AI Assistant
Version: 1.0
"""

def format_cop(value):
    """
    Formatea un valor numérico como moneda colombiana (COP)
    
    Args:
        value: Valor numérico a formatear
        
    Returns:
        str: Valor formateado como moneda colombiana
    """
    try:
        # Convertir a float en caso de recibir string
        if isinstance(value, str):
            value = float(value.replace(',', '').replace('.', ''))
            
        # Formatear con separador de miles y 0 decimales
        return "{:,.0f}".format(value).replace(',', '.')
    except (ValueError, TypeError):
        return "0"
