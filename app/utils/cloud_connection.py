import os
from google.cloud.sql.connector import Connector
import sqlalchemy
import pg8000
from google.cloud import secretmanager

def get_secret(secret_id):
    """
    Obtiene un secreto desde Google Secret Manager
    """
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{os.environ.get('GOOGLE_CLOUD_PROJECT')}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

def init_connection_engine():
    """
    Inicializa un motor de conexión para Google Cloud SQL
    """
    # Determina si estamos en entorno local o en producción
    if os.environ.get("GAE_ENV") == "standard" or os.environ.get("K_SERVICE"):
        # Estamos en GCP
        try:
            # Obtener credenciales desde Secret Manager
            db_user = get_secret("db_user")
            db_pass = get_secret("db_pass")
            db_name = get_secret("db_name")
            instance_connection_name = os.environ.get("INSTANCE_CONNECTION_NAME")
            
            # Inicializar el conector
            connector = Connector()
            
            # Función para crear conexiones a la base de datos
            def getconn():
                conn = connector.connect(
                    instance_connection_name,
                    "pg8000",
                    user=db_user,
                    password=db_pass,
                    db=db_name,
                )
                return conn
            
            # Crear el engine con el pool de conexiones
            engine = sqlalchemy.create_engine(
                "postgresql+pg8000://",
                creator=getconn,
                pool_size=5,
                max_overflow=2,
                pool_timeout=30,
                pool_recycle=1800,
            )
            return engine
        except Exception as e:
            print(f"Error al conectar a Cloud SQL: {e}")
            # Fallback a la configuración de DATABASE_URL en producción
            db_url = os.environ.get("DATABASE_URL")
            if db_url:
                return sqlalchemy.create_engine(db_url)
            raise
    else:
        # Entorno local - usar DATABASE_URL normal
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            raise ValueError("DATABASE_URL no está configurado")
        return sqlalchemy.create_engine(db_url)
