# Conectando tu aplicación en Cloud Run con PostgreSQL en GCP

Esta guía te ayudará a conectar tu aplicación Flask desplegada en Cloud Run con tu base de datos PostgreSQL en Cloud SQL.

## Requisitos previos

1. Tener la base de datos PostgreSQL creada en GCP Cloud SQL
2. Tener el SDK de Google Cloud instalado y configurado
3. Tener permisos suficientes en tu proyecto de GCP

## Pasos para conectar la aplicación con Cloud SQL

### 1. Verificar que la base de datos existe

```powershell
gcloud sql instances list --project=barber-brothers-460514
```

Si no ves tu instancia "barberia-db", necesitas crearla:

```powershell
gcloud sql instances create barberia-db `
  --database-version=POSTGRES_14 `
  --cpu=1 `
  --memory=3840MB `
  --region=us-east1 `
  --storage-type=SSD `
  --storage-size=10GB `
  --root-password="TuContraseñaSegura"
```

### 2. Crear la base de datos y el usuario si no existen

```powershell
# Conectar a la instancia PostgreSQL
gcloud sql connect barberia-db --user=postgres

# En la consola de PostgreSQL:
CREATE DATABASE barberia_db;
CREATE USER barberia_user WITH PASSWORD 'TuContraseñaSegura';
GRANT ALL PRIVILEGES ON DATABASE barberia_db TO barberia_user;
\q
```

### 3. Desplegar la aplicación en Cloud Run

Usa el script de despliegue que hemos creado:

```powershell
# Edita primero el script para configurar tu contraseña
cd "c:\Users\jrove\OneDrive\Documentos\PROYECTOS WEB\Barber-Brothers"
.\scripts\deploy_to_gcp.ps1
```

### 4. Ejecutar las migraciones de la base de datos

Después de desplegar la aplicación, puedes ejecutar las migraciones de la base de datos con el comando que aparece al final del script de despliegue. Algo como:

```powershell
gcloud run jobs create barberia-migrations --image=[URL_DE_TU_IMAGEN] --set-env-vars=FLASK_APP=wsgi.py --command=python --args=-m,flask,db,upgrade --region=us-east1 --add-cloudsql-instances=barber-brothers-460514:us-east1:barberia-db
gcloud run jobs execute barberia-migrations --region=us-east1
```

### 5. Verificar la conexión

Para verificar que tu aplicación está conectada correctamente a la base de datos:

1. Accede a la URL de tu aplicación en Cloud Run
2. Intenta iniciar sesión u otra acción que interactúe con la base de datos
3. Revisa los logs de la aplicación:

```powershell
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=barberia-app AND severity>=WARNING" --limit=20
```

## Solución de problemas comunes

### Error de conexión a la base de datos

Si ves errores de conexión:

1. Verifica que las variables de entorno estén configuradas correctamente:
   ```powershell
   gcloud run services describe barberia-app --region=us-east1 --format="yaml(spec.template.spec.containers[0].env)"
   ```

2. Asegúrate de que el servicio de Cloud Run tiene permisos para acceder a Cloud SQL:
   ```powershell
   gcloud run services describe barberia-app --region=us-east1 --format="yaml(spec.template.spec.volumes)"
   ```

3. Verifica que la instancia de Cloud SQL está en la misma región que tu servicio de Cloud Run

### Errores de migración

Si tienes problemas con las migraciones:

1. Revisa los logs del job de migración:
   ```powershell
   gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=barberia-migrations" --limit=50
   ```

2. Intenta ejecutar las migraciones manualmente conectándote a la base de datos directamente
