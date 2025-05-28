import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

def init_connection_engine():
    """
    Inicializa y retorna un motor de conexión para PostgreSQL en entorno local
    """
    try:
        # Obtener la URL de la base de datos de las variables de entorno
        db_url = os.environ.get('DATABASE_URL')
        
        if not db_url:
            # Si no está definida, usar una configuración por defecto para SQLite
            basedir = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            db_url = f'sqlite:///{os.path.join(basedir, "instance", "app.db")}'
            logging.warning(f"No se encontró DATABASE_URL. Usando SQLite como fallback: {db_url}")
        
        # Configurar el motor de conexión
        engine = create_engine(
            db_url,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=2,
            pool_timeout=30,
            pool_recycle=1800,
        )
        
        return engine
    except Exception as e:
        logging.error(f"Error al inicializar el motor de conexión: {str(e)}")
        raise
