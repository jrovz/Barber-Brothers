import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app

def allowed_file(filename):
    """
    Verifica si el archivo tiene una extensión permitida
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def save_image(file, subfolder):
    """
    Guarda un archivo de imagen en el sistema de archivos
    
    Args:
        file: El objeto archivo de Flask request.files
        subfolder: La subcarpeta dentro de UPLOAD_FOLDER donde guardar el archivo
        
    Returns:
        La ruta relativa del archivo para almacenar en la base de datos,
        o None si hubo un error o no se proporcionó un archivo
    """
    # Si no hay archivo o está vacío
    if not file or file.filename == '':
        return None
        
    # Si el archivo tiene una extensión permitida
    if file and allowed_file(file.filename):
        # Generar nombre seguro y único para el archivo
        original_filename = secure_filename(file.filename)
        file_extension = os.path.splitext(original_filename)[1]
        unique_filename = f"{uuid.uuid4().hex}{file_extension}"
        
        # Crear la subcarpeta si no existe
        subfolder_path = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder)
        if not os.path.exists(subfolder_path):
            os.makedirs(subfolder_path)
        
        # Ruta completa donde se guardará el archivo
        file_path = os.path.join(subfolder_path, unique_filename)
        
        # Guardar el archivo
        file.save(file_path)
        
        # Devolver la ruta relativa para almacenar en la BD (para acceso vía web)
        return f'/static/uploads/{subfolder}/{unique_filename}'
    
    return None