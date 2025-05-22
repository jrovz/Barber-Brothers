import os
from google.cloud.sql.connector import Connector
import sqlalchemy
import pymysql
from google.cloud import secretmanager

def get_secret(secret_id):
    """
    Obtiene un secreto desde Google Secret Manager
    """
    try:
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            print(f"GOOGLE_CLOUD_PROJECT no está configurado. Variables de entorno disponibles: {list(os.environ.keys())}")
            raise ValueError("GOOGLE_CLOUD_PROJECT no está configurado")
            
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        print(f"Intentando obtener secreto: {secret_id} desde: {name}")
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        print(f"Error obteniendo secreto {secret_id}: {str(e)}")
        raise

def init_connection_engine():
    """
    Inicializa un motor de conexión para Google Cloud SQL
    """
    # Determina si estamos en entorno local o en producción
    print(f"Entorno: GAE_ENV={os.environ.get('GAE_ENV')}, K_SERVICE={os.environ.get('K_SERVICE')}")
    
    if os.environ.get("GAE_ENV") == "standard" or os.environ.get("K_SERVICE"):
        # Estamos en GCP
        try:
            print("Iniciando conexión a Cloud SQL en entorno GCP")
            # Obtener credenciales desde Secret Manager
            db_user = get_secret("db_user")
            db_pass = get_secret("db_pass")
            db_name = get_secret("db_name")
            instance_connection_name = os.environ.get("INSTANCE_CONNECTION_NAME")
            
            if not instance_connection_name:
                print("Error: INSTANCE_CONNECTION_NAME no está configurada en el entorno")
                raise ValueError("INSTANCE_CONNECTION_NAME no está configurada")
            
            print(f"Información de conexión: usuario={db_user}, db={db_name}, instancia={instance_connection_name}")
              # Inicializar el conector
            connector = Connector()
            
            # Función para crear conexiones a la base de datos
            def getconn():
                print(f"Intentando conectar a: {instance_connection_name}")
                conn = connector.connect(
                    instance_connection_name,
                    "pymysql",  # Cambiado de pg8000 a pymysql para MySQL
                    user=db_user,
                    password=db_pass,
                    db=db_name,
                )
                print("Conexión exitosa a la base de datos")
                return conn
                
            # Crear el engine con el pool de conexiones
            engine = sqlalchemy.create_engine(
                "mysql+pymysql://",
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
