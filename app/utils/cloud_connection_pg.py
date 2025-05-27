"""
Módulo para manejar la conexión a Cloud SQL (PostgreSQL) en Google Cloud Platform.
"""
import os
import sqlalchemy
from google.cloud.sql.connector import Connector
from app.utils.config_manager import get_secret, get_instance_connection_name, get_db_credentials, build_database_url, is_production

def init_connection_pool():
    """
    Inicializa un pool de conexiones para PostgreSQL en Cloud SQL
    
    Esta función crea un pool de conexiones que puede ser reutilizado
    por múltiples solicitudes, manteniendo una conexión eficiente.
    
    Returns:
        Un motor SQLAlchemy para interactuar con la base de datos.
    """
    
    # Determina si estamos en entorno local o en producción
    print(f"Entorno: GAE_ENV={os.environ.get('GAE_ENV')}, K_SERVICE={os.environ.get('K_SERVICE')}")
    
    if is_production():
        # Entorno GCP (Cloud Run o App Engine)
        try:
            print("Iniciando conexión a Cloud SQL PostgreSQL en entorno GCP")
            
            # PRIORIDAD 1: Verificar si tenemos DATABASE_URL con formato para Cloud SQL Proxy
            db_url = os.environ.get("DATABASE_URL")
            if db_url and "postgresql" in db_url:
                print(f"Usando DATABASE_URL existente para PostgreSQL")
                if "unix_socket" in db_url:
                    print("La conexión usa socket Unix para Cloud SQL")
                return sqlalchemy.create_engine(
                    db_url,
                    pool_size=10,
                    max_overflow=5,
                    pool_timeout=30,
                    pool_recycle=300,
                    pool_pre_ping=True
                )
            
            # PRIORIDAD 2: Usar variables de entorno y el conector de Cloud SQL
            
            # Obtener credenciales (preferiblemente de Secret Manager)
            db_user, db_pass, db_name = get_db_credentials()
            
            # Nombre de la instancia de Cloud SQL
            instance_connection_name = get_instance_connection_name()
            
            print(f"Información de conexión: usuario={db_user}, db={db_name}, instancia={instance_connection_name}")
            
            # Inicializar el conector de Cloud SQL
            connector = Connector()
            
            # Función para crear una conexión usando el conector
            def getconn():
                conn = connector.connect(
                    instance_connection_name,
                    "pg8000",
                    user=db_user,
                    password=db_pass,
                    db=db_name
                )
                return conn
            
            # Crear el motor SQLAlchemy con el pool de conexiones
            engine = sqlalchemy.create_engine(
                "postgresql+pg8000://",
                creator=getconn,
                pool_size=10,
                max_overflow=5,
                pool_timeout=30,
                pool_recycle=300,
                pool_pre_ping=True
            )
            
            # Construir y guardar la URL para referencia (aunque usemos el conector)
            manual_db_url = build_database_url()
            os.environ["DATABASE_URL"] = manual_db_url
            print(f"URL de referencia establecida: {manual_db_url}")
            
            return engine
            
        except Exception as e:
            print(f"Error al conectar a Cloud SQL PostgreSQL: {e}")
            # Último intento - usar DATABASE_URL directo
            db_url = os.environ.get("DATABASE_URL")
            if db_url:
                print(f"Último intento: usando DATABASE_URL como último recurso")
                return sqlalchemy.create_engine(db_url)
            raise ValueError(f"No se pudo establecer conexión a la base de datos: {e}")
    else:
        # Entorno local de desarrollo
        db_url = build_database_url()
        
        print(f"Usando URL para entorno de desarrollo: {db_url}")
        return sqlalchemy.create_engine(db_url)

# Alias para mantener compatibilidad con código existente
init_connection_engine = init_connection_pool
