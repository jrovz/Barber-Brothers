import os
import sys

def main():
    """Verificar configuración de rutas de imágenes"""
    print("\n=== VERIFICACIÓN DE RUTAS DE IMÁGENES ===\n")
    
    # Obtener la ruta base del proyecto
    project_path = os.path.abspath(os.path.dirname(__file__))
    print(f"Ruta base del proyecto: {project_path}")
    
    # Rutas críticas a verificar
    app_path = os.path.join(project_path, 'app')
    uploads_path = os.path.join(app_path, 'static', 'uploads')
    duplicated_path = os.path.join(app_path, 'app', 'static', 'uploads')
    
    print(f"\nRuta de aplicación: {app_path}")
    print(f"Ruta correcta de uploads: {uploads_path}")
    print(f"Ruta incorrecta (duplicada): {duplicated_path}")
    
    # Verificar existencia de rutas
    print("\n--- Verificación de existencia ---")
    paths_to_check = {
        "Aplicación": app_path,
        "Uploads (correcto)": uploads_path,
        "Uploads (duplicado)": duplicated_path
    }
    
    for name, path in paths_to_check.items():
        if os.path.exists(path):
            print(f"✅ {name}: Existe - {path}")
            # Verificar si es directorio
            if os.path.isdir(path):
                print(f"   📁 Es un directorio")
                # Verificar archivos
                files = os.listdir(path)
                print(f"   - Contiene {len(files)} archivos/directorios")
            else:
                print(f"   📄 Es un archivo")
        else:
            print(f"❌ {name}: No existe - {path}")
    
    # Crear carpeta correcta si no existe
    if not os.path.exists(uploads_path):
        try:
            os.makedirs(uploads_path, exist_ok=True)
            print(f"\n✅ Carpeta de uploads creada: {uploads_path}")
        except Exception as e:
            print(f"\n❌ Error al crear carpeta: {str(e)}")
    
    # Crear subcarpetas necesarias
    subfolders = ['barberos', 'productos', 'servicios']
    for subfolder in subfolders:
        subfolder_path = os.path.join(uploads_path, subfolder)
        if not os.path.exists(subfolder_path):
            try:
                os.makedirs(subfolder_path, exist_ok=True)
                print(f"✅ Subcarpeta creada: {subfolder_path}")
            except Exception as e:
                print(f"❌ Error al crear subcarpeta {subfolder}: {str(e)}")
    
    # Buscar archivos en la ruta duplicada y copiarlos si existe
    if os.path.exists(duplicated_path):
        print("\n--- Migrando archivos de la ruta incorrecta ---")
        import shutil
        
        for root, dirs, files in os.walk(duplicated_path):
            for file in files:
                src_file = os.path.join(root, file)
                # Obtener ruta relativa desde la base duplicada
                rel_path = os.path.relpath(src_file, duplicated_path)
                # Construir ruta destino
                dst_file = os.path.join(uploads_path, rel_path)
                # Asegurar que la carpeta destino existe
                os.makedirs(os.path.dirname(dst_file), exist_ok=True)
                
                try:
                    shutil.copy2(src_file, dst_file)
                    print(f"✅ Copiado: {rel_path}")
                except Exception as e:
                    print(f"❌ Error al copiar {rel_path}: {str(e)}")
    
    print("\n=== VERIFICACIÓN COMPLETADA ===\n")

if __name__ == "__main__":
    main()