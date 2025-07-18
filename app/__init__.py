from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
import os
from app.utils import format_cop
from flask_mail import Mail
import logging

# Definir extensiones
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
mail = Mail()
# Configuración de login
login_manager.login_view = 'admin.login'  # Vista predeterminada para admin
login_manager.login_message = 'Por favor, inicia sesión para acceder a esta página.'
login_manager.login_message_category = 'info'

# Configuración personalizada para diferentes tipos de usuarios
def init_login_manager(app):
    @login_manager.user_loader
    def load_user(user_id):
        # Primero intentamos cargar un admin
        from app.models.admin import User
        admin = User.query.get(int(user_id))
        if admin:
            return admin
            
        # Si no es admin, intentamos cargar un barbero
        from app.models.barbero import Barbero
        barbero = Barbero.query.get(int(user_id))
        if barbero:
            return barbero
            
        return None

# Detectar entorno Azure - (Desactivado para entorno local)
def is_azure():
    """Detecta si estamos en Azure App Service"""
    return False  # Forzar siempre entorno local

# Función para cargar usuario (requerida por Flask-Login)
@login_manager.user_loader
def load_user(user_id):
    from app.models import User
    return User.query.get(int(user_id))

def create_app(config_name='default'):
    # Crear instancia de Flask
    app = Flask(__name__, 
                static_folder='static',
                static_url_path='/static')
   
    # CORRECCIÓN: Configuración de carga de archivos con ruta absoluta explícita
    basedir = os.path.abspath(os.path.dirname(__file__))
    print(f"Basedir original: {basedir}")
    
    # Verificar si la ruta contiene duplicación
    if basedir.endswith('app\\app') or basedir.endswith('app/app'):
        # Corregir la ruta eliminando la duplicación
        basedir = os.path.dirname(basedir)
        print(f"Basedir corregido (eliminada duplicación): {basedir}")
    
    # Construir la ruta completa para uploads
    UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')
    print(f"UPLOAD_FOLDER configurado: {UPLOAD_FOLDER}")
    
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    app.jinja_env.filters['cop_format'] = format_cop
    # Crear carpeta de uploads si no existe
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    # Configurar logging para GCP o entorno local
    try:
        from app.utils.cloud_logging import setup_logging
        logger = setup_logging(app)
        app.logger.info("Aplicación inicializada con configuración de logging")
    except ImportError:
        # Fallback si no se puede importar cloud_logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler()]
        )
        app.logger.info("Aplicación inicializada con configuración de logging básica")
    
    # Resto del código...
      # Importar y aplicar configuraciones
    from app.config import config_dict
    app.config.from_object(config_dict[config_name])
    mail.init_app(app)
    
    # Integrar el manejador de errores personalizado
    try:
        from app.utils.error_handler import setup_error_handlers
        setup_error_handlers(app)
        app.logger.info("Manejador de errores personalizado configurado correctamente")
    except Exception as e:
        app.logger.error(f"Error al configurar manejador de errores: {str(e)}", exc_info=True)
    
    # Habilitar modo debug en entornos específicos
    if os.environ.get('FLASK_DEBUG', 'False').lower() in ['true', '1', 't']:
        app.logger.info("Modo de depuración habilitado")
        app.config['DEBUG'] = True
        app.config['PROPAGATE_EXCEPTIONS'] = True
        app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = True
      # Configurar almacenamiento para entorno local
    app.logger.info("Configurando almacenamiento local...")
    # No se requiere configuración especial para almacenamiento local
    # Los archivos se guardarán en el directorio UPLOAD_FOLDER configurado anteriormente
    
     # Verificar rutas después de cargar configuración completa
    @app.before_request
    def verify_upload_path():
        from app.utils.path_checker import check_upload_path
        check_upload_path()
    

    @app.after_request
    def add_security_and_charset_headers(response):
        # Tu código existente...
        return response
      # Inicializar extensiones con la app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    init_login_manager(app)  # Inicializar el manejador de login personalizado
    
    # Initialize the database if needed (run migrations and import initial data)
    with app.app_context():
        try:
            # Usar módulo de conexión local
            app.logger.info("Usando módulo de conexión local para la base de datos")
            from app.utils.local_connection_pg import init_connection_engine
                
            # Inicializar la base de datos
            from app.utils.db_init_handler import init_database_if_needed
            init_database_if_needed()
            app.logger.info("Database initialization check completed.")
        except Exception as e:
            app.logger.error(f"Error during database initialization check: {e}")
    csrf.init_app(app)
    
    # Registrar blueprints
    from app.public import bp as public_bp
    app.register_blueprint(public_bp)
    
    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    from app.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    from app.barbero import bp as barbero_bp
    app.register_blueprint(barbero_bp, url_prefix='/barbero')
    
    return app




