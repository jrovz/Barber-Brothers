"""
Módulo centralizado de configuración para GCP y PostgreSQL.
Proporciona constantes y funciones para acceder a configuraciones
de manera estandarizada en todo el proyecto.
"""
import os
from google.cloud import secretmanager

# Regiones predeterminadas (pueden ser sobrescritas por variables de entorno)
DEFAULT_GCP_REGION = "us-east1"
DEFAULT_DB_REGION = "us-east1"

def get_project_id():
    """
    Obtiene el ID del proyecto GCP.
    Primero intenta obtenerlo de las variables de entorno,
    luego del nombre de conexión de la instancia.
    """
    project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
    if not project_id:
        # Intentar extraer el project_id del INSTANCE_CONNECTION_NAME
        instance_connection = os.environ.get("INSTANCE_CONNECTION_NAME", "")
        if instance_connection and ":" in instance_connection:
            project_id = instance_connection.split(":")[0]
        else:
            # Usar el ID por defecto como último recurso
            project_id = "barber-brothers-460514"
    
    return project_id

def get_gcp_region():
    """
    Obtiene la región GCP para servicios como Cloud Run.
    """
    return os.environ.get("REGION", DEFAULT_GCP_REGION)

def get_db_region():
    """
    Obtiene la región GCP para Cloud SQL.
    """
    return os.environ.get("DB_REGION", os.environ.get("REGION", DEFAULT_DB_REGION))

def get_instance_name():
    """
    Obtiene el nombre de la instancia de Cloud SQL.
    """
    return os.environ.get("INSTANCE_NAME", "barberia-db")

def get_instance_connection_name():
    """
    Construye el nombre completo de conexión a la instancia Cloud SQL.
    """
    instance_connection_name = os.environ.get("INSTANCE_CONNECTION_NAME")
    if not instance_connection_name:
        project_id = get_project_id()
        db_region = get_db_region()
        instance_name = get_instance_name()
        instance_connection_name = f"{project_id}:{db_region}:{instance_name}"
    
    return instance_connection_name

def get_secret(secret_id):
    """
    Obtiene un secreto desde Google Secret Manager.
    
    Args:
        secret_id: ID del secreto a obtener
        
    Returns:
        El valor del secreto o None si no se pudo obtener
    """
    try:
        project_id = get_project_id()
        
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        print(f"Error obteniendo secreto {secret_id}: {str(e)}")
        # No hacer raise, dejar que el código continúe con los valores por defecto
        return None

def get_db_credentials():
    """
    Obtiene las credenciales de la base de datos.
    Primero intenta obtenerlas de Secret Manager,
    luego de variables de entorno y finalmente usa valores por defecto.
    
    Returns:
        Tupla con (usuario, contraseña, nombre_db)
    """
    # Usuario de la base de datos
    db_user = get_secret("db_user")
    if not db_user:
        db_user = os.environ.get("DB_USER", "barberia_user")
    
    # Contraseña
    db_pass = get_secret("db_pass")
    if not db_pass:
        db_pass = os.environ.get("DB_PASS", "")
    
    # Nombre de la base de datos
    db_name = get_secret("db_name")
    if not db_name:
        db_name = os.environ.get("DB_NAME", "barberia_db")
    
    return db_user, db_pass, db_name

def get_db_socket_dir():
    """
    Obtiene el directorio del socket para Cloud SQL.
    """
    return os.environ.get("DB_SOCKET_DIR", "/cloudsql")

def build_database_url():
    """
    Construye la URL de conexión a la base de datos PostgreSQL.
    
    Returns:
        URL completa para conexión a la base de datos
    """
    # Verificar si ya tenemos una URL configurada
    db_url = os.environ.get("DATABASE_URL")
    if db_url and "postgresql" in db_url:
        return db_url
    
    # Construir la URL manualmente
    db_user, db_pass, db_name = get_db_credentials()
    instance_connection_name = get_instance_connection_name()
    db_socket_dir = get_db_socket_dir()
    
    # Determinar si estamos en producción (GCP) o desarrollo
    is_production = os.environ.get("GAE_ENV") == "standard" or os.environ.get("K_SERVICE")
    
    if is_production:
        # Formato para producción con socket Unix
        return f"postgresql+pg8000://{db_user}:{db_pass}@/{db_name}?unix_socket={db_socket_dir}/{instance_connection_name}"
    else:
        # Formato para desarrollo local
        db_host = os.environ.get("DB_HOST", "localhost")
        db_port = os.environ.get("DB_PORT", "5432")
        return f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

def is_production():
    """
    Determina si estamos en un entorno de producción (GCP).
    
    Returns:
        Boolean indicando si estamos en producción
    """
    return os.environ.get("GAE_ENV") == "standard" or os.environ.get("K_SERVICE")
