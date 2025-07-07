#!/usr/bin/env python3
"""
Script para diagnosticar y solucionar el error 413 'Request Entity Too Large'
en la aplicación Barber Brothers en producción
"""

import os
import subprocess
import sys
from pathlib import Path

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")

def print_status(text):
    print(f"✅ {text}")

def print_error(text):
    print(f"❌ {text}")

def print_warning(text):
    print(f"⚠️ {text}")

def run_command(command, description=""):
    """Ejecuta un comando y muestra el resultado"""
    try:
        if description:
            print(f"\n🔍 {description}")
        print(f"$ {command}")
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(f"Error: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"Error ejecutando comando: {e}")
        return False

def check_file_sizes():
    """Verifica tamaños de archivos en la carpeta uploads"""
    print_header("VERIFICANDO TAMAÑOS DE ARCHIVOS")
    
    upload_path = "/opt/barber-brothers/app/static/uploads/sliders"
    if os.path.exists(upload_path):
        run_command(f"ls -lh {upload_path}", "Tamaños de archivos en sliders:")
    else:
        print_warning("La carpeta sliders no existe")

def check_nginx_config():
    """Verifica y corrige configuración de nginx"""
    print_header("VERIFICANDO CONFIGURACIÓN DE NGINX")
    
    nginx_config = "/etc/nginx/sites-available/barber-brothers"
    if os.path.exists(nginx_config):
        run_command(f"grep -n 'client_max_body_size' {nginx_config}", 
                   "Configuración actual de client_max_body_size:")
    else:
        print_error("Archivo de configuración de nginx no encontrado")

def fix_nginx_config():
    """Aumenta el límite de nginx"""
    print_header("SOLUCIONANDO CONFIGURACIÓN DE NGINX")
    
    nginx_config = "/etc/nginx/sites-available/barber-brothers"
    
    # Backup de la configuración actual
    run_command(f"sudo cp {nginx_config} {nginx_config}.backup", 
               "Creando backup de configuración nginx")
    
    # Aumentar client_max_body_size
    run_command(f"sudo sed -i 's/client_max_body_size 16M;/client_max_body_size 50M;/' {nginx_config}",
               "Aumentando client_max_body_size a 50M")
    
    # Verificar cambios
    run_command(f"grep -n 'client_max_body_size' {nginx_config}",
               "Verificando cambios en nginx:")
    
    # Verificar configuración de nginx
    if run_command("sudo nginx -t", "Verificando configuración nginx"):
        print_status("Configuración de nginx válida")
        # Reiniciar nginx
        if run_command("sudo systemctl reload nginx", "Recargando nginx"):
            print_status("Nginx recargado exitosamente")
        else:
            print_error("Error al recargar nginx")
    else:
        print_error("Error en configuración nginx - restaurando backup")
        run_command(f"sudo cp {nginx_config}.backup {nginx_config}")

def create_gunicorn_config():
    """Crea configuración de gunicorn"""
    print_header("CREANDO CONFIGURACIÓN DE GUNICORN")
    
    gunicorn_config = "/opt/barber-brothers/gunicorn.conf.py"
    
    config_content = '''# Gunicorn configuration for Barber Brothers
bind = "127.0.0.1:5000"
workers = 3
timeout = 120
keepalive = 2
max_requests = 1000
max_requests_jitter = 50
preload_app = True
worker_class = "sync"
worker_connections = 1000

# Configuración de tamaño máximo para uploads
limit_request_line = 8190
limit_request_fields = 100
limit_request_field_size = 8190

# Configuración de memoria y buffers
worker_tmp_dir = "/dev/shm"

# Logs
accesslog = "/var/log/barber-brothers/gunicorn_access.log"
errorlog = "/var/log/barber-brothers/gunicorn_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Configuración de seguridad
forwarded_allow_ips = "127.0.0.1"
proxy_allow_ips = "127.0.0.1"
'''
    
    try:
        with open(gunicorn_config, 'w') as f:
            f.write(config_content)
        print_status(f"Archivo de configuración creado: {gunicorn_config}")
        
        # Cambiar permisos
        run_command(f"sudo chown ubuntu:ubuntu {gunicorn_config}")
        
    except Exception as e:
        print_error(f"Error creando configuración de gunicorn: {e}")

def update_flask_config():
    """Actualiza configuración de Flask"""
    print_header("VERIFICANDO CONFIGURACIÓN DE FLASK")
    
    flask_config = "/opt/barber-brothers/app/config/__init__.py"
    
    if os.path.exists(flask_config):
        run_command(f"grep -n 'MAX_CONTENT_LENGTH' {flask_config}",
                   "Configuración actual de MAX_CONTENT_LENGTH:")
        
        # Actualizar a 50MB
        run_command(f"sudo sed -i 's/MAX_CONTENT_LENGTH = 16 \* 1024 \* 1024/MAX_CONTENT_LENGTH = 50 * 1024 * 1024/' {flask_config}",
                   "Actualizando MAX_CONTENT_LENGTH a 50MB")
        
        run_command(f"grep -n 'MAX_CONTENT_LENGTH' {flask_config}",
                   "Nueva configuración:")
    else:
        print_error("Archivo de configuración de Flask no encontrado")

def restart_services():
    """Reinicia los servicios"""
    print_header("REINICIANDO SERVICIOS")
    
    # Reiniciar aplicación
    if run_command("sudo systemctl restart barber-brothers", "Reiniciando aplicación"):
        print_status("Aplicación reiniciada")
    else:
        print_error("Error reiniciando aplicación")
    
    # Verificar estado
    run_command("sudo systemctl status barber-brothers --no-pager -l", 
               "Estado de la aplicación:")

def check_logs():
    """Verifica logs recientes"""
    print_header("VERIFICANDO LOGS")
    
    print("📋 Logs recientes de nginx:")
    run_command("sudo tail -20 /var/log/nginx/barber-brothers_error.log")
    
    print("\n📋 Logs recientes de la aplicación:")
    run_command("sudo journalctl -u barber-brothers --no-pager -l --since '5 minutes ago'")

def test_upload():
    """Prueba de subida de archivos"""
    print_header("PRUEBA DE FUNCIONAMIENTO")
    
    print("🧪 Para probar la subida de archivos:")
    print("1. Ve a tu panel de admin")
    print("2. Intenta subir una imagen a los sliders")
    print("3. Si aún tienes problemas, verifica los logs con:")
    print("   sudo tail -f /var/log/nginx/barber-brothers_error.log")
    print("   sudo journalctl -u barber-brothers -f")

def main():
    if os.geteuid() != 0:
        print_error("Este script debe ejecutarse con privilegios de root")
        print("Ejecuta: sudo python3 fix_413_error.py")
        sys.exit(1)
    
    print_header("SOLUCIONADOR DE ERROR 413 - BARBER BROTHERS")
    print("Este script diagnosticará y solucionará el error 413 'Request Entity Too Large'")
    
    # Diagnóstico
    check_file_sizes()
    check_nginx_config()
    
    # Soluciones
    fix_nginx_config()
    create_gunicorn_config()
    update_flask_config()
    restart_services()
    
    # Verificación
    check_logs()
    test_upload()
    
    print_header("SOLUCIÓN COMPLETADA")
    print_status("El error 413 debería estar solucionado")
    print_status("Límites actualizados:")
    print("   • Nginx: 50MB")
    print("   • Flask: 50MB")
    print("   • Gunicorn: Configurado optimamente")
    print("\n📞 Si sigues teniendo problemas, verifica:")
    print("   1. Que el archivo no sea mayor a 50MB")
    print("   2. Los logs de nginx y la aplicación")
    print("   3. Que todos los servicios estén corriendo")

if __name__ == "__main__":
    main() 