"""
Error handler module for the application.
Provides custom error handlers for common HTTP errors.
"""
from flask import render_template


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
    
    app.logger.info("Custom error handlers have been set up")