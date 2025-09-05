"""
Helper para manejar canonicalización SEO en Barber Brothers.

Este módulo proporciona funciones para asegurar que todas las URLs
sean canónicas y consistentes para Google Search Console.
"""

from flask import request, redirect, url_for
from urllib.parse import urlparse, urlunparse


def get_canonical_url(endpoint, **values):
    """
    Genera la URL canónica para un endpoint específico.
    
    Args:
        endpoint: El endpoint de Flask (ej: 'public.home')
        **values: Valores adicionales para la URL
        
    Returns:
        str: URL canónica completa
    """
    # Generar URL con _external=True
    canonical_url = url_for(endpoint, _external=True, **values)
    
    # Asegurar que no termine en slash (excepto para home)
    if endpoint != 'public.home' and canonical_url.endswith('/'):
        canonical_url = canonical_url.rstrip('/')
    
    return canonical_url


def should_redirect_to_canonical(current_path, canonical_path):
    """
    Determina si la URL actual debe redirigirse a la canónica.
    
    Args:
        current_path: La ruta actual
        canonical_path: La ruta canónica
        
    Returns:
        bool: True si debe redirigirse
    """
    # Normalizar paths
    current_normalized = current_path.rstrip('/')
    canonical_normalized = canonical_path.rstrip('/')
    
    # Si no es la home, no debe terminar en slash
    if current_path != '/' and current_path.endswith('/'):
        return True
    
    # Si las rutas normalizadas son diferentes
    if current_normalized != canonical_normalized:
        return True
    
    return False


def get_redirect_response(endpoint, **values):
    """
    Genera una respuesta de redirección 301 a la URL canónica.
    
    Args:
        endpoint: El endpoint de Flask
        **values: Valores adicionales para la URL
        
    Returns:
        Response: Respuesta de redirección 301
    """
    return redirect(url_for(endpoint, **values), code=301)


def validate_canonical_url(url):
    """
    Valida que una URL sea canónica.
    
    Args:
        url: URL a validar
        
    Returns:
        bool: True si es canónica
    """
    parsed = urlparse(url)
    
    # Verificar que no tenga trailing slash (excepto home)
    if parsed.path != '/' and parsed.path.endswith('/'):
        return False
    
    # Verificar que no tenga parámetros de tracking
    tracking_params = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term']
    if parsed.query:
        query_params = parsed.query.split('&')
        for param in query_params:
            param_name = param.split('=')[0]
            if param_name in tracking_params:
                return False
    
    return True


def clean_url_for_canonical(url):
    """
    Limpia una URL para hacerla canónica.
    
    Args:
        url: URL a limpiar
        
    Returns:
        str: URL canónica limpia
    """
    parsed = urlparse(url)
    
    # Remover trailing slash (excepto para home)
    if parsed.path != '/' and parsed.path.endswith('/'):
        parsed = parsed._replace(path=parsed.path.rstrip('/'))
    
    # Remover parámetros de tracking
    if parsed.query:
        query_params = parsed.query.split('&')
        clean_params = []
        tracking_params = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term']
        
        for param in query_params:
            param_name = param.split('=')[0]
            if param_name not in tracking_params:
                clean_params.append(param)
        
        if clean_params:
            parsed = parsed._replace(query='&'.join(clean_params))
        else:
            parsed = parsed._replace(query='')
    
    return urlunparse(parsed)
