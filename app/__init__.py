from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
import os
from app.utils import format_cop
from flask_mail import Mail

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
    
    # Resto del código...
    
    # Importar y aplicar configuraciones
    from app.config import config_dict
    app.config.from_object(config_dict[config_name])
    mail.init_app(app)
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
    csrf.init_app(app)
    
    # Registrar blueprints
    from app.public import bp as public_bp
    app.register_blueprint(public_bp)
    
    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    from app.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    return app




