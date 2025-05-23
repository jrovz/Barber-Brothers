"""
Database Setup Script

This script initializes the database for the barberia application.
It creates all tables and imports initial data.
"""

import os
import sys
import time
import logging
import traceback
from flask_migrate import Migrate, upgrade
from app import create_app, db

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("setup_db")

def wait_for_database(app, max_retries=5, initial_delay=2):
    """Espera a que la base de datos esté disponible con backoff exponencial"""
    retry_count = 0
    delay = initial_delay
    
    while retry_count < max_retries:
        try:
            with app.app_context():
                logger.info(f"Intento {retry_count + 1}/{max_retries} de conexión a la base de datos...")
                db.session.execute('SELECT 1')
                db.session.commit()
                logger.info("Conexión a la base de datos exitosa")
                return True
        except Exception as e:
            retry_count += 1
            logger.warning(f"Error de conexión a la base de datos: {e}")
            
            if retry_count >= max_retries:
                logger.error("Número máximo de reintentos alcanzado. No se pudo conectar a la base de datos.")
                break
            
            logger.info(f"Reintentando en {delay} segundos...")
            time.sleep(delay)
            delay *= 2  # Backoff exponencial
    
    return False

def setup_database():
    """
    Set up the database for the application
    """
    try:
        logger.info("Starting database setup...")
        app = create_app('production')
        
        with app.app_context():
            # Wait a bit for database connection to be ready
            time.sleep(2)
            
            # Verificar si podemos conectar a la base de datos
            try:
                # Ejecutar una consulta simple para verificar la conexión
                logger.info("Verificando conexión a la base de datos...")
                db.session.execute('SELECT 1')
                logger.info("Conexión a la base de datos exitosa")
            except Exception as e:
                logger.error(f"ERROR DE CONEXIÓN A LA BASE DE DATOS: {e}")
                logger.info("Verificando configuración de variables de entorno...")
                  # Mostrar variables de entorno relevantes (asegurarse de no mostrar contraseñas en logs)
                import os
                env_vars = ['INSTANCE_CONNECTION_NAME', 'GOOGLE_CLOUD_PROJECT', 'DATABASE_URL', 'DB_USER', 'DB_NAME']
                for var in env_vars:
                    if var in os.environ:
                        value = os.environ[var]
                        if var in ['DB_PASS', 'DATABASE_URL'] and value:
                            # No mostrar contraseñas completas en logs
                            logger.info(f"  {var}: ***DEFINIDO***")
                        else:
                            logger.info(f"  {var}: {value}")
                    else:
                        logger.info(f"  {var}: NO DEFINIDO")
            
            try:
                logger.info("Running migrations...")
                # Run migrations
                migrate = Migrate(app, db)
                upgrade()
                logger.info("Migrations completed successfully.")
            except Exception as e:
                logger.error(f"Error en migraciones: {e}")
                import traceback
                traceback.print_exc()
              # Import initial data if specified
            try:
                logger.info("Importing initial data...")
                from init_data import import_initial_data
                success = import_initial_data()
                if success:
                    logger.info("Initial data imported successfully.")
                else:
                    logger.warning("Failed to import initial data.")
            except Exception as e:
                logger.error(f"Error importing initial data: {e}")
                import traceback
                traceback.print_exc()
                
            logger.info("Database setup completed.")
            return True
    except Exception as e:
        logger.error(f"Error setting up database: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logger.info("Starting database setup script")
    success = setup_database()
    if success:
        logger.info("Database setup completed successfully")
        sys.exit(0)
    else:
        logger.error("Database setup failed")
        sys.exit(1)
