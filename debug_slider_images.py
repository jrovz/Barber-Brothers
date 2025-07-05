#!/usr/bin/env python3
"""
Script de debug exhaustivo para el sistema de imágenes de sliders
Inspecciona todo el proceso desde el guardado hasta el acceso web
"""

import os
import sys
import psycopg2
from urllib.parse import urlparse
from pathlib import Path
import requests

def test_database_connection():
    """Probar conexión a la base de datos y revisar sliders"""
    print("=== VERIFICANDO CONEXIÓN A BASE DE DATOS ===")
    
    try:
        # Obtener configuración de la base de datos
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            print("❌ No se encontró DATABASE_URL en variables de entorno")
            return False
            
        print(f"🔗 DATABASE_URL encontrada: {database_url[:50]}...")
        
        # Conectar a la base de datos
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Verificar si existe la tabla sliders
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'sliders'
            );
        """)
        
        table_exists = cursor.fetchone()[0]
        if not table_exists:
            print("❌ La tabla 'sliders' no existe en la base de datos")
            return False
            
        print("✅ Tabla 'sliders' existe")
        
        # Obtener todos los sliders con imágenes
        cursor.execute("""
            SELECT id, titulo, tipo, imagen_url, activo, fecha_creacion 
            FROM sliders 
            WHERE tipo = 'imagen' AND imagen_url IS NOT NULL
        """)
        
        sliders = cursor.fetchall()
        print(f"📊 Se encontraron {len(sliders)} sliders con imágenes")
        
        for slider in sliders:
            slider_id, titulo, tipo, imagen_url, activo, fecha = slider
            print(f"  ID: {slider_id}")
            print(f"  Título: {titulo}")
            print(f"  URL en DB: {imagen_url}")
            print(f"  Activo: {activo}")
            print(f"  Fecha: {fecha}")
            print("  " + "-"*50)
            
        cursor.close()
        conn.close()
        
        return sliders
        
    except Exception as e:
        print(f"❌ Error de conexión: {str(e)}")
        return False

def test_file_system_paths():
    """Verificar las rutas del sistema de archivos"""
    print("\n=== VERIFICANDO SISTEMA DE ARCHIVOS ===")
    
    # Rutas importantes
    app_root = "/opt/barber-brothers"
    static_path = os.path.join(app_root, "app", "static")
    uploads_path = os.path.join(static_path, "uploads")
    sliders_path = os.path.join(uploads_path, "sliders")
    
    paths_to_check = [
        ("Raíz del proyecto", app_root),
        ("Carpeta static", static_path),
        ("Carpeta uploads", uploads_path),
        ("Carpeta sliders", sliders_path)
    ]
    
    for name, path in paths_to_check:
        print(f"\n📁 {name}: {path}")
        
        if os.path.exists(path):
            print("  ✅ Existe")
            
            # Verificar permisos
            is_readable = os.access(path, os.R_OK)
            is_writable = os.access(path, os.W_OK)
            is_executable = os.access(path, os.X_OK)
            
            print(f"  📖 Lectura: {'✅' if is_readable else '❌'}")
            print(f"  ✏️ Escritura: {'✅' if is_writable else '❌'}")
            print(f"  🏃 Ejecución: {'✅' if is_executable else '❌'}")
            
            # Obtener propietario y permisos
            stat_info = os.stat(path)
            owner_uid = stat_info.st_uid
            group_gid = stat_info.st_gid
            permissions = oct(stat_info.st_mode)[-3:]
            
            print(f"  👤 UID: {owner_uid}, GID: {group_gid}")
            print(f"  🔒 Permisos: {permissions}")
            
            # Listar contenido si es directorio
            if os.path.isdir(path):
                try:
                    contents = os.listdir(path)
                    print(f"  📄 Archivos: {len(contents)}")
                    if contents and path == sliders_path:
                        print("  📸 Imágenes encontradas:")
                        for item in contents[:5]:  # Mostrar solo los primeros 5
                            item_path = os.path.join(path, item)
                            size = os.path.getsize(item_path) if os.path.isfile(item_path) else 0
                            print(f"    - {item} ({size} bytes)")
                        if len(contents) > 5:
                            print(f"    ... y {len(contents) - 5} más")
                except PermissionError:
                    print("  ❌ Sin permisos para listar contenido")
        else:
            print("  ❌ No existe")
            
            # Intentar crear si es la carpeta sliders
            if path == sliders_path:
                try:
                    os.makedirs(path, exist_ok=True)
                    print("  ✅ Carpeta creada")
                except Exception as e:
                    print(f"  ❌ No se pudo crear: {e}")

def test_web_access():
    """Probar acceso web a las imágenes"""
    print("\n=== VERIFICANDO ACCESO WEB ===")
    
    base_urls = [
        "http://localhost",
        "http://127.0.0.1:5000",
        "http://144.217.86.8"
    ]
    
    # Rutas de prueba
    test_paths = [
        "/static/images/foto1.jpg",  # Imagen por defecto
        "/static/uploads/sliders/",  # Directorio de sliders
    ]
    
    for base_url in base_urls:
        print(f"\n🌐 Probando servidor: {base_url}")
        
        for path in test_paths:
            full_url = base_url + path
            try:
                response = requests.get(full_url, timeout=10)
                status_code = response.status_code
                
                if status_code == 200:
                    print(f"  ✅ {path} - OK ({len(response.content)} bytes)")
                elif status_code == 404:
                    print(f"  ❌ {path} - No encontrado")
                elif status_code == 403:
                    print(f"  🚫 {path} - Prohibido")
                else:
                    print(f"  ⚠️ {path} - HTTP {status_code}")
                    
            except requests.exceptions.ConnectionError:
                print(f"  🔌 {path} - Servidor no responde")
            except requests.exceptions.Timeout:
                print(f"  ⏰ {path} - Timeout")
            except Exception as e:
                print(f"  ❌ {path} - Error: {str(e)}")

def test_nginx_config():
    """Verificar configuración de nginx"""
    print("\n=== VERIFICANDO CONFIGURACIÓN NGINX ===")
    
    nginx_config_paths = [
        "/etc/nginx/sites-available/barber-brothers",
        "/etc/nginx/sites-enabled/barber-brothers"
    ]
    
    for config_path in nginx_config_paths:
        print(f"\n📄 Archivo: {config_path}")
        
        if os.path.exists(config_path):
            print("  ✅ Existe")
            
            try:
                with open(config_path, 'r') as f:
                    content = f.read()
                    
                # Buscar configuraciones relacionadas con static
                static_locations = []
                lines = content.split('\n')
                
                for i, line in enumerate(lines):
                    if 'location' in line and '/static' in line:
                        # Capturar el bloque location
                        block_lines = [line.strip()]
                        for j in range(i+1, min(i+10, len(lines))):
                            if lines[j].strip().startswith('}'):
                                block_lines.append(lines[j].strip())
                                break
                            block_lines.append(lines[j].strip())
                        static_locations.append('\n    '.join(block_lines))
                
                if static_locations:
                    print("  📍 Configuraciones de archivos estáticos:")
                    for loc in static_locations:
                        print(f"    {loc}")
                else:
                    print("  ⚠️ No se encontraron configuraciones de /static")
                    
            except PermissionError:
                print("  ❌ Sin permisos para leer")
        else:
            print("  ❌ No existe")

def test_url_generation():
    """Simular el proceso de generación de URLs"""
    print("\n=== SIMULANDO GENERACIÓN DE URLs ===")
    
    # Simular el resultado de save_image
    sample_filename = "abc123def456.jpg"
    
    # Como debería ser según save_image
    save_image_result = f"/static/uploads/sliders/{sample_filename}"
    print(f"📤 save_image() retornaría: {save_image_result}")
    
    # Como se almacena en la BD (después del fix)
    db_stored_url = save_image_result
    print(f"💾 Se almacena en BD: {db_stored_url}")
    
    # Como debería renderizarse en HTML
    html_src = db_stored_url
    print(f"🌐 En HTML src='': {html_src}")
    
    # URL completa que el navegador intentaría cargar
    full_urls = [
        f"http://144.217.86.8{html_src}",
        f"http://localhost{html_src}"
    ]
    
    print("🔗 URLs completas:")
    for url in full_urls:
        print(f"  {url}")

def main():
    """Función principal de debug"""
    print("🔍 SCRIPT DE DEBUG EXHAUSTIVO - SLIDERS IMÁGENES")
    print("=" * 60)
    
    # 1. Verificar base de datos
    sliders = test_database_connection()
    
    # 2. Verificar sistema de archivos
    test_file_system_paths()
    
    # 3. Verificar acceso web
    test_web_access()
    
    # 4. Verificar nginx
    test_nginx_config()
    
    # 5. Simular URLs
    test_url_generation()
    
    print("\n" + "=" * 60)
    print("🏁 DEBUG COMPLETADO")
    
    # Si hay sliders, probar acceso directo
    if sliders:
        print("\n🎯 PROBANDO ACCESO DIRECTO A IMÁGENES DE SLIDERS:")
        for slider in sliders[:3]:  # Solo los primeros 3
            slider_id, titulo, tipo, imagen_url, activo, fecha = slider
            print(f"\n📸 Slider: {titulo}")
            print(f"  URL en BD: {imagen_url}")
            
            if imagen_url:
                # Probar acceso directo
                test_urls = [
                    f"http://144.217.86.8{imagen_url}",
                    f"http://localhost{imagen_url}"
                ]
                
                for test_url in test_urls:
                    try:
                        response = requests.get(test_url, timeout=5)
                        if response.status_code == 200:
                            print(f"  ✅ Accesible: {test_url}")
                        else:
                            print(f"  ❌ HTTP {response.status_code}: {test_url}")
                    except Exception as e:
                        print(f"  ❌ Error: {test_url} - {str(e)}")

if __name__ == "__main__":
    main() 