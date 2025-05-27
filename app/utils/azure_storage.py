"""
Módulo para manejar el almacenamiento de archivos en Azure Blob Storage.
"""
import os
from datetime import datetime, timedelta
import mimetypes
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions

def get_blob_service_client():
    """
    Obtiene un cliente para Azure Blob Storage
    """
    connection_string = os.environ.get('AZURE_STORAGE_CONNECTION_STRING')
    if not connection_string:
        raise ValueError("AZURE_STORAGE_CONNECTION_STRING no está configurado")
    
    return BlobServiceClient.from_connection_string(connection_string)

def upload_file(file_stream, destination_blob_name, content_type=None):
    """
    Sube un archivo a Azure Blob Storage
    
    Args:
        file_stream: El objeto de archivo a subir
        destination_blob_name: Nombre del blob de destino (incluyendo la ruta)
        content_type: Tipo MIME del archivo (opcional)
    
    Returns:
        URL pública del archivo subido
    """
    try:
        # Obtener cliente y container
        blob_service_client = get_blob_service_client()
        container_name = os.environ.get('AZURE_STORAGE_CONTAINER', 'static')
        container_client = blob_service_client.get_container_client(container_name)
        
        # Detectar tipo de contenido si no se proporciona
        if not content_type:
            content_type, _ = mimetypes.guess_type(destination_blob_name)
        
        # Crear un cliente para el blob
        blob_client = container_client.get_blob_client(destination_blob_name)
        
        # Subir el archivo con tipo de contenido
        blob_client.upload_blob(file_stream, overwrite=True, content_settings={'content_type': content_type})
        
        # Obtener la URL del blob
        account_name = blob_service_client.account_name
        blob_url = f"https://{account_name}.blob.core.windows.net/{container_name}/{destination_blob_name}"
        
        print(f"Archivo subido exitosamente a: {blob_url}")
        return blob_url
        
    except Exception as e:
        print(f"Error al subir archivo a Azure Blob Storage: {e}")
        # Fallback a almacenamiento local si hay error
        return handle_upload_fallback(file_stream, destination_blob_name)

def handle_upload_fallback(file_stream, destination_blob_name):
    """
    Método de respaldo para guardar el archivo localmente si falla Azure Blob Storage
    """
    try:
        # Construir ruta local basada en la estructura de App Service
        uploads_folder = os.path.join('app', 'static', 'uploads')
        if not os.path.exists(uploads_folder):
            os.makedirs(uploads_folder, exist_ok=True)
        
        # Determinar ruta local
        local_path = os.path.join(uploads_folder, os.path.basename(destination_blob_name))
        
        # Guardar archivo localmente
        with open(local_path, 'wb') as f:
            file_stream.seek(0)
            f.write(file_stream.read())
        
        # Construir URL relativa para acceso
        relative_url = f"/static/uploads/{os.path.basename(destination_blob_name)}"
        print(f"Fallback: Archivo guardado localmente en {relative_url}")
        return relative_url
        
    except Exception as e:
        print(f"Error en fallback de subida de archivo: {e}")
        return None

def delete_file(blob_name):
    """
    Elimina un archivo de Azure Blob Storage
    
    Args:
        blob_name: Nombre del blob a eliminar (incluyendo la ruta)
    
    Returns:
        True si se eliminó correctamente, False en caso contrario
    """
    try:
        # Obtener cliente y container
        blob_service_client = get_blob_service_client()
        container_name = os.environ.get('AZURE_STORAGE_CONTAINER', 'static')
        container_client = blob_service_client.get_container_client(container_name)
        
        # Eliminar el blob
        blob_client = container_client.get_blob_client(blob_name)
        blob_client.delete_blob()
        
        print(f"Archivo eliminado exitosamente: {blob_name}")
        return True
        
    except Exception as e:
        print(f"Error al eliminar archivo de Azure Blob Storage: {e}")
        return False

def get_file_url(blob_name, expiry_hours=24):
    """
    Obtiene una URL con SAS para acceso temporal a un archivo
    
    Args:
        blob_name: Nombre del blob (incluyendo la ruta)
        expiry_hours: Horas de validez del token SAS
    
    Returns:
        URL con token SAS
    """
    try:
        # Obtener cliente y container
        blob_service_client = get_blob_service_client()
        account_name = blob_service_client.account_name
        container_name = os.environ.get('AZURE_STORAGE_CONTAINER', 'static')
        
        # Generar SAS
        sas_token = generate_blob_sas(
            account_name=account_name,
            container_name=container_name,
            blob_name=blob_name,
            account_key=blob_service_client.credential.account_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(hours=expiry_hours)
        )
        
        # Construir URL completa con SAS
        blob_url = f"https://{account_name}.blob.core.windows.net/{container_name}/{blob_name}?{sas_token}"
        
        return blob_url
        
    except Exception as e:
        print(f"Error al generar URL para archivo en Azure Blob Storage: {e}")
        # Fallback a URL relativa para acceso local
        return f"/static/uploads/{os.path.basename(blob_name)}"
