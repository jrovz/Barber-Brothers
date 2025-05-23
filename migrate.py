#!/usr/bin/env python3
"""
Script mejorado para ejecutar migraciones de base de datos de manera segura

Este script:
1. Verifica conexión a la base de datos
2. Ejecuta las migraciones pendientes
3. Valida que las migraciones se hayan aplicado correctamente
4. Maneja errores con reintentos y rollback
"""

import os
import sys
import time
import logging
import argparse
from sqlalchemy.exc import SQLAlchemyError
from flask_migrate import Migrate, upgrade, downgrade, current
from app import create_app, db

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("migrations.log")
    ]
)
logger = logging.getLogger("migrations")

def check_db_connection(app):
    """Verifica la conexión a la base de datos"""
    max_retries = 5
    retry_delay = 3
    
    for attempt in range(1, max_retries + 1):
        try:
            with app.app_context():
                logger.info(f"Intento {attempt}/{max_retries} de conectar a la base de datos...")
                db.session.execute('SELECT 1')
                db.session.commit()
                logger.info("Conexión a la base de datos establecida correctamente")
                return True
        except Exception as e:
            logger.error(f"Error al conectar a la base de datos (intento {attempt}/{max_retries}): {e}")
            if attempt < max_retries:
                logger.info(f"Reintentando en {retry_delay} segundos...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Incrementar el tiempo de espera (backoff exponencial)
            else:
                logger.error("Se agotaron los intentos de conexión a la base de datos")
                return False

def run_migrations(app, target=None, dry_run=False):
    """Ejecuta las migraciones pendientes hasta la revisión objetivo"""
    try:
        with app.app_context():
            migrate = Migrate(app, db)
            
            # Obtener revisión actual
            current_rev = current()
            logger.info(f"Revisión actual de la base de datos: {current_rev}")
            
            if dry_run:
                logger.info("Modo simulación activado, no se aplicarán cambios")
                return True
            
            # Ejecutar las migraciones
            logger.info(f"Ejecutando migraciones hacia {'la última revisión' if target is None else target}...")
            upgrade(directory='migrations', revision=target)
            
            # Verificar que se aplicaron correctamente
            new_rev = current()
            logger.info(f"Nueva revisión de la base de datos: {new_rev}")
            
            if current_rev == new_rev and target is not None:
                logger.warning("No se aplicaron nuevas migraciones")
            
            return True
    except Exception as e:
        logger.error(f"Error al ejecutar migraciones: {e}")
        import traceback
        traceback.print_exc()
        return False

def rollback_migration(app, steps=1):
    """Revierte la última migración o el número de pasos especificado"""
    try:
        with app.app_context():
            migrate = Migrate(app, db)
            
            # Obtener revisión actual
            current_rev = current()
            logger.info(f"Ejecutando rollback desde la revisión: {current_rev}")
            
            # Revertir la migración
            downgrade(directory='migrations', revision=f"-{steps}")
            
            # Verificar que se revirtió correctamente
            new_rev = current()
            logger.info(f"Rollback completado. Nueva revisión: {new_rev}")
            
            return True
    except Exception as e:
        logger.error(f"Error al revertir migración: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description="Ejecuta migraciones de base de datos de manera segura")
    parser.add_argument("--env", default="production", choices=["development", "production", "testing"],
                        help="Entorno de ejecución (default: production)")
    parser.add_argument("--target", help="Revisión objetivo (opcional)")
    parser.add_argument("--dry-run", action="store_true", help="Simulación sin aplicar cambios")
    parser.add_argument("--rollback", action="store_true", help="Revertir la última migración")
    parser.add_argument("--steps", type=int, default=1, help="Número de pasos para el rollback")
    args = parser.parse_args()
    
    logger.info(f"Iniciando script de migraciones en entorno: {args.env}")
    
    # Crear la aplicación con el entorno adecuado
    app = create_app(args.env)
    
    # Verificar conexión a la base de datos
    if not check_db_connection(app):
        logger.error("No se pudo conectar a la base de datos. Abortando migraciones.")
        sys.exit(1)
    
    # Ejecutar operación solicitada
    if args.rollback:
        logger.info(f"Modo rollback activado. Se revertirán {args.steps} migraciones.")
        success = rollback_migration(app, args.steps)
    else:
        success = run_migrations(app, args.target, args.dry_run)
    
    if success:
        logger.info("Operación completada exitosamente")
        sys.exit(0)
    else:
        logger.error("La operación falló")
        sys.exit(1)

if __name__ == "__main__":
    main()