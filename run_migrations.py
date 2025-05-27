#!/usr/bin/env python
"""
Script para ejecutar migraciones de base de datos
"""
import os
import sys
import logging
from flask import Flask
from flask.cli import FlaskGroup
from flask_migrate import upgrade

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_migrations():
    """Ejecutar migraciones de base de datos"""
    try:
        # Importar la aplicación
        from wsgi import app
        
        logger.info("Iniciando migraciones de base de datos...")
        
        with app.app_context():
            # Ejecutar migraciones
            upgrade()
            
        logger.info("Migraciones completadas exitosamente.")
        return True
    except Exception as e:
        logger.error(f"Error al ejecutar migraciones: {e}")
        return False

if __name__ == "__main__":
    # Ejecutar migraciones
    success = run_migrations()
    
    # Salir con código apropiado
    if success:
        sys.exit(0)
    else:
        sys.exit(1)
