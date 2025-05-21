import os
from google.cloud import storage
import tempfile

class CloudStorage:
    def __init__(self, bucket_name=None):
        """Inicializa el cliente de Google Cloud Storage y el nombre del bucket"""
        self.bucket_name = bucket_name or os.environ.get('GCS_BUCKET_NAME')
        if not self.bucket_name and (os.environ.get("GAE_ENV") == "standard" or os.environ.get("K_SERVICE")):
            raise ValueError("GCS_BUCKET_NAME environment variable is not set")
        
        # Solo inicializar si estamos en GCP
        self.client = None
        self.bucket = None
        if os.environ.get("GAE_ENV") == "standard" or os.environ.get("K_SERVICE"):
            self.client = storage.Client()
            self.bucket = self.client.bucket(self.bucket_name)

    def upload_file(self, file_object, destination_blob_name):
        """Sube un archivo a Cloud Storage"""
        if not self.client:
            # Si no estamos en GCP, devolver una ruta local
            return os.path.join('uploads', destination_blob_name)
            
        blob = self.bucket.blob(destination_blob_name)
        file_object.seek(0)  # Asegurarse de que el puntero del archivo esté al inicio
        blob.upload_from_file(file_object)
        
        # Hacer el blob públicamente accesible
        blob.make_public()
        
        # Devolver la URL pública
        return blob.public_url

    def download_file(self, source_blob_name, destination_file_name=None):
        """Descarga un archivo desde Cloud Storage"""
        if not self.client:
            # Si no estamos en GCP, devolver la ruta local
            local_path = os.path.join('app', 'static', 'uploads', source_blob_name)
            if os.path.exists(local_path):
                return local_path
            return None
            
        try:
            blob = self.bucket.blob(source_blob_name)
            
            if destination_file_name:
                blob.download_to_filename(destination_file_name)
                return destination_file_name
            else:
                # Si no se proporciona nombre de archivo, descargar a un archivo temporal
                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    blob.download_to_filename(temp_file.name)
                    return temp_file.name
        except Exception as e:
            print(f"Error descargando archivo {source_blob_name}: {e}")
            return None

    def delete_file(self, blob_name):
        """Elimina un archivo de Cloud Storage"""
        if not self.client:
            # Si no estamos en GCP, eliminar archivo local
            local_path = os.path.join('app', 'static', 'uploads', blob_name)
            if os.path.exists(local_path):
                os.remove(local_path)
                return True
            return False
            
        try:
            blob = self.bucket.blob(blob_name)
            blob.delete()
            return True
        except Exception as e:
            print(f"Error eliminando archivo {blob_name}: {e}")
            return False

# Función auxiliar para usar en la aplicación
def get_storage_client():
    """Devuelve una instancia de CloudStorage configurada con el bucket por defecto"""
    return CloudStorage()