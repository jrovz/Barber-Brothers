#!/usr/bin/env python
"""
Genera comandos de migración para Google Cloud Platform
"""
import os
import argparse

def generate_migration_commands(project_id, region, instance_name, db_user, db_pass, db_name, image_url):
    """Genera comandos para ejecutar migraciones en Cloud Run Jobs"""
    # Nombre completo de conexión
    instance_connection_name = f"{project_id}:{region}:{instance_name}"
    
    # Comando para crear un trabajo que ejecute las migraciones
    create_job_cmd = f'''gcloud run jobs create barberia-migrations \\
  --image={image_url} \\
  --set-env-vars="FLASK_APP=wsgi.py" \\
  --set-env-vars="DB_USER={db_user}" \\
  --set-env-vars="DB_PASS={db_pass}" \\
  --set-env-vars="DB_NAME={db_name}" \\
  --set-env-vars="DB_ENGINE=postgresql" \\
  --set-env-vars="GOOGLE_CLOUD_PROJECT={project_id}" \\
  --set-env-vars="REGION={region}" \\
  --set-env-vars="INSTANCE_NAME={instance_name}" \\
  --set-env-vars="INSTANCE_CONNECTION_NAME={instance_connection_name}" \\
  --command="/bin/bash" \\
  --args="-c","cd /app && python -m flask db upgrade" \\
  --region={region} \\
  --set-cloudsql-instances={instance_connection_name}'''
    
    # Comando para ejecutar el trabajo
    execute_job_cmd = f"gcloud run jobs execute barberia-migrations --region={region}"
    
    return create_job_cmd, execute_job_cmd

def main():
    parser = argparse.ArgumentParser(description='Genera comandos de migración para GCP')
    parser.add_argument('--project-id', required=True, help='ID del proyecto GCP')
    parser.add_argument('--region', default='us-east1', help='Región de GCP')
    parser.add_argument('--instance-name', default='barberia-db', help='Nombre de la instancia de Cloud SQL')
    parser.add_argument('--db-user', default='postgres', help='Usuario de la base de datos')
    parser.add_argument('--db-pass', required=True, help='Contraseña de la base de datos')
    parser.add_argument('--db-name', default='barberia-db', help='Nombre de la base de datos')
    parser.add_argument('--image-url', required=True, help='URL de la imagen del contenedor')
    
    args = parser.parse_args()
    
    create_job_cmd, execute_job_cmd = generate_migration_commands(
        args.project_id,
        args.region,
        args.instance_name,
        args.db_user,
        args.db_pass,
        args.db_name,
        args.image_url
    )
    
    print("\n=== Comando para crear el trabajo de migración ===")
    print(create_job_cmd)
    print("\n=== Comando para ejecutar el trabajo de migración ===")
    print(execute_job_cmd)
    print("\n=== Instrucciones ===")
    print("1. Ejecuta el primer comando para crear el trabajo de migración")
    print("2. Ejecuta el segundo comando para ejecutar las migraciones")
    print("3. Verifica los logs del trabajo para confirmar que las migraciones se han ejecutado correctamente")

if __name__ == "__main__":
    main()
