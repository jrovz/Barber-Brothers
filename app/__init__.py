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
login_manager.login_view = 'admin.login'
login_manager.login_message = 'Por favor, inicia sesión para acceder a esta página.'
login_manager.login_message_category = 'info'

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
    
    # Habilitar modo debug y mostrar errores detallados en Cloud Run
    if os.environ.get('FLASK_DEBUG_GCP', 'False').lower() in ['true', '1', 't']:
        app.logger.info("Modo de depuración habilitado en GCP")
        app.config['DEBUG'] = True
        app.config['PROPAGATE_EXCEPTIONS'] = True
        app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = True
    
    # Verificar si estamos en entorno GCP y configurar Storage
    if os.environ.get("GAE_ENV") == "standard" or os.environ.get("K_SERVICE"):
        app.logger.info("Detectado entorno GCP. Configurando Cloud Storage...")
        try:
            # Asegurarse de que el bucket esté configurado
            if not os.environ.get('GCS_BUCKET_NAME'):
                app.logger.warning("GCS_BUCKET_NAME no está configurado. El almacenamiento de archivos puede no funcionar correctamente.")
        except Exception as e:
            app.logger.error(f"Error configurando Cloud Storage: {e}")
    
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
    
    # Initialize the database if needed (run migrations and import initial data)
    with app.app_context():
        try:
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
    
    return app




