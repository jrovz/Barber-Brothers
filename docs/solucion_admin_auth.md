# Instrucciones para Solucionar el Error 500 de Autenticación en la Barbería

Este documento proporciona instrucciones paso a paso para solucionar el error interno del servidor (500) que ocurre durante la autenticación en el panel de administración de la aplicación desplegada en Google Cloud Platform.

## Diagnóstico del Problema

El problema identificado es un error en el proceso de autenticación que podría deberse a una de las siguientes causas:

1. El usuario administrador no existe en la base de datos PostgreSQL de GCP.
2. El usuario existe pero con un rol incorrecto (no es 'admin').
3. El usuario existe pero no tiene una contraseña válida configurada.
4. Hay un problema de conexión entre la aplicación y la base de datos.

## Pasos para Solucionar el Problema

### 1. Verificar la Existencia del Usuario Administrador

Primero, necesitamos verificar si el usuario administrador existe en la base de datos de GCP:

```bash
# Configurar las variables de entorno necesarias
export GOOGLE_CLOUD_PROJECT="barber-brothers-460514"
export CLOUD_SQL_REGION="us-central1"
export CLOUD_SQL_INSTANCE="barberia-db"
export INSTANCE_CONNECTION_NAME="${GOOGLE_CLOUD_PROJECT}:${CLOUD_SQL_REGION}:${CLOUD_SQL_INSTANCE}"
export DB_USER="barberia_user"
export DB_NAME="barberia_db"
export DB_PASS="tu_contraseña_segura"  # Reemplaza con la contraseña correcta

# Ejecutar el script de verificación
python scripts/verify_admin_gcp.py
```

### 2. Corregir o Crear el Usuario Administrador

Si el paso anterior muestra que el usuario no existe o tiene configuración incorrecta, use este script para arreglarlo:

```bash
# Configurar o restablecer el usuario administrador
python scripts/setup_admin_gcp.py --username admin --email admin@example.com --password admin123 --force-reset
```

Este comando:
- Creará el usuario "admin" si no existe
- Actualizará su rol a "admin" si es necesario
- Establecerá la contraseña como "admin123"

### 3. Mejorar la Depuración para Problemas Futuros

```bash
# Añadir middleware de depuración para capturar mejor los errores de autenticación
python scripts/improve_auth_debug.py

# Desplegar la aplicación con el modo de depuración activado
gcloud run deploy barberia-app --source=. --set-env-vars=FLASK_DEBUG=1
```

### 4. Verificar los Logs en Cloud Run

```bash
# Ver logs de error en Cloud Run
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=barberia-app AND severity>=ERROR" --limit=20
```

### 5. Probar la Autenticación

1. Accede al panel de administración en: https://barberia-app-xxxxx.run.app/admin/login
2. Inicia sesión con:
   - Usuario: admin
   - Contraseña: admin123

### 6. Desactivar el Modo de Depuración Después de Solucionar el Problema

```bash
# Cuando el problema esté resuelto, desactiva el modo de depuración
gcloud run deploy barberia-app --source=. --set-env-vars=FLASK_DEBUG=0
```

## Consideraciones de Seguridad

- Después de solucionar el problema, cambia la contraseña "admin123" por una más segura.
- Puedes hacerlo con el siguiente comando:

```bash
python scripts/setup_admin_gcp.py --username admin --password TuContraseñaSegura123! --force-reset
```

## Solución de Problemas Adicionales

Si después de seguir estos pasos aún persisten los problemas:

1. Verifica las conexiones de red entre Cloud Run y Cloud SQL:
   ```bash
   python scripts/cloud_run_diagnosis.py --check-connections
   ```

2. Verifica los permisos en Cloud SQL:
   ```bash
   python scripts/check_gcp_resources.py --check-permissions
   ```

3. Consulta los logs específicos de autenticación:
   ```bash
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=barberia-app AND textPayload:auth_debug" --limit=20
   ```

## Contacto para Soporte

Si continúas experimentando problemas después de seguir estas instrucciones, contacta al equipo de desarrollo en soporte@barber-brothers.example.com.
