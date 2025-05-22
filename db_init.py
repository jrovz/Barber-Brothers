#!/usr/bin/env python3
from app import create_app, db
from flask_migrate import upgrade
import os
import sys

def init_db():
    """
    Inicializa la base de datos ejecutando las migraciones.
    """
    print("Iniciando configuración de la base de datos...")
    
    app = create_app()
    with app.app_context():
        print("Aplicando las migraciones...")
        try:
            # Usar Flask-Migrate para aplicar las migraciones
            upgrade()
            print("Migraciones aplicadas con éxito.")
            
            # Verificar si las tablas existen
            tables = db.engine.table_names()
            print(f"Tablas existentes en la base de datos: {tables}")
            
            # Si la tabla 'productos' existe pero no tiene datos, importamos datos iniciales
            if 'producto' in tables:
                from app.models import Producto
                if not Producto.query.first():
                    print("Importando datos iniciales...")
                    try:
                        from init_data import import_initial_data
                        import_initial_data()
                        print("Datos iniciales importados con éxito.")
                    except Exception as e:
                        print(f"Error al importar datos iniciales: {e}")
            else:
                print("La tabla 'producto' no existe. Revisa las migraciones.")
                
            return True
        except Exception as e:
            print(f"Error al aplicar migraciones: {e}")
            return False

if __name__ == "__main__":
    success = init_db()
    sys.exit(0 if success else 1)
