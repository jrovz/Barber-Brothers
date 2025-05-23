#!/usr/bin/env python3
"""
Script para validar la configuración de Cloud Run y diagnosticar problemas comunes
"""

import os
import sys
import logging
import requests
import subprocess
import json
import platform
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("cloud_run_diagnosis.log")
    ]
)
logger = logging.getLogger("cloud_run_diagnosis")

def check_gcloud_installation():
    """Verifica que gcloud esté instalado y configurado"""
    try:
        logger.info("Verificando instalación de gcloud...")
        result = subprocess.run(["gcloud", "version"], capture_output=True, text=True)
        if result.returncode != 0:
            logger.error("gcloud no está instalado o no se encuentra en el PATH")
            return False
        
        logger.info("gcloud está instalado correctamente")
        
        # Verificar autenticación
        result = subprocess.run(["gcloud", "auth", "list"], capture_output=True, text=True)
        if "No credentialed accounts." in result.stdout:
            logger.error("No hay cuentas autenticadas en gcloud")
            return False
        
        logger.info("gcloud está autenticado correctamente")
        return True
    except Exception as e:
        logger.error(f"Error verificando gcloud: {e}")
        return False

def check_cloud_run_service(service_name="barberia-app", region="us-central1"):
    """Verifica el estado del servicio Cloud Run"""
    try:
        logger.info(f"Verificando servicio Cloud Run: {service_name}...")
        result = subprocess.run(
            ["gcloud", "run", "services", "describe", service_name, "--region", region, "--format=json"],
            capture_output=True, text=True
        )
        
        if result.returncode != 0:
            logger.error(f"Error al obtener información del servicio Cloud Run: {result.stderr}")
            return False
        
        # Analizar el resultado JSON
        service_info = json.loads(result.stdout)
        
        # Información básica
        logger.info(f"Nombre del servicio: {service_info.get('metadata', {}).get('name')}")
        logger.info(f"URL del servicio: {service_info.get('status', {}).get('url')}")
        logger.info(f"Región: {service_info.get('metadata', {}).get('labels', {}).get('cloud.googleapis.com/location')}")
        
        # Revisar recursos asignados
        cpu = service_info.get('template', {}).get('spec', {}).get('containers', [{}])[0].get('resources', {}).get('limits', {}).get('cpu')
        memory = service_info.get('template', {}).get('spec', {}).get('containers', [{}])[0].get('resources', {}).get('limits', {}).get('memory')
        logger.info(f"CPU asignada: {cpu}")
        logger.info(f"Memoria asignada: {memory}")
        
        # Revisar autoscaling
        min_instances = service_info.get('template', {}).get('spec', {}).get('containerConcurrency')
        max_instances = service_info.get('template', {}).get('metadata', {}).get('annotations', {}).get('autoscaling.knative.dev/maxScale')
        logger.info(f"Concurrencia por instancia: {min_instances}")
        logger.info(f"Máximo de instancias: {max_instances}")
        
        # Revisar variables de entorno
        env_vars = service_info.get('template', {}).get('spec', {}).get('containers', [{}])[0].get('env', [])
        logger.info("Variables de entorno configuradas:")
        for env in env_vars:
            name = env.get('name')
            if name in ['DB_PASS', 'DATABASE_URL', 'SECRET_KEY']:
                logger.info(f"  {name}: ***VALOR SECRETO***")
            else:
                value = env.get('value', '***NO VALOR EXPLÍCITO***')
                logger.info(f"  {name}: {value}")
        
        # Revisar conexiones a Cloud SQL
        cloud_sql = service_info.get('template', {}).get('metadata', {}).get('annotations', {}).get('run.googleapis.com/cloudsql-instances')
        if cloud_sql:
            logger.info(f"Instancias Cloud SQL conectadas: {cloud_sql}")
        else:
            logger.warning("No hay instancias de Cloud SQL conectadas")
        
        # Revisar estado general
        conditions = service_info.get('status', {}).get('conditions', [])
        for condition in conditions:
            if condition.get('type') == 'Ready':
                if condition.get('status') == 'True':
                    logger.info("El servicio está LISTO y disponible")
                else:
                    logger.error(f"El servicio NO está listo: {condition.get('message')}")
        
        return True
    except Exception as e:
        logger.error(f"Error verificando servicio Cloud Run: {e}")
        return False

def check_cloud_sql_instance(instance_name="barberia-db", region="us-central1"):
    """Verifica el estado de la instancia de Cloud SQL"""
    try:
        logger.info(f"Verificando instancia Cloud SQL: {instance_name}...")
        result = subprocess.run(
            ["gcloud", "sql", "instances", "describe", instance_name, "--format=json"],
            capture_output=True, text=True
        )
        
        if result.returncode != 0:
            logger.error(f"Error al obtener información de la instancia Cloud SQL: {result.stderr}")
            return False
        
        # Analizar el resultado JSON
        instance_info = json.loads(result.stdout)
        
        # Información básica
        logger.info(f"Nombre de la instancia: {instance_info.get('name')}")
        logger.info(f"Versión: {instance_info.get('databaseVersion')}")
        logger.info(f"Región: {instance_info.get('region')}")
        logger.info(f"Estado: {instance_info.get('state')}")
        
        # Revisar configuración de red
        settings = instance_info.get('settings', {})
        ip_config = settings.get('ipConfiguration', {})
        authorized_networks = ip_config.get('authorizedNetworks', [])
        
        if ip_config.get('privateNetwork'):
            logger.info(f"Red privada: {ip_config.get('privateNetwork')}")
        
        if authorized_networks:
            logger.info("Redes autorizadas:")
            for network in authorized_networks:
                logger.info(f"  {network.get('name')}: {network.get('value')}")
        else:
            logger.info("No hay redes autorizadas configuradas")
        
        # Revisar conexión pública
        if ip_config.get('ipv4Enabled'):
            logger.info("La instancia tiene IP pública habilitada")
        else:
            logger.info("La instancia no tiene IP pública habilitada")
        
        return True
    except Exception as e:
        logger.error(f"Error verificando instancia Cloud SQL: {e}")
        return False

def check_cloud_storage_bucket(bucket_name="barberia-uploads"):
    """Verifica el estado del bucket de Cloud Storage"""
    try:
        logger.info(f"Verificando bucket de Cloud Storage: {bucket_name}...")
        result = subprocess.run(
            ["gcloud", "storage", "buckets", "describe", f"gs://{bucket_name}", "--format=json"],
            capture_output=True, text=True
        )
        
        if result.returncode != 0:
            logger.error(f"Error al obtener información del bucket: {result.stderr}")
            return False
        
        # Analizar el resultado JSON
        bucket_info = json.loads(result.stdout)
        
        # Información básica
        logger.info(f"Nombre del bucket: {bucket_info.get('name')}")
        logger.info(f"Ubicación: {bucket_info.get('location')}")
        logger.info(f"Clase de almacenamiento: {bucket_info.get('storageClass')}")
        
        # Verificar permisos públicos
        result = subprocess.run(
            ["gcloud", "storage", "buckets", "get-iam-policy", f"gs://{bucket_name}", "--format=json"],
            capture_output=True, text=True
        )
        
        if result.returncode != 0:
            logger.error(f"Error al obtener política IAM del bucket: {result.stderr}")
            return False
        
        # Analizar el resultado JSON
        iam_policy = json.loads(result.stdout)
        
        has_public_access = False
        for binding in iam_policy.get('bindings', []):
            if 'allUsers' in binding.get('members', []):
                has_public_access = True
                logger.info(f"El bucket tiene acceso público para el rol: {binding.get('role')}")
        
        if not has_public_access:
            logger.warning("El bucket no tiene configurado acceso público. Los archivos subidos pueden no ser accesibles públicamente.")
        
        return True
    except Exception as e:
        logger.error(f"Error verificando bucket de Cloud Storage: {e}")
        return False

def main():
    """Función principal"""
    logger.info("=== Iniciando diagnóstico de Cloud Run para Barber Brothers ===")
    logger.info(f"Fecha y hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Sistema operativo: {platform.system()} {platform.release()}")
    
    # Verificar herramientas
    if not check_gcloud_installation():
        logger.error("Es necesario instalar y configurar gcloud para continuar")
        sys.exit(1)
    
    # Verificar servicios
    check_cloud_run_service()
    check_cloud_sql_instance()
    check_cloud_storage_bucket()
    
    logger.info("=== Diagnóstico completado ===")
    logger.info("Consulta 'cloud_run_diagnosis.log' para ver el resultado completo")

if __name__ == "__main__":
    main()
