#!/usr/bin/env python3
"""
Script para diagnosticar y verificar el estado de los sliders
"""
import os
import sys
from pathlib import Path

# Agregar la ruta del proyecto al path
sys.path.insert(0, os.path.abspath('.'))

from app import create_app, db
from app.models.slider import Slider
from flask import current_app

def main():
    app = create_app()
    
    with app.app_context():
        print("=== DIAGNÓSTICO DE SLIDERS ===")
        print(f"UPLOAD_FOLDER: {current_app.config['UPLOAD_FOLDER']}")
        print(f"Ruta completa de sliders: {os.path.join(current_app.config['UPLOAD_FOLDER'], 'sliders')}")
        print()
        
        # Verificar que la carpeta de sliders existe
        sliders_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'sliders')
        print(f"¿Existe la carpeta sliders?: {os.path.exists(sliders_path)}")
        
        if not os.path.exists(sliders_path):
            print("Creando carpeta sliders...")
            os.makedirs(sliders_path, exist_ok=True)
            print("✅ Carpeta creada")
        
        # Listar archivos en la carpeta
        if os.path.exists(sliders_path):
            archivos = os.listdir(sliders_path)
            print(f"Archivos en carpeta sliders: {archivos}")
        print()
        
        # Verificar sliders en la base de datos
        sliders = Slider.query.all()
        print(f"Total de sliders en BD: {len(sliders)}")
        print()
        
        for slider in sliders:
            print(f"--- Slider ID: {slider.id} ---")
            print(f"Título: {slider.titulo}")
            print(f"Tipo: {slider.tipo}")
            print(f"Imagen URL: {slider.imagen_url}")
            print(f"Activo: {slider.activo}")
            
            if slider.imagen_url and slider.tipo == 'imagen':
                filename = slider.imagen_url.split('/')[-1]
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'sliders', filename)
                existe = os.path.exists(file_path)
                print(f"Archivo existe: {existe}")
                print(f"Ruta del archivo: {file_path}")
                
                if existe:
                    size = os.path.getsize(file_path)
                    print(f"Tamaño: {size} bytes")
                else:
                    print("⚠️  ARCHIVO NO ENCONTRADO")
            
            print()
        
        print("=== FIN DEL DIAGNÓSTICO ===")

if __name__ == '__main__':
    main() 