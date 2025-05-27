"""
Módulo para manejar la conexión a PostgreSQL en Microsoft Azure.
"""
import os
import sqlalchemy
from app.utils.config_manager import is_production

def is_azure():
    """Detecta si estamos ejecutando en Azure App Service"""
    return os.environ.get('WEBSITE_SITE_NAME') is not None

def init_connection_pool():
    """
    Inicializa un pool de conexiones para PostgreSQL en Azure
    
    Esta función crea un pool de conexiones que puede ser reutilizado
    por múltiples solicitudes, manteniendo una conexión eficiente.
    
    Returns:
        Un motor SQLAlchemy para interactuar con la base de datos.
    """
    
    # Determina si estamos en entorno local o en Azure
    print(f"Entorno: Azure App Service={is_azure()}, Producción={is_production()}")
    
    if is_azure() or is_production():
        # Entorno Azure App Service
        try:
            print("Iniciando conexión a PostgreSQL en entorno Azure")
            
            # PRIORIDAD 1: Verificar si tenemos DATABASE_URL configurado
            db_url = os.environ.get("DATABASE_URL")
            if db_url and "postgresql" in db_url:
                print(f"Usando DATABASE_URL existente para PostgreSQL")
                return sqlalchemy.create_engine(
                    db_url,
                    pool_size=5,  # Reducido para minimizar el consumo de recursos en plan F1
                    max_overflow=2,
                    pool_timeout=30,
                    pool_recycle=300,
                    pool_pre_ping=True
                )
            
            # PRIORIDAD 2: Usar variables de entorno individuales
            db_user = os.environ.get("DB_USER", "barberia_user")
            db_pass = os.environ.get("DB_PASS")
            db_name = os.environ.get("DB_NAME", "barberia_db")
            db_host = os.environ.get("DB_HOST")  # IP de la VM con PostgreSQL
            db_port = os.environ.get("DB_PORT", "5432")
            
            if not all([db_pass, db_host]):
                raise ValueError("Faltan variables de entorno necesarias: DB_PASS, DB_HOST")
            
            print(f"Información de conexión: usuario={db_user}, db={db_name}, host={db_host}")
            
            # Construir la URL de conexión
            db_url = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
            
            # Crear el motor SQLAlchemy con el pool de conexiones
            engine = sqlalchemy.create_engine(
                db_url,
                pool_size=5,  # Reducido para el plan F1
                max_overflow=2,
                pool_timeout=30,
                pool_recycle=300,
                pool_pre_ping=True
            )
            
            # Guardar la URL para referencia
            os.environ["DATABASE_URL"] = db_url
            print(f"URL de referencia establecida para PostgreSQL en Azure")
            
            return engine
            
        except Exception as e:
            print(f"Error al conectar a PostgreSQL en Azure: {e}")
            raise ValueError(f"No se pudo establecer conexión a la base de datos: {e}")
    else:
        # Entorno local de desarrollo
        db_url = os.environ.get("DATABASE_URL", "postgresql://postgres:password@localhost:5432/barberia_db")
        print(f"Usando URL para entorno de desarrollo: {db_url}")
        return sqlalchemy.create_engine(db_url)

# Alias para mantener compatibilidad con código existente
init_connection_engine = init_connection_pool
