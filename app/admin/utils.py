import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app

def allowed_file(filename):
    allowed_extensions = current_app.config['ALLOWED_EXTENSIONS']
    is_allowed = '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions
    print(f"¿Archivo {filename} permitido?: {is_allowed}")
    return is_allowed

def save_image(file, subfolder):
    import logging
    from flask import request, current_app
        
    # Configuración de logging...
    logger = logging.getLogger('image_uploader')
    
    # CORRECCIÓN: Verificar la estructura de la ruta
    upload_folder = current_app.config['UPLOAD_FOLDER']
    logger.info(f"UPLOAD_FOLDER configurado: {upload_folder}")
    
    # Verificar si hay duplicación en la ruta
    parts = upload_folder.split(os.sep)
    duplicated = False
    for i in range(1, len(parts)):
        if parts[i] == parts[i-1] == 'app':
            duplicated = True
            logger.warning(f"⚠️ Detectada duplicación de 'app' en la ruta")
            # Corregir la ruta temporalmente
            corrected_path = os.path.join(os.path.dirname(upload_folder), 'static', 'uploads')
            logger.info(f"Usando ruta corregida: {corrected_path}")
            upload_folder = corrected_path
            break
    
    # Verificar que la carpeta de uploads existe
    if not os.path.exists(upload_folder):
        logger.error(f"❌ La carpeta de uploads no existe: {upload_folder}")
        # Intentar crearla
        try:
            os.makedirs(upload_folder, exist_ok=True)
            logger.info(f"✅ Carpeta de uploads creada: {upload_folder}")
        except Exception as e:
            logger.error(f"❌ No se pudo crear la carpeta: {str(e)}")
            return None
    
    # Verificar archivo
    if not file or file.filename == '':
        logger.error("No se proporcionó archivo o nombre vacío")
        return None
    
    # Verificar extensión
    if not allowed_file(file.filename):
        logger.warning(f"Extensión no permitida: {file.filename}")
        return None
    
    # Si el archivo tiene una extensión permitida
    if file and allowed_file(file.filename):
        # Generar nombre seguro y único para el archivo
        original_filename = secure_filename(file.filename)
        file_extension = os.path.splitext(original_filename)[1]
        unique_filename = f"{uuid.uuid4().hex}{file_extension}"
        
        # Crear la subcarpeta si no existe
        subfolder_path = os.path.join(upload_folder, subfolder)
        if not os.path.exists(subfolder_path):
            os.makedirs(subfolder_path)
        
        # Ruta completa donde se guardará el archivo
        file_path = os.path.join(subfolder_path, unique_filename)
        
        # Guardar el archivo
        try:
            file.save(file_path)
            
            # Verificar si el archivo existe después de guardarlo
            if os.path.exists(file_path):
                logger.info(f"✅ Archivo guardado exitosamente y verificado")
                logger.info(f"   - Tamaño del archivo: {os.path.getsize(file_path)} bytes")
            else:
                logger.error(f"❌ El archivo no existe después de guardarlo")
                
            logger.info(f"   - Ruta del sistema: {file_path}")
            logger.info(f"   - URL relativa: /static/uploads/{subfolder}/{unique_filename}")
            logger.info(f"   - URL absoluta: {request.host_url}static/uploads/{subfolder}/{unique_filename}")
        except Exception as e:
            logger.error(f"❌ Error al guardar: {str(e)}")
            return None
        
        logger.info(f"--- FIN GUARDADO DE IMAGEN ---")
        return f'/static/uploads/{subfolder}/{unique_filename}'
    
    logger.warning(f"Extensión no permitida: {file.filename}")
    return None

