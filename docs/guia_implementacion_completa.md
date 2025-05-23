# Guía de Implementación Final - Barber Brothers en GCP

Esta guía detalla todos los pasos necesarios para implementar completamente el sistema de Barber Brothers en Google Cloud Platform, con énfasis en seguridad, escalabilidad y confiabilidad.

## Índice

1. [Preparación del entorno](#1-preparación-del-entorno)
2. [Configuración de infraestructura](#2-configuración-de-infraestructura)
3. [Implementación de la aplicación](#3-implementación-de-la-aplicación)
4. [Configuración de la base de datos](#4-configuración-de-la-base-de-datos)
5. [Seguridad y acceso](#5-seguridad-y-acceso)
6. [Monitoreo y diagnóstico](#6-monitoreo-y-diagnóstico)
7. [Mantenimiento continuo](#7-mantenimiento-continuo)
8. [Verificación final](#8-verificación-final)
9. [Resolución de problemas comunes](#9-resolución-de-problemas-comunes)

## 1. Preparación del entorno

### 1.1 Instalar herramientas necesarias

Antes de comenzar, asegúrate de tener instalado:

- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)
- Python 3.9+
- Git

### 1.2 Autenticación en GCP

```bash
# Iniciar sesión en Google Cloud
gcloud auth login

# Configurar el proyecto activo
gcloud config set project barber-brothers-460514
```

### 1.3 Habilitar las APIs necesarias

```bash
# Habilitar APIs requeridas
gcloud services enable sqladmin.googleapis.com \
    secretmanager.googleapis.com \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    cloudbuild.googleapis.com \
    storage.googleapis.com \
    logging.googleapis.com \
    monitoring.googleapis.com \
    vpcaccess.googleapis.com
```

### 1.4 Clonar repositorio

```bash
# Clonar el repositorio
git clone https://github.com/jrovz/barber-brothers.git
cd barber-brothers
```

## 2. Configuración de infraestructura

### 2.1 Configurar VPC y Serverless Connector

Para una comunicación segura entre servicios:

```bash
# Ejecutar el script de configuración del VPC Connector
chmod +x scripts/vpc_connector_setup.sh
./scripts/vpc_connector_setup.sh
```

El script creará:
- Una red VPC dedicada
- Una subred para el conector
- Un VPC Serverless Connector
- Configuración del servicio Cloud Run para usar el conector

### 2.2 Configurar Cloud Storage

```bash
# Crear bucket para uploads
gcloud storage buckets create gs://barberia-uploads \
  --location=us-central1 \
  --uniform-bucket-level-access

# Configurar acceso público para lectura
gcloud storage buckets add-iam-policy-binding gs://barberia-uploads \
  --member=allUsers \
  --role=roles/storage.objectViewer
```

### 2.3 Configurar Cloud SQL

```bash
# Crear instancia PostgreSQL
gcloud sql instances create barberia-db \
  --database-version=POSTGRES_15 \
  --cpu=1 \
  --memory=4GB \
  --region=us-central1 \
  --root-password="REEMPLAZAR_PASSWORD" \
  --storage-type=SSD \
  --storage-size=10 \
  --availability-type=zonal

# Crear base de datos
gcloud sql databases create barberia_db --instance=barberia-db

# Crear usuario para la aplicación
gcloud sql users create barberia_user \
  --instance=barberia-db \
  --password="REEMPLAZAR_PASSWORD"
```

### 2.4 Configurar Secret Manager

```bash
# Crear secretos para credenciales
echo "barberia_user" | gcloud secrets create db_user --data-file=-
echo "REEMPLAZAR_PASSWORD" | gcloud secrets create db_pass --data-file=-
echo "barberia_db" | gcloud secrets create db_name --data-file=-
echo "GENERAR_CLAVE_SECRETA" | gcloud secrets create secret_key --data-file=-

# Configuración de email
echo "smtp.gmail.com" | gcloud secrets create mail_server --data-file=-
echo "587" | gcloud secrets create mail_port --data-file=-
echo "True" | gcloud secrets create mail_use_tls --data-file=-
echo "tu_email@gmail.com" | gcloud secrets create mail_username --data-file=-
echo "tu_password_app" | gcloud secrets create mail_password --data-file=-
echo "Barber Brothers" | gcloud secrets create mail_sender --data-file=-
```

## 3. Implementación de la aplicación

### 3.1 Preparar el código

Asegúrate de que el Dockerfile y el archivo cloudbuild.yaml estén correctamente configurados según nuestras mejoras.

### 3.2 Construir y publicar la imagen de contenedor

```bash
# Construir imagen Docker
docker build -t gcr.io/barber-brothers-460514/barberia-app:v1 .

# Configurar Docker para autenticación con GCP
gcloud auth configure-docker

# Publicar imagen en Container Registry
docker push gcr.io/barber-brothers-460514/barberia-app:v1
```

### 3.3 Desplegar en Cloud Run

```bash
# Desplegar servicio en Cloud Run
gcloud run deploy barberia-app \
  --image gcr.io/barber-brothers-460514/barberia-app:v1 \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --set-env-vars="FLASK_ENV=production" \
  --set-env-vars="INSTANCE_CONNECTION_NAME=barber-brothers-460514:us-central1:barberia-db" \
  --set-env-vars="GCS_BUCKET_NAME=barberia-uploads" \
  --add-cloudsql-instances=barber-brothers-460514:us-central1:barberia-db \
  --vpc-connector=barberia-vpc-connector \
  --set-secrets="SECRET_KEY=secret_key:latest" \
  --set-secrets="MAIL_SERVER=mail_server:latest" \
  --set-secrets="MAIL_PORT=mail_port:latest" \
  --set-secrets="MAIL_USE_TLS=mail_use_tls:latest" \
  --set-secrets="MAIL_USERNAME=mail_username:latest" \
  --set-secrets="MAIL_PASSWORD=mail_password:latest" \
  --set-secrets="MAIL_DEFAULT_SENDER=mail_sender:latest"
```

### 3.4 Configurar CI/CD con Cloud Build

```bash
# Crear trigger para CI/CD
gcloud builds triggers create github \
  --name="deploy-barberia-app" \
  --repo="jrovz/barber-brothers" \
  --branch-pattern="main" \
  --build-config="cloudbuild.yaml"
```

## 4. Configuración de la base de datos

### 4.1 Ejecutar migraciones

```bash
# Crear job para migraciones
gcloud run jobs create barberia-migrations \
  --image gcr.io/barber-brothers-460514/barberia-app:v1 \
  --tasks 1 \
  --set-env-vars="FLASK_APP=wsgi.py" \
  --command="python" \
  --args="migrate.py" \
  --set-env-vars="INSTANCE_CONNECTION_NAME=barber-brothers-460514:us-central1:barberia-db" \
  --set-env-vars="GCS_BUCKET_NAME=barberia-uploads" \
  --add-cloudsql-instances=barber-brothers-460514:us-central1:barberia-db \
  --set-secrets="SECRET_KEY=secret_key:latest" \
  --vpc-connector=barberia-vpc-connector \
  --region us-central1

# Ejecutar job de migraciones
gcloud run jobs execute barberia-migrations --region us-central1 --wait
```

### 4.2 Configurar respaldos automáticos

```bash
# Configurar respaldos diarios
gcloud sql instances patch barberia-db \
  --backup-start-time="23:00" \
  --enable-bin-log
```

## 5. Seguridad y acceso

### 5.1 Configurar IAM para limitación de acceso

```bash
# Verificar permisos actuales
gcloud run services get-iam-policy barberia-app --region us-central1

# Si se requiere acceso autenticado en lugar de público:
gcloud run services remove-iam-policy-binding barberia-app \
  --member="allUsers" \
  --role="roles/run.invoker" \
  --region us-central1

# Agregar permisos específicos
gcloud run services add-iam-policy-binding barberia-app \
  --member="serviceAccount:SERVICE_ACCOUNT_EMAIL" \
  --role="roles/run.invoker" \
  --region us-central1
```

### 5.2 Configurar políticas de seguridad de Cloud Armor (opcional)

```bash
# Crear política de seguridad de Cloud Armor
gcloud compute security-policies create barberia-security-policy \
  --description "Política de seguridad para Barber Brothers"

# Agregar reglas de seguridad
gcloud compute security-policies rules create 1000 \
  --security-policy barberia-security-policy \
  --description "Bloquear países no deseados" \
  --expression "origin.region_code != 'CO'" \
  --action "deny-403"
```

## 6. Monitoreo y diagnóstico

### 6.1 Configurar alertas de Cloud Monitoring

```bash
# Crear alerta para latencia alta
gcloud alpha monitoring policies create \
  --display-name="Alerta de latencia alta" \
  --condition-display-name="Latencia > 2s" \
  --if="metric.type=\"run.googleapis.com/request_latencies\" resource.type=\"cloud_run_revision\" resource.labels.service_name=\"barberia-app\" metric.labels.response_code_class=\"2xx\" > 2000" \
  --duration="60s" \
  --notification-channels="email:jrovezdev11@gmail.com"

# Crear alerta para errores 5xx
gcloud alpha monitoring policies create \
  --display-name="Alerta de errores 5xx" \
  --condition-display-name="Errores 5xx" \
  --if="metric.type=\"run.googleapis.com/request_count\" resource.type=\"cloud_run_revision\" resource.labels.service_name=\"barberia-app\" metric.labels.response_code_class=\"5xx\" > 5" \
  --duration="60s" \
  --notification-channels="email:jrovezdev11@gmail.com"
```

### 6.2 Uso de scripts de diagnóstico

Utiliza los scripts creados para verificar el estado del sistema:

```bash
# Verificar estado de salud
python scripts/health_check.py

# Verificar recursos en GCP
python scripts/check_gcp_resources.py
```

### 6.3 Configuración de logs

```bash
# Ver logs del servicio
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=barberia-app" --limit=50
```

## 7. Mantenimiento continuo

### 7.1 Actualización de dependencias

Mantén actualizado el archivo requirements.txt y realiza pruebas antes de desplegar:

```bash
# Actualizar dependencias
pip install -U -r requirements.txt

# Actualizar archivo
pip freeze > requirements.txt
```

### 7.2 Escalado de recursos

Monitorea el uso de recursos y ajusta según sea necesario:

```bash
# Escalar memoria
gcloud run services update barberia-app \
  --memory 1Gi \
  --region us-central1

# Escalar CPU
gcloud run services update barberia-app \
  --cpu 2 \
  --region us-central1

# Ajustar instancias máximas
gcloud run services update barberia-app \
  --max-instances 20 \
  --region us-central1
```

## 8. Verificación final

Usa la siguiente lista de verificación para asegurar que todo esté correctamente implementado:

- [ ] Servicio Cloud Run operativo
- [ ] Base de datos Cloud SQL configurada
- [ ] Migraciones aplicadas correctamente
- [ ] VPC Connector activo y funcionando
- [ ] Secret Manager con todas las credenciales
- [ ] Cloud Storage configurado para uploads
- [ ] CI/CD funcionando con Cloud Build
- [ ] Monitoreo y alertas configurados
- [ ] Health check respondiendo correctamente

Para automatizar esta verificación:

```bash
python scripts/check_gcp_resources.py --verbose
```

## 9. Resolución de problemas comunes

### 9.1 Problemas de conexión a la base de datos

Si hay problemas conectando a Cloud SQL:

1. Verifica que la instancia esté en estado "RUNNABLE"
2. Confirma que el servicio Cloud Run esté configurado con `--add-cloudsql-instances`
3. Verifica que el VPC Connector esté correctamente configurado
4. Comprueba las credenciales en Secret Manager

```bash
# Verificar estado de la instancia
gcloud sql instances describe barberia-db --format="value(state)"

# Verificar configuración del servicio
gcloud run services describe barberia-app --region us-central1 \
  --format="yaml" | grep -A 5 cloudsql
```

### 9.2 Problemas con almacenamiento de archivos

Si hay problemas subiendo archivos:

1. Verifica que el bucket exista
2. Confirma que la variable de entorno `GCS_BUCKET_NAME` esté correctamente configurada
3. Verifica los permisos del bucket

```bash
# Verificar existencia del bucket
gcloud storage ls

# Verificar permisos del bucket
gcloud storage buckets get-iam-policy gs://barberia-uploads
```

### 9.3 Problemas de despliegue

Si hay problemas con el despliegue:

1. Verifica los logs de Cloud Build
2. Comprueba los logs del servicio Cloud Run
3. Intenta un despliegue manual

```bash
# Ver logs de Cloud Build
gcloud builds list --filter="source.repo_source.repo_name:barber-brothers"
gcloud builds log [BUILD_ID]

# Ver logs de Cloud Run
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=barberia-app" --limit=50
```

---

Este documento proporciona una guía completa para implementar y mantener la aplicación Barber Brothers en GCP. Sigue estos pasos cuidadosamente para asegurar un despliegue exitoso y un sistema robusto y confiable.
