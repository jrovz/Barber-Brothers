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
            print(f"GOOGLE_CLOUD_PROJECT no está configurado. Usando project_id del INSTANCE_CONNECTION_NAME.")
            # Intentar extraer el project_id del INSTANCE_CONNECTION_NAME
            instance_connection = os.environ.get("INSTANCE_CONNECTION_NAME", "")
            if instance_connection and ":" in instance_connection:
                project_id = instance_connection.split(":")[0]
                print(f"Usando project_id extraído: {project_id}")
            else:
                # Usar el ID de proyecto hardcoded como último recurso
                project_id = "barber-brothers-460514"
                print(f"Usando project_id hardcoded: {project_id}")
            
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        print(f"Intentando obtener secreto: {secret_id} desde: {name}")
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        print(f"Error obteniendo secreto {secret_id}: {str(e)}")
        # No hacer raise, dejar que el código continúe con los valores por defecto
        return None

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
            
            # PRIORIDAD 1: Verificar si tenemos DATABASE_URL con formato para Cloud SQL Proxy
            db_url = os.environ.get("DATABASE_URL")
            if db_url and "unix_socket" in db_url:
                print(f"Usando DATABASE_URL con unix_socket para Cloud SQL")
                # Verificar que la cadena de conexión sea válida
                if ":" in db_url and "@" in db_url and "?" in db_url:
                    print("Formato de DATABASE_URL parece correcto. Creando engine.")
                    return sqlalchemy.create_engine(
                        db_url,
                        pool_size=10,
                        max_overflow=5,
                        pool_timeout=30,
                        pool_recycle=300,
                        pool_pre_ping=True,
                        connect_args={"connect_timeout": 10}
                    )
                    print("Formato de DATABASE_URL parece correcto. Creando engine.")
                    return sqlalchemy.create_engine(
                        db_url,
                        pool_size=5,
                        max_overflow=2,
                        pool_timeout=30,
                        pool_recycle=1800,
                    )
                else:
                    print(f"Formato de DATABASE_URL incorrecto: {db_url}")
            
            # PRIORIDAD 2: Usar variables de entorno directas
            db_user = os.environ.get("DB_USER", "barberia_user")
            db_pass = os.environ.get("DB_PASS", "BarberiaSecure123!")  # Usando la contraseña actualizada
            db_name = os.environ.get("DB_NAME", "barberia_db")
            
            # Intentar obtener el nombre de la instancia
            instance_connection_name = os.environ.get("INSTANCE_CONNECTION_NAME")
            
            if not instance_connection_name:
                print("INSTANCE_CONNECTION_NAME no está configurada, construyéndola desde el project_id")
                project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "barber-brothers-460514")
                instance_connection_name = f"{project_id}:us-central1:barberia-db"
                print(f"INSTANCE_CONNECTION_NAME construida: {instance_connection_name}")
            
            print(f"Información de conexión: usuario={db_user}, db={db_name}, instancia={instance_connection_name}")
              # PRIORIDAD 3: Construir DATABASE_URL manualmente y usarla
            manual_db_url = f"mysql+pymysql://{db_user}:{db_pass}@/{db_name}?unix_socket=/cloudsql/{instance_connection_name}"            print(f"Construyendo DATABASE_URL manualmente: {manual_db_url}")
            
            # También actualizamos la variable de entorno para futuras referencias
            os.environ["DATABASE_URL"] = manual_db_url
            
            return sqlalchemy.create_engine(
                manual_db_url,
                pool_size=10,
                max_overflow=5,
                pool_timeout=30,
                pool_recycle=300,
                pool_pre_ping=True,
                connect_args={"connect_timeout": 10}
            )
            
        except Exception as e:
            print(f"Error al conectar a Cloud SQL: {e}")
            # Último intento - usar DATABASE_URL directo
            db_url = os.environ.get("DATABASE_URL")
            if db_url:
                print(f"Último intento: usando DATABASE_URL como último recurso")
                return sqlalchemy.create_engine(db_url)
            raise ValueError(f"No se pudo establecer conexión a la base de datos: {e}")
    else:
        # Entorno local - usar DATABASE_URL normal
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            raise ValueError("DATABASE_URL no está configurado para desarrollo local")
        return sqlalchemy.create_engine(db_url)
