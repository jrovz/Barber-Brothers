import logging
import os
import sys
import flask
from google.cloud import logging as cloud_logging
from google.cloud.logging.handlers import CloudLoggingHandler

def setup_logging(app):
    """
    Configura el logging para la aplicación Flask.
    En GCP, usa Cloud Logging; de lo contrario, usa logging estándar.
    """
    # Configurar el logger principal
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Limpiar los handlers existentes
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Si estamos en GCP, usar Cloud Logging
    if os.environ.get("GAE_ENV") == "standard" or os.environ.get("K_SERVICE"):
        try:
            # Cliente de Cloud Logging
            client = cloud_logging.Client()
            
            # Handler para Cloud Logging
            handler = CloudLoggingHandler(client, name="barberia_app")
            
            # Agregar el handler al logger
            logger.addHandler(handler)
            
            # Registrar eventos de Flask en Cloud Logging
            app.logger.addHandler(handler)
            
            # Log de inicialización
            app.logger.info("Inicializado Cloud Logging en GCP")
            
        except Exception as e:
            print(f"Error al configurar Cloud Logging: {e}")
            # Fallback a logging estándar
            _setup_standard_logging(logger, formatter)
    else:
        # En entorno local, usar logging estándar
        _setup_standard_logging(logger, formatter)
    
    return logger

def _setup_standard_logging(logger, formatter):
    """Configura el logging estándar para entorno local"""
    # Handler para salida a consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Si no existe el directorio logs, crearlo
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Handler para salida a archivo
    file_handler = logging.FileHandler('logs/app.log')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    logger.info("Inicializado logging estándar en entorno local")
