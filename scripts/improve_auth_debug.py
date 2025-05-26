#!/usr/bin/env python
"""
Script para mejorar el manejo de errores y debugging de autenticación

Este script añade middleware para capturar y registrar errores de autenticación
en la aplicación Flask desplegada en GCP.
"""
import os
import sys
import argparse
import traceback

def generate_middleware_code():
    """
    Genera el código para el middleware de manejo de errores de autenticación
    """
    return """
import logging
import traceback
from functools import wraps
from flask import request, current_app, jsonify, session
from werkzeug.exceptions import HTTPException

logger = logging.getLogger('auth_debug')

class AuthDebugMiddleware:
    def __init__(self, app):
        self.app = app
        # Configurar logger específico
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        
        app.logger.info("AuthDebugMiddleware inicializado")
        
        # Añadir interceptor de errores
        self._register_error_handlers(app)
    
    def _register_error_handlers(self, app):
        @app.errorhandler(Exception)
        def handle_exception(e):
            # Pasar errores HTTP normales
            if isinstance(e, HTTPException):
                # Registrar información sobre errores HTTP
                logger.warning(f"Error HTTP {e.code}: {e.description}")
                return e
            
            # Registrar errores no HTTP (errores 500)
            logger.error(f"Error no manejado: {str(e)}")
            traceback.print_exc()
            
            # Registrar información de sesión y contexto si es posible
            try:
                self._log_session_info()
                self._log_auth_info()
            except Exception as session_error:
                logger.error(f"Error al registrar información de sesión: {str(session_error)}")
            
            # Devolver respuesta JSON para API o página de error para navegador
            if request.path.startswith('/api/'):
                return jsonify({
                    'error': 'Internal Server Error',
                    'message': str(e) if app.debug else 'Ha ocurrido un error en el servidor'
                }), 500
            else:
                return self.app.finalize_request(e)
    
    def _log_session_info(self):
        """Registra información relevante de la sesión para depuración"""
        if session:
            logger.debug("Información de sesión:")
            for key in session:
                # Evitar registrar información sensible
                if key not in ['_csrf_token', 'password']:
                    logger.debug(f"  {key}: {session[key]}")
        else:
            logger.debug("No hay información de sesión disponible")
    
    def _log_auth_info(self):
        """Registra información de autenticación para depuración"""
        from flask_login import current_user
        
        logger.debug("Información de autenticación:")
        if current_user.is_authenticated:
            logger.debug(f"  Usuario autenticado: {current_user.username}")
            if hasattr(current_user, 'role'):
                logger.debug(f"  Rol: {current_user.role}")
            if hasattr(current_user, 'is_admin'):
                logger.debug(f"  Es admin: {current_user.is_admin()}")
        else:
            logger.debug("  Usuario no autenticado")

# Decorador para mejorar el registro de actividad en rutas de autenticación
def debug_auth_route(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.debug(f"Acceso a ruta de autenticación: {request.path}")
        logger.debug(f"Método: {request.method}")
        logger.debug(f"Datos del formulario: {request.form}")
        
        try:
            result = func(*args, **kwargs)
            logger.debug(f"Resultado de autenticación exitoso: {result}")
            return result
        except Exception as e:
            logger.error(f"Error en ruta de autenticación: {str(e)}")
            traceback.print_exc()
            raise
    
    return wrapper
"""

def create_middleware_file(file_path):
    """
    Crea el archivo de middleware para depuración de autenticación
    """
    try:
        with open(file_path, 'w') as f:
            f.write(generate_middleware_code())
        print(f"✅ Archivo middleware generado: {file_path}")
        return True
    except Exception as e:
        print(f"❌ Error al crear archivo middleware: {e}")
        return False

def update_app_init(init_file_path):
    """
    Actualiza el archivo __init__.py de la aplicación para integrar el middleware
    """
    try:
        # Leer el archivo actual
        with open(init_file_path, 'r') as f:
            content = f.read()
        
        # Verificar si ya se ha integrado el middleware
        if "from app.utils.auth_debug import AuthDebugMiddleware" in content:
            print("⚠️ El middleware de depuración ya está integrado en el archivo __init__.py")
            return True
        
        # Buscar el punto de inserción (después de crear la aplicación Flask)
        import_line = "from app.utils.auth_debug import AuthDebugMiddleware\n"
        middleware_line = "    # Integrar middleware de depuración de autenticación\n    AuthDebugMiddleware(app)\n"
        
        # Agregar importación
        if "import os" in content:
            content = content.replace("import os", "import os\n" + import_line, 1)
        else:
            # Si no encuentra la línea específica, agrega al principio
            content = import_line + content
        
        # Agregar la línea para inicializar el middleware
        if "# Registrar blueprints" in content:
            content = content.replace("# Registrar blueprints", middleware_line + "# Registrar blueprints", 1)
        elif "from app.models import" in content:
            content = content.replace("from app.models import", middleware_line + "from app.models import", 1)
        else:
            print("⚠️ No se pudo encontrar un lugar adecuado para insertar el middleware")
            return False
        
        # Escribir el archivo actualizado
        with open(init_file_path, 'w') as f:
            f.write(content)
        
        print(f"✅ Archivo __init__.py actualizado: {init_file_path}")
        return True
    except Exception as e:
        print(f"❌ Error al actualizar archivo __init__.py: {e}")
        traceback.print_exc()
        return False

def update_admin_routes(routes_file_path):
    """
    Actualiza el archivo de rutas de administración para usar el decorador de depuración
    """
    try:
        # Leer el archivo actual
        with open(routes_file_path, 'r') as f:
            content = f.read()
        
        # Verificar si ya se ha integrado el decorador
        if "from app.utils.auth_debug import debug_auth_route" in content:
            print("⚠️ El decorador de depuración ya está integrado en el archivo de rutas")
            return True
        
        # Agregar importación del decorador
        import_line = "from app.utils.auth_debug import debug_auth_route\n"
        
        if "from .forms import" in content:
            content = content.replace("from .forms import", import_line + "from .forms import", 1)
        else:
            # Si no encuentra la línea específica, agrega después de los imports
            content = content.replace("import logging", "import logging\n" + import_line, 1)
        
        # Reemplazar la definición de la ruta de login con el decorador
        old_route = "@bp.route('/login', methods=['GET', 'POST'])\ndef login():"
        new_route = "@bp.route('/login', methods=['GET', 'POST'])\n@debug_auth_route\ndef login():"
        
        if old_route in content:
            content = content.replace(old_route, new_route)
        else:
            print("⚠️ No se pudo encontrar la definición de la ruta de login para añadir el decorador")
            return False
        
        # Escribir el archivo actualizado
        with open(routes_file_path, 'w') as f:
            f.write(content)
        
        print(f"✅ Archivo de rutas actualizado: {routes_file_path}")
        return True
    except Exception as e:
        print(f"❌ Error al actualizar archivo de rutas: {e}")
        traceback.print_exc()
        return False

def main():
    # Configurar argumentos de línea de comandos
    parser = argparse.ArgumentParser(description='Mejorar manejo de errores para problemas de autenticación')
    parser.add_argument('--basedir', default=None, help='Directorio base de la aplicación')
    
    args = parser.parse_args()
    
    basedir = args.basedir
    if not basedir:
        # Intentar determinar el directorio base
        script_dir = os.path.dirname(os.path.abspath(__file__))
        basedir = os.path.dirname(script_dir)
    
    print(f"Directorio base: {basedir}")
    
    # Rutas a los archivos que se modificarán
    middleware_path = os.path.join(basedir, 'app', 'utils', 'auth_debug.py')
    init_path = os.path.join(basedir, 'app', '__init__.py')
    routes_path = os.path.join(basedir, 'app', 'admin', 'routes.py')
    
    # Verificar que los archivos existen
    if not os.path.exists(os.path.dirname(middleware_path)):
        print(f"❌ El directorio {os.path.dirname(middleware_path)} no existe")
        return 1
    
    if not os.path.exists(init_path):
        print(f"❌ El archivo {init_path} no existe")
        return 1
    
    if not os.path.exists(routes_path):
        print(f"❌ El archivo {routes_path} no existe")
        return 1
    
    # Crear y actualizar archivos
    success = create_middleware_file(middleware_path)
    if not success:
        return 1
    
    success = update_app_init(init_path)
    if not success:
        return 1
    
    success = update_admin_routes(routes_path)
    if not success:
        return 1
    
    print("\n✅ Mejoras de depuración de autenticación aplicadas con éxito")
    print("Para activar completamente el modo de depuración, actualiza tu aplicación en GCP")
    
    # Generar comandos para GCP
    print("\nComandos para aplicar los cambios en GCP:")
    print("1. Sincroniza los archivos modificados:")
    print("   (Usa tu método habitual para subir cambios a GCP)")
    print("\n2. Despliega la aplicación con variables de entorno para depuración:")
    print("   gcloud run deploy barberia-app --source=. --set-env-vars=FLASK_DEBUG=1")
    print("\n3. Después de resolver el problema, recuerda desactivar el modo depuración:")
    print("   gcloud run deploy barberia-app --source=. --set-env-vars=FLASK_DEBUG=0")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
