# Estrategias de Optimización para Azure F1

## Límites del Plan F1 a Tener en Cuenta

- **CPU**: 60 minutos al día (total de todas las aplicaciones en el plan)
- **Memoria**: 1GB
- **Almacenamiento**: 1GB
- **Ancho de banda**: 165MB/día

## Estrategias de Optimización

### Rendimiento de la Aplicación

1. **Implementar caché agresivo:**
   ```python
   # Ejemplo de configuración en Flask
   from flask_caching import Cache
   
   cache = Cache(config={
       'CACHE_TYPE': 'simple',
       'CACHE_DEFAULT_TIMEOUT': 300  # 5 minutos
   })
   
   # En create_app()
   cache.init_app(app)
   
   # En rutas
   @app.route('/')
   @cache.cached(timeout=300)  # Cachear página principal por 5 minutos
   def index():
       # ...
   ```

2. **Reducir consultas a la base de datos:**
   - Usa `join` en lugar de consultas múltiples
   - Limita el número de registros consultados
   - Implementa paginación para listas largas

3. **Optimizar imágenes antes de subir:**
   - Redimensionar a tamaño máximo necesario
   - Comprimir con calidad apropiada
   - Convertir a formatos eficientes (WebP)

4. **Minificar CSS y JavaScript:**
   - Usar versiones minificadas en producción
   - Combinar archivos para reducir solicitudes HTTP

### Base de Datos

1. **Índices optimizados:**
   - Crear índices para campos de búsqueda frecuentes
   - Evitar índices innecesarios

2. **Consultas eficientes:**
   - Usar `EXPLAIN` para analizar consultas
   - Optimizar joins y where clauses

3. **Conexiones de base de datos:**
   - Usar pool de conexiones con tamaño limitado
   - Cerrar conexiones cuando no se usen

### Blob Storage

1. **Acceso CDN para archivos públicos:**
   - Crear URLs con SAS de larga duración para activos estáticos
   - Implementar caché del navegador con headers adecuados

2. **Lazy loading para imágenes:**
   - Cargar imágenes solo cuando sean visibles
   - Usar thumbnails para previsualizaciones

### Estrategias para no exceder el límite de CPU

1. **Implementar cola de tareas:**
   - Procesar operaciones pesadas en horas de bajo tráfico
   - Usar Azure Functions (plan de consumo) para tareas asíncronas

2. **Hibernación inteligente:**
   - La aplicación se hibernará automáticamente tras 20 minutos de inactividad
   - Implementar un "ping" externo para mantener activa solo durante horas críticas

3. **Monitoreo de uso:**
   - Revisar el uso diario de CPU en Azure Portal
   - Identificar y optimizar operaciones que consumen más CPU

### Script de Optimización de Imágenes

```python
from PIL import Image
import os

def optimize_image(input_path, output_path, quality=85, max_size=(800, 800)):
    """Optimiza una imagen para reducir su tamaño"""
    try:
        with Image.open(input_path) as img:
            # Convertir a RGB si es RGBA
            if img.mode == 'RGBA':
                img = img.convert('RGB')
                
            # Redimensionar si es más grande que max_size
            if img.width > max_size[0] or img.height > max_size[1]:
                img.thumbnail(max_size, Image.LANCZOS)
                
            # Guardar con compresión
            img.save(output_path, optimize=True, quality=quality)
            
            print(f"Imagen optimizada: {os.path.basename(output_path)}")
            
            # Mostrar reducción de tamaño
            original_size = os.path.getsize(input_path)
            new_size = os.path.getsize(output_path)
            reduction = (original_size - new_size) / original_size * 100
            print(f"Reducción: {reduction:.1f}% ({original_size} → {new_size} bytes)")
            
    except Exception as e:
        print(f"Error al optimizar {input_path}: {e}")
```

### Recomendaciones de Monitoreo

1. **Verificar uso de CPU y memoria regularmente**
2. **Configurar alertas cuando el uso se acerque a los límites**
3. **Analizar patrones de tráfico para identificar horas pico**

Estas estrategias te ayudarán a mantener tu aplicación dentro de los límites del plan F1 gratuito mientras maximizas su rendimiento.
