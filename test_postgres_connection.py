"""
Script para probar la conexión a PostgreSQL

Este script verifica la conexión a PostgreSQL, ya sea local o en GCP.
Útil para confirmar que la configuración funciona correctamente antes
de desplegar la aplicación completa.
"""

import os
import sys
import time
import logging
from sqlalchemy import create_engine, text

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("test_postgres_connection")

def test_local_connection():
    """Prueba la conexión a PostgreSQL local"""
    try:
        logger.info("Probando conexión a PostgreSQL local...")
        
        # URL de conexión local predeterminada (puede ser reemplazada con DATABASE_URL)
        db_url = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/barberia_db")
        
        logger.info(f"Usando URL de conexión: {db_url}")
        
        # Crear engine
        engine = create_engine(db_url)
        
        # Probar conexión
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            
            logger.info(f"¡Conexión exitosa a PostgreSQL!")
            logger.info(f"Versión de PostgreSQL: {version}")
            
            # Listar tablas (si existen)
            result = conn.execute(text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public'"
            ))
            tables = [row[0] for row in result]
            
            if tables:
                logger.info(f"Tablas encontradas en la base de datos: {', '.join(tables)}")
            else:
                logger.info("No se encontraron tablas en la base de datos.")
            
        return True
    except Exception as e:
        logger.error(f"Error conectando a PostgreSQL local: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cloud_connection():
    """Prueba la conexión a PostgreSQL en GCP usando Cloud SQL Python Connector"""
    try:
        logger.info("Probando conexión a PostgreSQL en GCP...")
        
        # Importar el módulo de conexión a Cloud SQL
        from app.utils.cloud_connection_pg import init_connection_engine
        
        # Inicializar engine
        logger.info("Inicializando conexión con Cloud SQL Connector...")
        engine = init_connection_engine()
        
        # Probar conexión
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            
            logger.info(f"¡Conexión exitosa a PostgreSQL en GCP!")
            logger.info(f"Versión de PostgreSQL: {version}")
            
            # Listar tablas (si existen)
            result = conn.execute(text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public'"
            ))
            tables = [row[0] for row in result]
            
            if tables:
                logger.info(f"Tablas encontradas en la base de datos: {', '.join(tables)}")
            else:
                logger.info("No se encontraron tablas en la base de datos.")
            
        return True
    except Exception as e:
        logger.error(f"Error conectando a PostgreSQL en GCP: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Función principal"""
    # Determinar qué tipo de conexión probar
    if os.environ.get("GAE_ENV") == "standard" or os.environ.get("K_SERVICE"):
        # Estamos en GCP
        logger.info("Entorno detectado: Google Cloud Platform")
        success = test_cloud_connection()
    else:
        # Entorno local
        logger.info("Entorno detectado: Local")
        success = test_local_connection()
    
    if success:
        logger.info("Prueba de conexión exitosa")
        return 0
    else:
        logger.error("Prueba de conexión fallida")
        return 1

if __name__ == "__main__":
    sys.exit(main())
