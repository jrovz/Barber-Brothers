"""
Error handler module for the application.
Provides custom error handlers for common HTTP errors.
"""
from flask import render_template, jsonify, request, current_app
from sqlalchemy.exc import OperationalError, InterfaceError

MENSAJE_BD_NO_DISPONIBLE = 'El servicio está ocupado un momento. Inténtalo de nuevo en unos segundos.'


def respuesta_bd_no_disponible(error, reintentar=True, mensaje=None):
    """503 con Retry-After cuando la base de datos no respondió (conexión caída, reinicio...).

    reintentar=True indica al navegador que es seguro repetir la petición porque no se guardó
    nada. Solo se registra el tipo y el mensaje del driver: el error de SQLAlchemy incluye el
    SQL y sus parámetros, que pueden traer datos personales.
    """
    from app import db
    db.session.rollback()
    origen = getattr(error, 'orig', None) or error
    detalle = (str(origen).strip().splitlines() or [''])[0][:120]
    current_app.logger.error(f'Base de datos no disponible ({type(origen).__name__}): {detalle}')
    texto = mensaje or MENSAJE_BD_NO_DISPONIBLE
    cabeceras = {'Retry-After': '2'}
    if request.path.startswith('/api/'):
        return jsonify({'error': texto, 'reintentar': bool(reintentar)}), 503, cabeceras
    return render_template('errors/503.html'), 503, cabeceras


def setup_error_handlers(app):
    """
    Configure custom error handlers for the application.
    
    Args:
        app: The Flask application instance
    """
    @app.errorhandler(400)
    def bad_request(error):
        return render_template('errors/400.html'), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return render_template('errors/401.html'), 401
        
    @app.errorhandler(403)
    def forbidden(error):
        return render_template('errors/403.html'), 403
        
    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404
        
    @app.errorhandler(500)
    def internal_server_error(error):
        return render_template('errors/500.html'), 500

    @app.errorhandler(OperationalError)
    @app.errorhandler(InterfaceError)
    def base_de_datos_no_disponible(error):
        return respuesta_bd_no_disponible(error)
    
    app.logger.info("Custom error handlers have been set up")