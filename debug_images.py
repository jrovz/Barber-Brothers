import os
import sys
from flask import Flask

# Configurar aplicación Flask para contexto
from app import create_app
app = create_app()

# Importar modelos
from app.models import Barbero, Producto, Servicio

def check_image_paths():
    """Verificar rutas de imágenes en la base de datos y sistema de archivos"""
    print("\n=== DIAGNÓSTICO DE RUTAS DE IMÁGENES ===\n")

    # Verificar imágenes de barberos
    print("\n--- BARBEROS ---")
    barberos = Barbero.query.all()
    for barbero in barberos:
        print(f"\nBarbero ID: {barbero.id} - {barbero.nombre}")
        
        # Verificar URL en la base de datos
        print(f"URL en base de datos: '{barbero.imagen_url}'")
        
        if not barbero.imagen_url:
            print("❌ No hay URL de imagen guardada")
            continue
            
        # Construir ruta del sistema a partir de la URL
        if barbero.imagen_url.startswith('/static/'):
            # Quitar "/static/" y obtener ruta relativa
            rel_path = barbero.imagen_url.replace('/static/', '')
            # Construir ruta absoluta
            abs_path = os.path.join(app.root_path, 'static', rel_path)
            
            print(f"Ruta del sistema: '{abs_path}'")
            
            # Verificar si el archivo existe
            if os.path.exists(abs_path):
                print(f"✅ Archivo existe físicamente")
                # Verificar permisos
                if os.access(abs_path, os.R_OK):
                    print("✅ Archivo tiene permisos de lectura")
                else:
                    print("❌ Archivo no tiene permisos de lectura")
            else:
                print(f"❌ Archivo NO existe físicamente")
        else:
            print(f"⚠️ URL no comienza con '/static/' - posible URL externa")
    
    # Repetir para productos y servicios
    # (Código similar para Producto y Servicio)

if __name__ == "__main__":
    with app.app_context():
        check_image_paths()