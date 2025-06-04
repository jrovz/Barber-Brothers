"""
Cloud PostgreSQL Connection Module for Barber Brothers
Handles connections to Google Cloud SQL PostgreSQL instances using Cloud SQL Connector
"""

import os
import logging
from typing import Optional
import sqlalchemy
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_connection_engine() -> Engine:
    """
    Inicializa conexión a Cloud SQL PostgreSQL usando Cloud SQL Connector
    
    Soporta múltiples métodos de conexión con fallback automático:
    1. Cloud SQL Connector (preferido para GCP)
    2. Standard PostgreSQL connection string
    3. SQLite fallback para desarrollo
    
    Returns:
        Engine: SQLAlchemy engine configurado para la conexión
        
    Raises:
        ValueError: Si no se puede establecer ningún tipo de conexión
    """
    
    # Verificar si estamos en entorno GCP
    is_gcp_env = (
        os.environ.get("GAE_ENV") == "standard" or 
        os.environ.get("K_SERVICE") or
        os.environ.get("GOOGLE_CLOUD_PROJECT")
    )
    
    if is_gcp_env:
        logger.info("Detectado entorno GCP, intentando conexión con Cloud SQL Connector")
        return _create_cloud_sql_engine()
    else:
        logger.info("Entorno no-GCP detectado, usando conexión estándar")
        return _create_standard_engine()


def _create_cloud_sql_engine() -> Engine:
    """
    Crea engine usando Google Cloud SQL Connector
    """
    try:
        from google.cloud.sql.connector import Connector
        
        # Validar variables de entorno requeridas
        required_vars = ["INSTANCE_CONNECTION_NAME", "DB_USER", "DB_PASS", "DB_NAME"]
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        
        if missing_vars:
            raise ValueError(f"Variables de entorno faltantes para Cloud SQL: {missing_vars}")
        
        def getconn():
            """Función de conexión para Cloud SQL Connector"""
            connector = Connector()
            conn = connector.connect(
                os.environ["INSTANCE_CONNECTION_NAME"],  # formato: "project:region:instance"
                "pg8000",  # Driver PostgreSQL
                user=os.environ["DB_USER"],
                password=os.environ["DB_PASS"],
                db=os.environ["DB_NAME"]
            )
            return conn

        # Crear engine con Cloud SQL Connector
        engine = sqlalchemy.create_engine(
            "postgresql+pg8000://",
            creator=getconn,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=2,
            pool_timeout=30,
            pool_recycle=1800,
            pool_pre_ping=True,  # Verificar conexiones antes de usar
            echo=os.environ.get('SQLALCHEMY_ECHO', 'False').lower() == 'true'
        )
        
        # Probar la conexión
        with engine.connect() as conn:
            conn.execute(sqlalchemy.text("SELECT 1"))
            
        logger.info("Conexión Cloud SQL PostgreSQL establecida exitosamente")
        return engine
        
    except ImportError:
        logger.warning("google-cloud-sql-connector no disponible, usando conexión estándar")
        return _create_standard_engine()
    except Exception as e:
        logger.error(f"Error al conectar con Cloud SQL Connector: {str(e)}")
        logger.info("Intentando conexión estándar como fallback")
        return _create_standard_engine()


def _create_standard_engine() -> Engine:
    """
    Crea engine usando conexión PostgreSQL estándar o SQLite como fallback
    """
    try:
        # Obtener DATABASE_URL
        database_url = os.environ.get('DATABASE_URL')
        
        if database_url and 'postgresql' in database_url:
            logger.info(f"Usando DATABASE_URL para PostgreSQL: {database_url[:50]}...")
            
            # Configurar engine para PostgreSQL
            engine = sqlalchemy.create_engine(
                database_url,
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=2,
                pool_timeout=30,
                pool_recycle=1800,
                pool_pre_ping=True,
                echo=os.environ.get('SQLALCHEMY_ECHO', 'False').lower() == 'true'
            )
            
            # Probar la conexión
            with engine.connect() as conn:
                conn.execute(sqlalchemy.text("SELECT 1"))
                
            logger.info("Conexión PostgreSQL estándar establecida exitosamente")
            return engine
            
        else:
            # Construir URL manualmente desde variables de entorno
            db_url = _build_database_url_from_env()
            if db_url:
                logger.info("URL de base de datos construida desde variables de entorno")
                
                engine = sqlalchemy.create_engine(
                    db_url,
                    poolclass=QueuePool,
                    pool_size=5,
                    max_overflow=2,
                    pool_timeout=30,
                    pool_recycle=1800,
                    pool_pre_ping=True
                )
                
                # Probar la conexión
                with engine.connect() as conn:
                    conn.execute(sqlalchemy.text("SELECT 1"))
                    
                logger.info("Conexión PostgreSQL desde variables de entorno establecida")
                return engine
            else:
                # Fallback a SQLite para desarrollo
                return _create_sqlite_fallback()
                
    except Exception as e:
        logger.error(f"Error al crear conexión estándar: {str(e)}")
        logger.info("Usando SQLite como fallback final")
        return _create_sqlite_fallback()


def _build_database_url_from_env() -> Optional[str]:
    """
    Construye DATABASE_URL desde variables de entorno individuales
    """
    try:
        db_user = os.environ.get("DB_USER") or os.environ.get("POSTGRES_USER")
        db_pass = os.environ.get("DB_PASS") or os.environ.get("POSTGRES_PASSWORD")
        db_name = os.environ.get("DB_NAME") or os.environ.get("POSTGRES_DB")
        db_host = os.environ.get("DB_HOST", "localhost")
        db_port = os.environ.get("DB_PORT", "5432")
        
        if not all([db_user, db_pass, db_name]):
            logger.warning("Variables de entorno de base de datos incompletas")
            return None
            
        # Para Cloud SQL con conexión de socket Unix
        instance_connection = os.environ.get("INSTANCE_CONNECTION_NAME")
        if instance_connection:
            # Formato para Cloud SQL con socket Unix
            return f"postgresql+psycopg2://{db_user}:{db_pass}@/{db_name}?host=/cloudsql/{instance_connection}"
        else:
            # Formato estándar TCP/IP
            return f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
            
    except Exception as e:
        logger.error(f"Error construyendo DATABASE_URL: {str(e)}")
        return None


def _create_sqlite_fallback() -> Engine:
    """
    Crea engine SQLite como fallback para desarrollo
    """
    try:
        # Determinar ruta para SQLite
        basedir = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        sqlite_path = os.path.join(basedir, "instance", "app.db")
        
        # Crear directorio instance si no existe
        os.makedirs(os.path.dirname(sqlite_path), exist_ok=True)
        
        sqlite_url = f'sqlite:///{sqlite_path}'
        logger.warning(f"Usando SQLite como fallback: {sqlite_url}")
        
        engine = sqlalchemy.create_engine(
            sqlite_url,
            echo=os.environ.get('SQLALCHEMY_ECHO', 'False').lower() == 'true'
        )
        
        return engine
        
    except Exception as e:
        logger.error(f"Error creando SQLite fallback: {str(e)}")
        raise ValueError("No se pudo establecer ningún tipo de conexión a base de datos")


def test_connection(engine: Engine) -> bool:
    """
    Prueba la conexión a la base de datos
    
    Args:
        engine: Motor SQLAlchemy a probar
        
    Returns:
        bool: True si la conexión es exitosa, False en caso contrario
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(sqlalchemy.text("SELECT 1"))
            result.fetchone()
        logger.info("Test de conexión exitoso")
        return True
    except Exception as e:
        logger.error(f"Test de conexión falló: {str(e)}")
        return False


def get_connection_info(engine: Engine) -> dict:
    """
    Obtiene información sobre la conexión actual
    
    Args:
        engine: Motor SQLAlchemy
        
    Returns:
        dict: Información de la conexión
    """
    try:
        info = {
            'driver': str(engine.dialect.driver),
            'database': engine.url.database,
            'host': engine.url.host,
            'port': engine.url.port,
            'pool_size': getattr(engine.pool, 'size', lambda: 'N/A')(),
            'pool_checked_in': getattr(engine.pool, 'checkedin', lambda: 'N/A')(),
            'pool_checked_out': getattr(engine.pool, 'checkedout', lambda: 'N/A')(),
            'pool_overflow': getattr(engine.pool, 'overflow', lambda: 'N/A')(),
        }
        return info
    except Exception as e:
        logger.error(f"Error obteniendo información de conexión: {str(e)}")
        return {'error': str(e)}


# Función de compatibilidad para importaciones existentes
def init_connection_pool():
    """
    Función de compatibilidad - alias para init_connection_engine
    """
    return init_connection_engine()
