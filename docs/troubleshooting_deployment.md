# Guía de Solución de Problemas de Despliegue en GCP

Este documento proporciona una guía detallada para solucionar los problemas de despliegue de la aplicación Barber Brothers en Google Cloud Platform (GCP).

## Problema Actual

La aplicación está teniendo problemas con:
1. Conexión a la base de datos PostgreSQL en Cloud SQL
2. Ejecución del script de inicialización de la base de datos (setup_db.py)
3. Errores durante el despliegue en Cloud Run

## Soluciones Implementadas

Se han realizado las siguientes mejoras:

1. **Corrección del script setup_db.py**:
   - Eliminado código inalcanzable
   - Mejorada la función de inicialización de la base de datos
   - Implementada mejor gestión de errores

2. **Actualización del Dockerfile**:
   - Mejorado el script de inicio para continuar incluso si setup_db.py falla
   - Añadido logging de variables de entorno críticas

3. **Corrección de errores en el código**:
   - Arreglado error de sintaxis en cloud_connection_pg.py
   - Mejorado el manejo de errores en la inicialización de la base de datos

4. **Nuevos scripts de diagnóstico**:
   - Script para depurar el contenedor Docker localmente
   - Script para probar la conexión a la base de datos de forma aislada
   - Script de despliegue con modo de depuración activado

## Pasos para Solucionar los Problemas

### 1. Prueba Local del Contenedor

Para identificar problemas con el contenedor antes de desplegarlo:

```powershell
# Navegar al directorio raíz del proyecto
cd "c:\Users\jrove\OneDrive\Documentos\PROYECTOS WEB\Barber-Brothers"

# Ejecutar el script de depuración del contenedor
python scripts/debug_container.py
```

Este script compilará y ejecutará el contenedor localmente con las mismas variables de entorno que se usarían en Cloud Run.

### 2. Prueba de Conexión a la Base de Datos

Para verificar que la lógica de conexión a la base de datos funciona correctamente:

```powershell
# Ejecutar el script de prueba de conexión
python scripts/test_db_connection.py
```

Este script probará diferentes métodos de conexión a la base de datos y mostrará cuáles funcionan.

### 3. Despliegue con Modo de Depuración

Para desplegar la aplicación con logging detallado:

```powershell
# Navegar al directorio de scripts
cd "c:\Users\jrove\OneDrive\Documentos\PROYECTOS WEB\Barber-Brothers\scripts"

# Ejecutar el script de despliegue con depuración
.\debug_deploy_to_gcp.ps1
```

### 4. Verificación de Logs en GCP

Para ver los logs de la aplicación desplegada:

```powershell
# Reemplazar barberia-app con el nombre de tu servicio si es diferente
gcloud logging read 'resource.type=cloud_run_revision AND resource.labels.service_name=barberia-app' --limit=50
```

### 5. Verificación de la Base de Datos

Para verificar el estado de la base de datos:

```powershell
# Conectarse a la instancia de Cloud SQL
gcloud sql connect barberia-db --user=postgres

# Una vez conectado, ejecutar:
\l                  # Listar bases de datos
\c barberia-db      # Conectarse a la base de datos
\dt                 # Listar tablas
```

## Configuración Correcta de Variables de Entorno

Asegúrate de que las siguientes variables de entorno estén configuradas correctamente:

| Variable | Valor | Descripción |
|----------|-------|-------------|
| INSTANCE_CONNECTION_NAME | barber-brothers-460514:us-central1:barberia-db | Nombre completo de la instancia de Cloud SQL |
| DB_USER | postgres | Usuario de la base de datos |
| DB_PASS | y3WhoYFS | Contraseña de la base de datos |
| DB_NAME | barberia-db | Nombre de la base de datos |
| GOOGLE_CLOUD_PROJECT | barber-brothers-460514 | ID del proyecto de GCP |
| REGION | us-central1 | Región de la instancia de Cloud SQL |

## Estructura de Directorios Correcta

Asegúrate de que la estructura de directorios de tu aplicación coincida con la esperada:

```
app/
├── __init__.py          # Punto de entrada de Flask
├── config/              # Configuración de la aplicación
├── models/              # Modelos de datos
├── static/              # Archivos estáticos
│   └── uploads/         # Directorio para cargas (debe existir)
├── templates/           # Plantillas HTML
└── utils/               # Utilidades
    ├── cloud_connection_pg.py  # Conexión a PostgreSQL
    └── db_init_handler.py      # Inicialización de la BD
```

## Siguientes Pasos

Si los problemas persisten después de seguir esta guía, considera:

1. Revisar los permisos IAM para asegurarte de que el servicio tiene acceso a Cloud SQL
2. Verificar que la instancia de Cloud SQL acepta conexiones desde Cloud Run
3. Comprobar las reglas de firewall si estás utilizando una red VPC personalizada
