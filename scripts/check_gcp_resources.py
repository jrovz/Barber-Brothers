#!/usr/bin/env python3
"""
Verificación de Recursos GCP para Barber Brothers

Este script verifica que todos los recursos necesarios para el proyecto
estén creados correctamente en GCP. Sirve como una lista de verificación
para asegurar que la implementación esté completa.
"""

import os
import sys
import json
import logging
import subprocess
import argparse
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("gcp_resources_check.log")
    ]
)
logger = logging.getLogger("gcp_resources")

# Constantes
DEFAULT_PROJECT_ID = "barber-brothers-460514"
DEFAULT_REGION = "us-central1"

def run_gcloud_command(cmd, ignore_errors=False):
    """Ejecuta un comando gcloud y devuelve el resultado"""
    try:
        logger.debug(f"Ejecutando comando: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0 and not ignore_errors:
            logger.error(f"Error ejecutando comando: {result.stderr}")
            return None
        
        return result.stdout.strip()
    except Exception as e:
        logger.error(f"Excepción ejecutando comando: {e}")
        return None

def check_cloud_run(project_id, region):
    """Verifica servicios Cloud Run"""
    logger.info("Verificando servicios Cloud Run...")
    
    cmd = ["gcloud", "run", "services", "list", "--platform", "managed", 
           "--region", region, "--project", project_id, "--format=json"]
    output = run_gcloud_command(cmd)
    
    if not output:
        logger.error("❌ No se pudo obtener la lista de servicios Cloud Run")
        return False
    
    try:
        services = json.loads(output)
        
        if not services:
            logger.warning("⚠️ No hay servicios Cloud Run desplegados en la región")
            return False
        
        logger.info(f"Se encontraron {len(services)} servicios Cloud Run")
        
        barberia_service = None
        for service in services:
            name = service.get('metadata', {}).get('name', '')
            logger.info(f"Servicio: {name}")
            
            if name == "barberia-app":
                barberia_service = service
                logger.info("✅ Servicio 'barberia-app' encontrado")
        
        if not barberia_service:
            logger.warning("⚠️ Servicio 'barberia-app' no encontrado")
            return False
        
        # Verificar configuración del servicio
        url = barberia_service.get('status', {}).get('url')
        logger.info(f"URL del servicio: {url}")
        
        vpc_connector = barberia_service.get('spec', {}).get('template', {}).get('metadata', {}).get('annotations', {}).get('run.googleapis.com/vpc-access-connector')
        if vpc_connector:
            logger.info(f"✅ VPC Connector configurado: {vpc_connector}")
        else:
            logger.warning("⚠️ No hay VPC Connector configurado")
        
        cloud_sql = barberia_service.get('spec', {}).get('template', {}).get('metadata', {}).get('annotations', {}).get('run.googleapis.com/cloudsql-instances')
        if cloud_sql:
            logger.info(f"✅ Instancia Cloud SQL conectada: {cloud_sql}")
        else:
            logger.warning("⚠️ No hay instancia Cloud SQL conectada")
        
        # Verificar configuración de escalado
        min_instances = barberia_service.get('spec', {}).get('template', {}).get('metadata', {}).get('annotations', {}).get('autoscaling.knative.dev/minScale')
        max_instances = barberia_service.get('spec', {}).get('template', {}).get('metadata', {}).get('annotations', {}).get('autoscaling.knative.dev/maxScale')
        
        logger.info(f"Instancias mínimas: {min_instances or '0'}")
        logger.info(f"Instancias máximas: {max_instances or 'ilimitado'}")
        
        return True
    except Exception as e:
        logger.error(f"Error analizando servicios Cloud Run: {e}")
        return False

def check_cloud_sql(project_id):
    """Verifica instancias Cloud SQL"""
    logger.info("Verificando instancias Cloud SQL...")
    
    cmd = ["gcloud", "sql", "instances", "list", 
           "--project", project_id, "--format=json"]
    output = run_gcloud_command(cmd)
    
    if not output:
        logger.error("❌ No se pudo obtener la lista de instancias Cloud SQL")
        return False
    
    try:
        instances = json.loads(output)
        
        if not instances:
            logger.warning("⚠️ No hay instancias Cloud SQL creadas")
            return False
        
        logger.info(f"Se encontraron {len(instances)} instancias Cloud SQL")
        
        barberia_db = None
        for instance in instances:
            name = instance.get('name', '')
            logger.info(f"Instancia: {name}")
            
            if name == "barberia-db":
                barberia_db = instance
                logger.info("✅ Instancia 'barberia-db' encontrada")
        
        if not barberia_db:
            logger.warning("⚠️ Instancia 'barberia-db' no encontrada")
            return False
        
        # Verificar configuración de la instancia
        state = barberia_db.get('state')
        logger.info(f"Estado: {state}")
        
        if state != "RUNNABLE":
            logger.warning(f"⚠️ La instancia está en estado {state}, no en RUNNABLE")
        
        db_version = barberia_db.get('databaseVersion')
        logger.info(f"Versión de base de datos: {db_version}")
        
        return True
    except Exception as e:
        logger.error(f"Error analizando instancias Cloud SQL: {e}")
        return False

def check_cloud_storage(project_id):
    """Verifica buckets de Cloud Storage"""
    logger.info("Verificando buckets de Cloud Storage...")
    
    cmd = ["gcloud", "storage", "ls", "--project", project_id, "--format=json"]
    output = run_gcloud_command(cmd)
    
    if not output:
        logger.error("❌ No se pudo obtener la lista de buckets")
        return False
    
    try:
        buckets = json.loads(output)
        
        if not buckets:
            logger.warning("⚠️ No hay buckets de Storage creados")
            return False
        
        logger.info(f"Se encontraron {len(buckets)} buckets")
        
        barberia_bucket = None
        for bucket in buckets:
            name = bucket.get('name', '')
            logger.info(f"Bucket: {name}")
            
            if name.endswith('barberia-uploads') or name.endswith('/barberia-uploads/'):
                bucket_name = name.rstrip('/')
                barberia_bucket = bucket
                logger.info(f"✅ Bucket 'barberia-uploads' encontrado: {bucket_name}")
        
        if not barberia_bucket:
            logger.warning("⚠️ Bucket 'barberia-uploads' no encontrado")
            return False
        
        # Verificar acceso público
        cmd_iam = ["gcloud", "storage", "buckets", "get-iam-policy", "gs://barberia-uploads", 
                 "--project", project_id, "--format=json"]
        iam_output = run_gcloud_command(cmd_iam)
        
        if iam_output:
            try:
                iam_policy = json.loads(iam_output)
                bindings = iam_policy.get('bindings', [])
                public_access = False
                
                for binding in bindings:
                    if 'allUsers' in binding.get('members', []):
                        public_access = True
                        logger.info(f"✅ Acceso público configurado con rol: {binding.get('role')}")
                
                if not public_access:
                    logger.warning("⚠️ El bucket no tiene acceso público configurado")
            except Exception as e:
                logger.error(f"Error analizando política IAM: {e}")
        
        return True
    except Exception as e:
        logger.error(f"Error analizando buckets: {e}")
        return False

def check_secrets(project_id):
    """Verifica secretos en Secret Manager"""
    logger.info("Verificando secretos en Secret Manager...")
    
    cmd = ["gcloud", "secrets", "list", "--project", project_id, "--format=json"]
    output = run_gcloud_command(cmd)
    
    if not output:
        logger.error("❌ No se pudo obtener la lista de secretos")
        return False
    
    try:
        secrets = json.loads(output)
        
        if not secrets:
            logger.warning("⚠️ No hay secretos configurados")
            return False
        
        logger.info(f"Se encontraron {len(secrets)} secretos")
        
        # Lista de secretos esperados
        expected_secrets = [
            "secret_key", "db_user", "db_pass", "db_name",
            "mail_server", "mail_port", "mail_use_tls", 
            "mail_username", "mail_password", "mail_sender"
        ]
        
        found_secrets = set()
        for secret in secrets:
            name = secret.get('name', '').split('/')[-1]  # Extraer solo el nombre del secret
            logger.info(f"Secreto: {name}")
            found_secrets.add(name)
        
        # Verificar secretos faltantes
        missing_secrets = [s for s in expected_secrets if s not in found_secrets]
        
        if missing_secrets:
            logger.warning(f"⚠️ Secretos faltantes: {', '.join(missing_secrets)}")
        else:
            logger.info("✅ Todos los secretos esperados están configurados")
        
        return len(missing_secrets) == 0
    except Exception as e:
        logger.error(f"Error analizando secretos: {e}")
        return False

def check_vpc_connector(project_id, region):
    """Verifica VPC Connector"""
    logger.info("Verificando VPC Connector...")
    
    cmd = ["gcloud", "compute", "networks", "vpc-access", "connectors", "list", 
           "--region", region, "--project", project_id, "--format=json"]
    output = run_gcloud_command(cmd)
    
    if not output:
        logger.error("❌ No se pudo obtener la lista de VPC Connectors")
        return False
    
    try:
        connectors = json.loads(output)
        
        if not connectors:
            logger.warning("⚠️ No hay VPC Connectors configurados")
            return False
        
        logger.info(f"Se encontraron {len(connectors)} VPC Connectors")
        
        barberia_connector = None
        for connector in connectors:
            name = connector.get('name', '').split('/')[-1]  # Extraer solo el nombre
            logger.info(f"Connector: {name}")
            
            if name == "barberia-vpc-connector":
                barberia_connector = connector
                logger.info("✅ VPC Connector 'barberia-vpc-connector' encontrado")
        
        if not barberia_connector:
            logger.warning("⚠️ VPC Connector 'barberia-vpc-connector' no encontrado")
            return False
        
        # Verificar estado del connector
        state = barberia_connector.get('state')
        logger.info(f"Estado: {state}")
        
        if state != "READY":
            logger.warning(f"⚠️ El VPC Connector está en estado {state}, no en READY")
        
        return True
    except Exception as e:
        logger.error(f"Error analizando VPC Connectors: {e}")
        return False

def check_cloud_build(project_id):
    """Verifica configuración de Cloud Build"""
    logger.info("Verificando configuración de Cloud Build...")
    
    cmd = ["gcloud", "builds", "triggers", "list", 
           "--project", project_id, "--format=json"]
    output = run_gcloud_command(cmd)
    
    if not output:
        logger.error("❌ No se pudo obtener la lista de triggers de Cloud Build")
        return False
    
    try:
        triggers = json.loads(output)
        
        if not triggers:
            logger.warning("⚠️ No hay triggers de Cloud Build configurados")
            return False
        
        logger.info(f"Se encontraron {len(triggers)} triggers de Cloud Build")
        
        barberia_trigger = None
        for trigger in triggers:
            name = trigger.get('name')
            description = trigger.get('description', '')
            logger.info(f"Trigger: {name} - {description}")
            
            if "barberia" in name.lower() or "barber" in name.lower() or "deploy-barberia" in name.lower():
                barberia_trigger = trigger
                logger.info(f"✅ Trigger para Barber Brothers encontrado: {name}")
        
        if not barberia_trigger:
            logger.warning("⚠️ No se encontró un trigger específico para Barber Brothers")
            return False
        
        # Verificar detalles del trigger
        source = barberia_trigger.get('github', {}).get('name')
        if source:
            logger.info(f"Repositorio GitHub: {source}")
        
        branch = barberia_trigger.get('github', {}).get('push', {}).get('branch')
        if branch:
            logger.info(f"Rama: {branch}")
        
        return True
    except Exception as e:
        logger.error(f"Error analizando triggers de Cloud Build: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Verificación de recursos GCP para Barber Brothers")
    parser.add_argument("--project-id", default=DEFAULT_PROJECT_ID, 
                      help=f"ID del proyecto GCP (default: {DEFAULT_PROJECT_ID})")
    parser.add_argument("--region", default=DEFAULT_REGION, 
                      help=f"Región de GCP (default: {DEFAULT_REGION})")
    parser.add_argument("--verbose", "-v", action="store_true", 
                      help="Mostrar información detallada")
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    logger.info("=" * 60)
    logger.info(f"Verificación de recursos GCP: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Proyecto: {args.project_id}, Región: {args.region}")
    logger.info("=" * 60)
    
    # Ejecutar todas las verificaciones
    cloud_run_ok = check_cloud_run(args.project_id, args.region)
    cloud_sql_ok = check_cloud_sql(args.project_id)
    storage_ok = check_cloud_storage(args.project_id)
    secrets_ok = check_secrets(args.project_id)
    vpc_ok = check_vpc_connector(args.project_id, args.region)
    build_ok = check_cloud_build(args.project_id)
    
    # Resumen final
    logger.info("=" * 60)
    logger.info("RESUMEN DE VERIFICACIÓN DE RECURSOS")
    logger.info("=" * 60)
    logger.info(f"Cloud Run:        {'✅ OK' if cloud_run_ok else '❌ Verificar'}")
    logger.info(f"Cloud SQL:        {'✅ OK' if cloud_sql_ok else '❌ Verificar'}")
    logger.info(f"Cloud Storage:    {'✅ OK' if storage_ok else '❌ Verificar'}")
    logger.info(f"Secret Manager:   {'✅ OK' if secrets_ok else '❌ Verificar'}")
    logger.info(f"VPC Connector:    {'✅ OK' if vpc_ok else '❌ Verificar'}")
    logger.info(f"Cloud Build:      {'✅ OK' if build_ok else '❌ Verificar'}")
    
    # Estado general
    all_ok = all([cloud_run_ok, cloud_sql_ok, storage_ok, secrets_ok, vpc_ok, build_ok])
    logger.info("=" * 60)
    if all_ok:
        logger.info("✅ TODOS LOS RECURSOS ESTÁN CORRECTAMENTE CONFIGURADOS")
        sys.exit(0)
    else:
        logger.warning("⚠️ HAY RECURSOS QUE REQUIEREN ATENCIÓN")
        sys.exit(1)

if __name__ == "__main__":
    main()
