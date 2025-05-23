#!/usr/bin/env python3
"""
Health Check Script para el servicio de Barber Brothers
Este script verifica el estado de salud del servicio en Cloud Run,
la base de datos, y otros componentes críticos.
"""

import os
import sys
import json
import logging
import argparse
import requests
from datetime import datetime
import subprocess
import time

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("health_check.log")
    ]
)
logger = logging.getLogger("health_check")

# Configuración por defecto
DEFAULT_SERVICE_URL = "https://barberia-app-fofqkxmmkq-uc.a.run.app"
DEFAULT_REGION = "us-central1"
DEFAULT_PROJECT_ID = "barber-brothers-460514"

def check_service_health(service_url):
    """Verifica si el servicio web está respondiendo correctamente"""
    try:
        logger.info(f"Verificando estado del servicio en: {service_url}")
        start_time = time.time()
        response = requests.get(f"{service_url}/api/health", timeout=10)
        elapsed_time = time.time() - start_time
        
        logger.info(f"Tiempo de respuesta: {elapsed_time:.2f} segundos")
        logger.info(f"Código de estado: {response.status_code}")
        
        if response.status_code == 200:
            try:
                health_data = response.json()
                logger.info(f"Estado del servicio: {health_data.get('status', 'Desconocido')}")
                logger.info(f"Estado de base de datos: {health_data.get('database', 'Desconocido')}")
                logger.info(f"Estado de almacenamiento: {health_data.get('storage', 'Desconocido')}")
                
                # Verificar todos los componentes
                all_healthy = all([
                    health_data.get('status') == 'ok',
                    health_data.get('database') == 'connected',
                    health_data.get('storage') == 'available'
                ])
                
                if all_healthy:
                    logger.info("✅ Todos los componentes están funcionando correctamente")
                    return True
                else:
                    logger.warning("⚠️ Uno o más componentes tienen problemas")
                    return False
            except json.JSONDecodeError:
                logger.error("❌ Respuesta no es un JSON válido")
                return False
        else:
            logger.error(f"❌ Servicio respondió con código de error: {response.status_code}")
            return False
    except requests.RequestException as e:
        logger.error(f"❌ Error al conectar con el servicio: {e}")
        return False

def check_cloud_run_service(service_name="barberia-app", region=DEFAULT_REGION, project_id=DEFAULT_PROJECT_ID):
    """Verifica el estado del servicio en Cloud Run usando gcloud"""
    try:
        logger.info(f"Verificando estado de servicio Cloud Run: {service_name}")
        result = subprocess.run(
            ["gcloud", "run", "services", "describe", service_name, 
             "--region", region, "--project", project_id, "--format=json"],
            capture_output=True, text=True
        )
        
        if result.returncode != 0:
            logger.error(f"❌ Error consultando servicio Cloud Run: {result.stderr}")
            return False
        
        service_info = json.loads(result.stdout)
        
        # Verificar que el servicio esté listo
        ready = False
        for condition in service_info.get('status', {}).get('conditions', []):
            if condition.get('type') == 'Ready':
                ready = condition.get('status') == 'True'
                if ready:
                    logger.info("✅ Servicio Cloud Run está listo")
                else:
                    logger.error(f"❌ Servicio Cloud Run no está listo: {condition.get('message')}")
        
        # Obtener URL del servicio
        service_url = service_info.get('status', {}).get('url')
        logger.info(f"URL del servicio: {service_url}")
        
        # Obtener métricas de tráfico
        traffic = service_info.get('status', {}).get('traffic', [])
        for route in traffic:
            logger.info(f"Revisión: {route.get('revisionName')}, Tráfico: {route.get('percent')}%")
        
        # Obtener información de revisión actual
        current_revision = service_info.get('status', {}).get('latestReadyRevisionName')
        logger.info(f"Revisión actual: {current_revision}")
        
        return ready, service_url
    except Exception as e:
        logger.error(f"❌ Error verificando servicio Cloud Run: {e}")
        return False, None

def check_cloud_sql(instance_name="barberia-db", project_id=DEFAULT_PROJECT_ID):
    """Verifica el estado de la instancia Cloud SQL"""
    try:
        logger.info(f"Verificando estado de instancia Cloud SQL: {instance_name}")
        result = subprocess.run(
            ["gcloud", "sql", "instances", "describe", instance_name, 
             "--project", project_id, "--format=json"],
            capture_output=True, text=True
        )
        
        if result.returncode != 0:
            logger.error(f"❌ Error consultando instancia Cloud SQL: {result.stderr}")
            return False
        
        instance_info = json.loads(result.stdout)
        
        # Verificar estado de la instancia
        state = instance_info.get('state')
        logger.info(f"Estado de instancia Cloud SQL: {state}")
        
        if state == 'RUNNABLE':
            logger.info("✅ Instancia Cloud SQL está operativa")
            return True
        else:
            logger.error(f"❌ Instancia Cloud SQL no está operativa (estado: {state})")
            return False
    except Exception as e:
        logger.error(f"❌ Error verificando instancia Cloud SQL: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Verificador de salud para Barber Brothers")
    parser.add_argument("--service-url", default=DEFAULT_SERVICE_URL, 
                      help=f"URL del servicio (default: {DEFAULT_SERVICE_URL})")
    parser.add_argument("--service-name", default="barberia-app", 
                      help="Nombre del servicio Cloud Run (default: barberia-app)")
    parser.add_argument("--region", default=DEFAULT_REGION, 
                      help=f"Región de GCP (default: {DEFAULT_REGION})")
    parser.add_argument("--project-id", default=DEFAULT_PROJECT_ID, 
                      help=f"ID del proyecto GCP (default: {DEFAULT_PROJECT_ID})")
    parser.add_argument("--db-instance", default="barberia-db", 
                      help="Nombre de la instancia Cloud SQL (default: barberia-db)")
    parser.add_argument("--verbose", "-v", action="store_true", 
                      help="Mostrar información detallada")
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    logger.info("=" * 60)
    logger.info(f"Iniciando verificación de salud: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    
    # Verificar servicio Cloud Run
    cloud_run_status, service_url = check_cloud_run_service(
        args.service_name, args.region, args.project_id
    )
    
    # Usar service_url de Cloud Run si está disponible, sino usar la proporcionada
    service_url = service_url or args.service_url
    
    # Verificar estado del servicio web
    service_health = check_service_health(service_url)
    
    # Verificar instancia Cloud SQL
    db_status = check_cloud_sql(args.db_instance, args.project_id)
    
    # Resumen final
    logger.info("=" * 60)
    logger.info("RESUMEN DE SALUD DEL SISTEMA")
    logger.info("=" * 60)
    logger.info(f"Servicio Cloud Run: {'✅ Operativo' if cloud_run_status else '❌ Con problemas'}")
    logger.info(f"Aplicación Web:      {'✅ Operativa' if service_health else '❌ Con problemas'}")
    logger.info(f"Base de Datos:       {'✅ Operativa' if db_status else '❌ Con problemas'}")
    
    # Estado general
    all_healthy = all([cloud_run_status, service_health, db_status])
    logger.info("=" * 60)
    if all_healthy:
        logger.info("✅ SISTEMA COMPLETAMENTE OPERATIVO")
        sys.exit(0)
    else:
        logger.error("❌ UNO O MÁS COMPONENTES PRESENTAN PROBLEMAS")
        sys.exit(1)

if __name__ == "__main__":
    main()
