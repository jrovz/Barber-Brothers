"""
Mejora del manejo de errores en la aplicación Flask Barber Brothers.

Este módulo proporciona funciones para mejorar el manejo de errores
en diferentes partes de la aplicación, especialmente en rutas críticas
como la autenticación y acceso al panel de administración.
"""
import traceback
import logging
import sys
from functools import wraps
from flask import jsonify, flash, render_template, request, current_app

def setup_error_handlers(app):
    """
    Configura manejadores de errores para la aplicación Flask.
    """
    logger = logging.getLogger('error_handler')
    
    @app.errorhandler(404)
    def not_found_error(error):
        logger.warning(f"404 Error: {request.path} - Referrer: {request.referrer}")
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"500 Error: {str(error)}", exc_info=True)
        db = app.extensions.get('sqlalchemy').db
        db.session.rollback()
        if app.config.get('DEBUG', False):
            error_details = traceback.format_exc()
            return render_template('errors/500.html', error_details=error_details), 500
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(401)
    def unauthorized_error(error):
        logger.warning(f"401 Error: {request.path} - User: {getattr(getattr(request, 'user', None), 'username', 'unknown')}")
        return render_template('errors/401.html'), 401
    
    @app.errorhandler(403)
    def forbidden_error(error):
        logger.warning(f"403 Error: {request.path} - User: {getattr(getattr(request, 'user', None), 'username', 'unknown')}")
        return render_template('errors/403.html'), 403

def api_error_handler(f):
    """
    Decorador para manejar errores en rutas API y devolver respuestas JSON.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger = current_app.logger
            logger.error(f"API Error en {f.__name__}: {str(e)}", exc_info=True)
            
            error_response = {
                "success": False,
                "error": str(e),
                "message": "Se produjo un error en el servidor."
            }
            
            if current_app.config.get('DEBUG', False):
                error_response["traceback"] = traceback.format_exc()
                
            return jsonify(error_response), 500
    return decorated_function

def route_error_handler(f):
    """
    Decorador para manejar errores en rutas normales y mostrar mensajes flash.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger = current_app.logger
            logger.error(f"Error en ruta {f.__name__}: {str(e)}", exc_info=True)
            
            flash(f"Se produjo un error inesperado: {str(e)}", "danger")
            
            # Si estamos en modo debug, podemos mostrar más detalles
            if current_app.config.get('DEBUG', False):
                error_details = traceback.format_exc()
                return render_template('errors/custom_error.html', 
                                       error=str(e), 
                                       traceback=error_details), 500
            
            return render_template('errors/custom_error.html', 
                                  error="Se produjo un error en el servidor."), 500
    return decorated_function

# Plantillas HTML básicas para los errores
error_templates = {
    "404": """
    <div class="error-container">
        <h1>404 - Página no encontrada</h1>
        <p>La página que estás buscando no existe o ha sido movida.</p>
        <a href="/" class="btn btn-primary">Volver al inicio</a>
    </div>
    """,
    
    "500": """
    <div class="error-container">
        <h1>500 - Error interno del servidor</h1>
        <p>Lo sentimos, ocurrió un error al procesar tu solicitud.</p>
        {% if error_details and config.DEBUG %}
        <div class="error-details">
            <h3>Detalles del error (sólo en modo debug):</h3>
            <pre>{{ error_details }}</pre>
        </div>
        {% endif %}
        <a href="/" class="btn btn-primary">Volver al inicio</a>
    </div>
    """,
    
    "401": """
    <div class="error-container">
        <h1>401 - No autorizado</h1>
        <p>Debes iniciar sesión para acceder a esta página.</p>
        <a href="/admin/login" class="btn btn-primary">Iniciar sesión</a>
    </div>
    """,
    
    "403": """
    <div class="error-container">
        <h1>403 - Acceso prohibido</h1>
        <p>No tienes permisos para acceder a esta página.</p>
        <a href="/" class="btn btn-primary">Volver al inicio</a>
    </div>
    """,
    
    "custom_error": """
    <div class="error-container">
        <h1>Error en la aplicación</h1>
        <p>{{ error }}</p>
        {% if traceback and config.DEBUG %}
        <div class="error-details">
            <h3>Detalles del error (sólo en modo debug):</h3>
            <pre>{{ traceback }}</pre>
        </div>
        {% endif %}
        <a href="/" class="btn btn-primary">Volver al inicio</a>
    </div>
    """
}
