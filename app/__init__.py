from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect # Añadido

# Definir extensiones aquí para evitar importaciones circulares
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect() # Añadido

login_manager.login_view = 'admin.login' # Ruta a la que redirigir si no está logueado
login_manager.login_message = 'Por favor, inicia sesión para acceder a esta página.' # Mensaje flash
login_manager.login_message_category = 'info' # Categoría del mensaje flash

# Función para cargar usuario (requerida por Flask-Login)
@login_manager.user_loader
def load_user(user_id):
    from app.models import User # Importar aquí para evitar importación circular
    return User.query.get(int(user_id))

def create_app(config_name='default'):
    # Especifica static_folder relativo al directorio de la app (__name__)
    # y el prefijo de URL para acceder a esos archivos.
    app = Flask(__name__, 
                static_folder='static',      # Nombre de la carpeta dentro de 'app'
                static_url_path='/static')   # URL base para acceder a los archivos estáticos
    
    @app.after_request
    def add_security_and_charset_headers(response):
        # Punto 1: Asegurar charset=utf-8 si no está presente
        # Verifica si 'charset' ya está en el Content-Type (insensible a mayúsculas/minúsculas)
        if 'charset' not in response.headers.get('Content-Type', '').lower():
            # Si no está, lo añade explícitamente
            response.charset = 'utf-8' 
        
        # Punto 4: Añadir X-Content-Type-Options
        # Evita que el navegador intente adivinar el tipo MIME
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # Punto 6: Añadir Content-Security-Policy (reemplaza X-Frame-Options)
        # 'frame-ancestors \'self\'' previene clickjacking permitiendo iframes solo desde tu propio dominio.
        # Puedes añadir más directivas CSP aquí si lo necesitas (ej., para scripts, estilos, etc.)
        # Si ya tienes un encabezado CSP, asegúrate de que incluya 'frame-ancestors \'self\';'
        if 'Content-Security-Policy' not in response.headers:
             response.headers['Content-Security-Policy'] = "frame-ancestors 'self';"
        # Nota: Si usas Flask-Talisman, podría manejar esto por ti. Verifica su configuración.

        # Eliminar encabezados obsoletos/innecesarios si los añade algún otro componente
        # (Flask no los añade por defecto, pero podrían venir de otro lado)
        # response.headers.pop('X-Frame-Options', None) 
        # response.headers.pop('X-XSS-Protection', None)
        # response.headers.pop('Expires', None) 
        # Descomenta las líneas pop si sabes que estos encabezados se están añadiendo y quieres forzar su eliminación.

        # Devuelve el objeto response modificado
        return response
    
    # Importar y aplicar configuraciones
    from app.config import config_dict
    app.config.from_object(config_dict[config_name])
    
    # Inicializar extensiones con la app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app) # Añadido: Inicializar CSRFProtect
    
    # Registrar blueprints
    from app.public import bp as public_bp
    app.register_blueprint(public_bp)
    
    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    from app.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    return app

# from flask import render_template, request # ... otros imports ...
# from app.public import bp
# from app.models import Producto, Cliente, Mensaje, Servicio # Añadir Servicio
# from app import db




