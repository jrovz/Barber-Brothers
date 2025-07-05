#!/usr/bin/env python3
"""
Script para limpiar imágenes huérfanas de sliders
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
        print("=== LIMPIEZA DE IMÁGENES HUÉRFANAS ===")
        print(f"UPLOAD_FOLDER: {current_app.config['UPLOAD_FOLDER']}")
        
        sliders_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'sliders')
        
        if not os.path.exists(sliders_path):
            print("❌ La carpeta sliders no existe")
            return
        
        # Obtener todas las imágenes usadas por los sliders
        sliders = Slider.query.filter(Slider.tipo == 'imagen', Slider.imagen_url.isnot(None)).all()
        imagenes_usadas = set()
        
        for slider in sliders:
            if slider.imagen_url:
                filename = slider.imagen_url.split('/')[-1]
                imagenes_usadas.add(filename)
        
        print(f"Imágenes en uso por sliders: {len(imagenes_usadas)}")
        print(f"Archivos: {list(imagenes_usadas)}")
        print()
        
        # Obtener todos los archivos en la carpeta
        archivos_en_carpeta = set()
        try:
            for archivo in os.listdir(sliders_path):
                if os.path.isfile(os.path.join(sliders_path, archivo)):
                    archivos_en_carpeta.add(archivo)
        except Exception as e:
            print(f"Error al listar archivos: {e}")
            return
        
        print(f"Archivos en carpeta: {len(archivos_en_carpeta)}")
        print(f"Archivos: {list(archivos_en_carpeta)}")
        print()
        
        # Encontrar archivos huérfanos
        huerfanos = archivos_en_carpeta - imagenes_usadas
        
        print(f"Archivos huérfanos encontrados: {len(huerfanos)}")
        
        if huerfanos:
            print("Archivos huérfanos:")
            for archivo in huerfanos:
                file_path = os.path.join(sliders_path, archivo)
                size = os.path.getsize(file_path)
                print(f"  - {archivo} ({size} bytes)")
            
            respuesta = input("\n¿Deseas eliminar estos archivos huérfanos? (s/N): ")
            
            if respuesta.lower() in ['s', 'si', 'sí', 'y', 'yes']:
                eliminados = 0
                for archivo in huerfanos:
                    try:
                        file_path = os.path.join(sliders_path, archivo)
                        os.remove(file_path)
                        eliminados += 1
                        print(f"✅ Eliminado: {archivo}")
                    except Exception as e:
                        print(f"❌ Error al eliminar {archivo}: {e}")
                
                print(f"\n🎉 Se eliminaron {eliminados} archivos huérfanos")
            else:
                print("Operación cancelada")
        else:
            print("✅ No se encontraron archivos huérfanos")
        
        print("\n=== FIN DE LA LIMPIEZA ===")

if __name__ == '__main__':
    main() 