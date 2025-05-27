import os
from dotenv import load_dotenv

load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'desarrollo-clave-segura'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Configuraciones para carga de archivos
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB límite de tamaño
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() in ['true', '1', 't']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    # Forma recomendada de configurar MAIL_DEFAULT_SENDER
    MAIL_DEFAULT_SENDER_NAME = os.environ.get('MAIL_DEFAULT_SENDER_NAME', 'Barber Brothers')
    MAIL_DEFAULT_SENDER = (MAIL_DEFAULT_SENDER_NAME, os.environ.get('MAIL_USERNAME'))

    
class DevelopmentConfig(Config):
    DEBUG = True
    # Lee la URL de PostgreSQL del entorno, si no existe, usa SQLite como fallback
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, '..', 'app.db') # Ruta relativa a la raíz del proyecto
    
class ProductionConfig(Config):
    DEBUG = False
    # En GCP, usaremos Cloud SQL Connector o DATABASE_URL según corresponda
    try:
        # Si estamos en GCP
        if os.environ.get("GAE_ENV") == "standard" or os.environ.get("K_SERVICE"):
            # Método preferido: usar Cloud SQL Connector para PostgreSQL
            from app.utils.cloud_connection_pg import init_connection_engine
            
            # El DATABASE_URL se usa dentro de init_connection_engine() 
            # con el orden de prioridad correcto
            print("Inicializando el motor de conexión para Cloud SQL PostgreSQL...")
            engine = init_connection_engine()
            
            # Guardar el engine para su uso en SQLAlchemy
            SQLALCHEMY_ENGINE = engine
            
            # Si estamos usando connection_string, podemos asignar DATABASE_URL
            db_url = os.environ.get('DATABASE_URL')
            if db_url and "postgresql" in db_url:
                print(f"Config: Usando DATABASE_URL para PostgreSQL: {db_url}")
                SQLALCHEMY_DATABASE_URI = db_url
            else:
                # Si no hay DATABASE_URL o estamos usando connector directo,
                # SQLAlchemy usará el engine directamente
                SQLALCHEMY_DATABASE_URI = None
                print("Config: Usando engine directo para la conexión a PostgreSQL")
        else:
            # Si no estamos en GCP, usamos DATABASE_URL normal (entorno de desarrollo)
            SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
            if SQLALCHEMY_DATABASE_URI is None:
                raise ValueError("No DATABASE_URL set for production")
    except Exception as e:
        print(f"Error en configuración de producción: {e}")
        # Fallback a la configuración estándar
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
        print(f"Usando fallback DATABASE_URL: {SQLALCHEMY_DATABASE_URI}")
        if SQLALCHEMY_DATABASE_URI is None:            # Última opción, construir DATABASE_URL manualmente
            try:
                db_user = os.environ.get("DB_USER", "barberia_user")
                db_pass = os.environ.get("DB_PASS", "BarberiaSecure123!")
                db_name = os.environ.get("DB_NAME", "barberia_db")
                project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "barber-brothers-460514")
                instance = os.environ.get("INSTANCE_CONNECTION_NAME", f"{project_id}:us-east1:barberia-db")
                
                # URI para PostgreSQL (cambiado de MySQL)
                SQLALCHEMY_DATABASE_URI = f"postgresql+psycopg2://{db_user}:{db_pass}@/{db_name}?host=/cloudsql/{instance}"
                print(f"Usando DATABASE_URL construido manualmente para PostgreSQL: {SQLALCHEMY_DATABASE_URI}")
            except Exception as e2:
                print(f"Error construyendo DATABASE_URL: {e2}")
                raise ValueError("No DATABASE_URL set for production and could not build one")

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

# Diccionario para seleccionar configuración
config_dict = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
