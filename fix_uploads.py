import os
import shutil

# Ruta base del proyecto
project_path = os.path.abspath(os.path.dirname(__file__))
print(f"Ruta del proyecto: {project_path}")

# Ruta correcta de uploads
correct_path = os.path.join(project_path, 'app', 'static', 'uploads')
print(f"Ruta correcta de uploads: {correct_path}")

# Ruta incorrecta con duplicación
incorrect_path = os.path.join(project_path, 'app', 'app', 'static', 'uploads')
print(f"Ruta incorrecta de uploads: {incorrect_path}")

# Crear carpeta correcta si no existe
os.makedirs(correct_path, exist_ok=True)
print(f"✅ Carpeta correcta creada: {correct_path}")

# Crear subcarpetas para diferentes tipos de imágenes
for subfolder in ['barberos', 'productos', 'servicios']:
    subfolder_path = os.path.join(correct_path, subfolder)
    os.makedirs(subfolder_path, exist_ok=True)
    print(f"✅ Subcarpeta creada: {subfolder_path}")

# Mover archivos de la ruta incorrecta a la correcta si existen
if os.path.exists(incorrect_path):
    print(f"⚠️ Se encontró la ruta incorrecta: {incorrect_path}")
    
    # Mover cada subcarpeta si existe
    for subfolder in ['barberos', 'productos', 'servicios']:
        src_folder = os.path.join(incorrect_path, subfolder)
        dst_folder = os.path.join(correct_path, subfolder)
        
        if os.path.exists(src_folder):
            print(f"Moviendo archivos de {src_folder} a {dst_folder}")
            # Mover cada archivo
            for file in os.listdir(src_folder):
                src_file = os.path.join(src_folder, file)
                dst_file = os.path.join(dst_folder, file)
                if os.path.isfile(src_file):
                    shutil.copy2(src_file, dst_file)
                    print(f"  - Copiado: {file}")
    
    print("✅ Archivos copiados correctamente")
else:
    print("ℹ️ No se encontró la ruta incorrecta, no es necesario mover archivos.")

print("🎉 Proceso completado!")