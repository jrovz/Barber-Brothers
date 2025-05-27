#!/usr/bin/env python
"""
Script para ejecutar migraciones de base de datos
"""
import os
import sys
import logging
import importlib
import traceback
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def configure_environment():
    """Configurar las variables de entorno necesarias para la conexión a la base de datos"""
    # Asegurarse de que FLASK_APP esté configurado
    if not os.environ.get('FLASK_APP'):
        os.environ['FLASK_APP'] = 'wsgi.py'
        logger.info("Configurado FLASK_APP=wsgi.py")
    
    # Obtener información de conexión a la base de datos
    db_user = os.environ.get('DB_USER', 'barberia_user')
    db_pass = os.environ.get('DB_PASS', 'BarberiaSecure123!')
    db_name = os.environ.get('DB_NAME', 'barberia_db')
    instance_connection_name = os.environ.get('INSTANCE_CONNECTION_NAME')
    
    if not instance_connection_name and os.environ.get('GOOGLE_CLOUD_PROJECT'):
        # Construir el nombre de conexión si no está definido
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
        region = os.environ.get('REGION', 'us-east1')
        instance_name = os.environ.get('INSTANCE_NAME', 'barberia-db')
        instance_connection_name = f"{project_id}:{region}:{instance_name}"
        os.environ['INSTANCE_CONNECTION_NAME'] = instance_connection_name
        logger.info(f"Construido INSTANCE_CONNECTION_NAME: {instance_connection_name}")
    
    # Configurar DATABASE_URL para PostgreSQL en Cloud SQL
    if instance_connection_name:
        db_socket_dir = os.environ.get('DB_SOCKET_DIR', '/cloudsql')
        db_uri = f"postgresql+pg8000://{db_user}:{db_pass}@/{db_name}?unix_socket={db_socket_dir}/{instance_connection_name}"
        os.environ['DATABASE_URL'] = db_uri
        logger.info(f"Configurado DATABASE_URL para PostgreSQL en Cloud SQL: {db_uri.replace(db_pass, '***')}")
        
        # Configurar también variables específicas para Flask-SQLAlchemy
        os.environ['SQLALCHEMY_DATABASE_URI'] = db_uri
        return True
    else:
        logger.error("No se pudo configurar la conexión a la base de datos: falta INSTANCE_CONNECTION_NAME")
        return False

def test_database_connection():
    """Probar la conexión a la base de datos"""
    db_uri = os.environ.get('DATABASE_URL')
    if not db_uri:
        logger.error("No se configuró DATABASE_URL")
        return False
    
    try:
        logger.info(f"Probando conexión a la base de datos...")
        engine = create_engine(db_uri)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            for row in result:
                logger.info(f"Conexión exitosa: {row}")
        return True
    except OperationalError as e:
        logger.error(f"Error al conectar a la base de datos: {e}")
        return False
    except Exception as e:
        logger.error(f"Error inesperado al conectar a la base de datos: {e}")
        return False

def run_migrations():
    """Ejecutar migraciones de base de datos"""
    try:
        # Configurar entorno
        if not configure_environment():
            logger.error("Fallo al configurar el entorno. Abortando migraciones.")
            return False
        
        # Probar conexión a la base de datos
        if not test_database_connection():
            logger.error("Fallo al conectar a la base de datos. Abortando migraciones.")
            return False
        
        # Importar la aplicación
        logger.info("Importando la aplicación...")
        from wsgi import app
        
        logger.info("Iniciando migraciones de base de datos...")
        
        # Registrar módulos importantes
        for module_name in ['flask_migrate', 'alembic']:
            try:
                importlib.import_module(module_name)
                logger.info(f"Módulo {module_name} importado correctamente")
            except ImportError as e:
                logger.error(f"No se pudo importar {module_name}: {e}")
                return False
        
        # Ejecutar migraciones dentro del contexto de la aplicación
        with app.app_context():
            from flask_migrate import upgrade
            logger.info("Ejecutando upgrade()...")
            upgrade()
            
        logger.info("Migraciones completadas exitosamente.")
        return True
    except Exception as e:
        logger.error(f"Error al ejecutar migraciones: {e}")
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    logger.info("Iniciando script de migraciones...")
    # Ejecutar migraciones
    success = run_migrations()
    
    # Salir con código apropiado
    if success:
        logger.info("Script de migraciones completado exitosamente.")
        sys.exit(0)
    else:
        logger.error("Script de migraciones falló.")
        sys.exit(1)
