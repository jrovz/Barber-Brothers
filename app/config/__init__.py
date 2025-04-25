import os
from dotenv import load_dotenv

load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'desarrollo-clave-segura'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Configuraciones para carga de archivos
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app', 'static', 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB límite de tamaño

class DevelopmentConfig(Config):
    DEBUG = True
    # Lee la URL de PostgreSQL del entorno, si no existe, usa SQLite como fallback
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, '..', 'app.db') # Ruta relativa a la raíz del proyecto
    
class ProductionConfig(Config):
    DEBUG = False
    # Production debería SIEMPRE usar DATABASE_URL
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    if SQLALCHEMY_DATABASE_URI is None:
        raise ValueError("No DATABASE_URL set for production")

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