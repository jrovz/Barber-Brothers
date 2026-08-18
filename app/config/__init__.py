import os
from dotenv import load_dotenv
from sqlalchemy.pool import StaticPool

load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'desarrollo-clave-segura'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    # Configuraciones para carga de archivos    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    MAX_CONTENT_LENGTH = 30 * 1024 * 1024  # 30 MB límite de tamaño
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() in ['true', '1', 't']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    # Forma recomendada de configurar MAIL_DEFAULT_SENDER
    MAIL_DEFAULT_SENDER_NAME = os.environ.get('MAIL_DEFAULT_SENDER', 'Barber Brothers')
    MAIL_DEFAULT_SENDER = (MAIL_DEFAULT_SENDER_NAME, os.environ.get('MAIL_USERNAME'))

    
class DevelopmentConfig(Config):
    DEBUG = True
    # Lee la URL de PostgreSQL del entorno, si no existe, usa SQLite como fallback
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, '..', 'app.db') # Ruta relativa a la raíz del proyecto
    
class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    # Configuración de base de datos para producción usando PostgreSQL estándar
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    if SQLALCHEMY_DATABASE_URI is None:
        raise ValueError("DATABASE_URL environment variable is required for production")

    SECRET_KEY = os.environ.get('SECRET_KEY')
    if SECRET_KEY is None:
        raise ValueError("SECRET_KEY environment variable is required for production")

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    # Comparte una única conexión en memoria entre requests/hilos de prueba;
    # sin esto, cada conexión nueva del pool ve una base de datos SQLite distinta y vacía.
    SQLALCHEMY_ENGINE_OPTIONS = {
        'poolclass': StaticPool,
        'connect_args': {'check_same_thread': False},
    }

# Diccionario para seleccionar configuración
config_dict = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
