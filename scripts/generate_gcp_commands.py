#!/usr/bin/env python
"""
Script para generar comandos de verificación y corrección de problemas en GCP

Este script genera los comandos que necesitas ejecutar en GCP para solucionar
problemas de autenticación con el panel de administración.
"""
import os
import sys
import argparse

def generate_commands(project_id=None, region=None, instance_name=None):
    """
    Genera los comandos necesarios para verificar y corregir problemas en GCP
    """
    if not project_id:
        project_id = "barber-brothers-460514"  # ID por defecto
    
    if not region:
        region = "us-central1"  # Región por defecto
    
    if not instance_name:
        instance_name = "barberia-db"  # Nombre de instancia por defecto
    
    print("\n=== COMANDOS PARA VERIFICAR Y SOLUCIONAR PROBLEMAS DE AUTENTICACIÓN EN GCP ===\n")
    
    print("# 1. Configuración del entorno")
    print("# Exporta las variables de entorno necesarias para la conexión a Cloud SQL")
    print(f"export GOOGLE_CLOUD_PROJECT={project_id}")
    print(f"export CLOUD_SQL_REGION={region}")
    print(f"export CLOUD_SQL_INSTANCE={instance_name}")
    print('export INSTANCE_CONNECTION_NAME="${GOOGLE_CLOUD_PROJECT}:${CLOUD_SQL_REGION}:${CLOUD_SQL_INSTANCE}"')
    print('export DB_USER="barberia_user"')
    print('export DB_NAME="barberia_db"')
    print('# Asegúrate de tener una contraseña segura para DB_PASS')
    print('# export DB_PASS="tu_contraseña_segura"')
    print()
    
    print("# 2. Verificar usuario administrador en PostgreSQL")
    print("# Este comando se conecta a Cloud SQL y verifica si existe el usuario administrador")
    print("python scripts/verify_admin_gcp.py")
    print()
    
    print("# 3. Solucionar problemas de autenticación")
    print("# Este comando corrige problemas con el usuario administrador")
    print("python scripts/fix_gcp_admin_auth.py --username admin --email admin@example.com")
    print()
    
    print("# 4. Mejorar el manejo de errores de autenticación")
    print("# Este comando añade middleware de depuración para autenticación")
    print("python scripts/improve_auth_debug.py")
    print()
    
    print("# 5. Consultar logs de error en Cloud Run")
    print("# Este comando muestra los logs de error de la aplicación")
    print(f"gcloud logging read \"resource.type=cloud_run_revision AND resource.labels.service_name=barberia-app AND severity>=ERROR\" --limit=20")
    print()
    
    print("# 6. Habilitar modo debug en Cloud Run")
    print("# Este comando despliega la aplicación con modo debug activado")
    print("gcloud run deploy barberia-app --source=. --set-env-vars=FLASK_DEBUG=1")
    print()
    
    print("# 7. Cuando hayas solucionado el problema, desactiva el modo debug")
    print("gcloud run deploy barberia-app --source=. --set-env-vars=FLASK_DEBUG=0")
    print()

def main():
    parser = argparse.ArgumentParser(description='Generar comandos para solucionar problemas en GCP')
    parser.add_argument('--project-id', help='ID del proyecto de GCP')
    parser.add_argument('--region', help='Región de GCP donde está desplegado Cloud SQL')
    parser.add_argument('--instance-name', help='Nombre de la instancia de Cloud SQL')
    
    args = parser.parse_args()
    
    generate_commands(args.project_id, args.region, args.instance_name)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
