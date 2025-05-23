"""
API Endpoint para Health Check
Este módulo implementa un endpoint de health check para verificar el estado
de la aplicación y sus componentes principales (base de datos, almacenamiento).
"""

from flask import jsonify, current_app
from sqlalchemy.exc import SQLAlchemyError
from app import db
from app.utils.cloud_storage import CloudStorage

def register_health_routes(bp):
    """
    Registra rutas relacionadas con health check en el blueprint proporcionado.
    """
    
    @bp.route('/health', methods=['GET'])
    def health_check():
        """
        Endpoint de health check que verifica:
        - Estado general de la aplicación
        - Conexión a la base de datos
        - Conexión al almacenamiento en la nube
        """
        health_data = {
            'status': 'ok',
            'version': '1.0',
            'database': 'unknown',
            'storage': 'unknown'
        }
        
        # Verificar conexión a la base de datos
        try:
            db.session.execute('SELECT 1')
            health_data['database'] = 'connected'
        except SQLAlchemyError as e:
            current_app.logger.error(f"Error de salud en la base de datos: {e}")
            health_data['database'] = 'error'
            health_data['database_error'] = str(e)
            health_data['status'] = 'degraded'
        
        # Verificar conexión al almacenamiento
        try:
            # Solo verificar que se pueda inicializar el cliente de almacenamiento
            storage = CloudStorage()
            if storage.client:
                health_data['storage'] = 'available'
            else:
                health_data['storage'] = 'unavailable'
                health_data['status'] = 'degraded'
        except Exception as e:
            current_app.logger.error(f"Error de salud en el almacenamiento: {e}")
            health_data['storage'] = 'error'
            health_data['storage_error'] = str(e)
            health_data['status'] = 'degraded'
        
        # Si algún componente crítico falla, establecer el estado como degradado
        if health_data['database'] != 'connected' or health_data['storage'] != 'available':
            health_data['status'] = 'degraded'
        
        # Información adicional
        try:
            health_data['environment'] = current_app.config.get('FLASK_ENV', 'unknown')
            health_data['app_name'] = 'Barber Brothers'
        except Exception:
            pass
        
        # Determinar el código de respuesta HTTP basado en el estado
        status_code = 200 if health_data['status'] == 'ok' else 503
        
        return jsonify(health_data), status_code
