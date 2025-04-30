import os

def check_upload_path():
    """
    Verifica si la ruta de uploads es correcta y no contiene duplicaciones
    """
    from flask import current_app
    
    upload_path = current_app.config['UPLOAD_FOLDER']
    print("\n=== VERIFICACIÓN DE RUTAS ===")
    print(f"Ruta de uploads configurada: {upload_path}")
    
    # Verificar si existe duplicación de 'app/app'
    parts = upload_path.split(os.sep)
    duplicated = False
    
    for i in range(1, len(parts)):
        if parts[i] == parts[i-1] == 'app':
            duplicated = True
            print(f"⚠️ ADVERTENCIA: Detectada duplicación de 'app' en la ruta")
            break
    
    if not duplicated:
        print("✅ Ruta correcta: No hay duplicación")
    
    # Verificar si la ruta existe
    if os.path.exists(upload_path):
        print(f"✅ La carpeta de uploads existe")
    else:
        print(f"❌ La carpeta de uploads NO existe")
        try:
            os.makedirs(upload_path, exist_ok=True)
            print(f"✅ Carpeta de uploads creada: {upload_path}")
        except Exception as e:
            print(f"❌ No se pudo crear la carpeta: {str(e)}")
    
    # Verificar permisos
    if os.access(upload_path, os.W_OK):
        print(f"✅ La carpeta tiene permisos de escritura")
    else:
        print(f"❌ La carpeta NO tiene permisos de escritura")
    
    print("=== FIN DE VERIFICACIÓN ===\n")
    return not duplicated