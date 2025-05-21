# Guía de Despliegue en Google Cloud Platform (GCP)

Esta guía detalla los pasos necesarios para desplegar la aplicación web de Barber Brothers en GCP, utilizando Cloud Run, Cloud SQL y otros servicios relacionados.

## Índice

1. [Arquitectura de la Solución](#1-arquitectura-de-la-solución)
2. [Preparación del Entorno Local](#2-preparación-del-entorno-local)
3. [Configuración de Google Cloud Platform](#3-configuración-de-google-cloud-platform)
4. [Configuración de Base de Datos (Cloud SQL)](#4-configuración-de-base-de-datos-cloud-sql)
5. [Configuración de Almacenamiento de Archivos (Cloud Storage)](#5-configuración-de-almacenamiento-de-archivos-cloud-storage)
6. [Configuración de Secretos y Variables de Entorno](#6-configuración-de-secretos-y-variables-de-entorno)
7. [Despliegue de la Aplicación (Cloud Run)](#7-despliegue-de-la-aplicación-cloud-run)
8. [Configuración de Migraciones de Base de Datos](#8-configuración-de-migraciones-de-base-de-datos)
9. [Implementación de CI/CD con Cloud Build](#9-implementación-de-cicd-con-cloud-build)
10. [Monitoreo y Logging](#10-monitoreo-y-logging)
11. [Seguridad y Mejores Prácticas](#11-seguridad-y-mejores-prácticas)
12. [Solución de Problemas](#12-solución-de-problemas)

## 1. Arquitectura de la Solución

La arquitectura propuesta para el despliegue de la aplicación Barber Brothers en GCP se basa en los siguientes servicios:

- **Cloud Run**: Servicio sin servidor para ejecutar contenedores que escala automáticamente según la demanda.
- **Cloud SQL**: Base de datos PostgreSQL totalmente administrada.
- **Secret Manager**: Almacenamiento seguro de credenciales y variables sensibles.
- **Cloud Storage**: Almacenamiento de archivos estáticos y uploads de imágenes.
- **Cloud Logging**: Registro centralizado de logs de la aplicación.
- **Cloud Monitoring**: Monitoreo del rendimiento y disponibilidad.
- **Cloud Build**: Automatización de CI/CD para despliegue continuo.

### Diagrama de Arquitectura

```
Cliente Web/Móvil
       |
       ↓
     Cloud Run ←→ Secret Manager
    /    |      \
   ↓     ↓       ↓
Cloud SQL  Cloud Storage  Cloud Logging/Monitoring
```

Esta arquitectura ofrece:
- Alta disponibilidad y escalabilidad
- Costos optimizados (pago por uso)
- Seguridad integrada
- Facilidad de mantenimiento

## 2. Preparación del Entorno Local

### 2.1. Requisitos Previos

- Python 3.x instalado
- Docker instalado
- Cliente de Google Cloud SDK instalado
- Cuenta de Google Cloud con un proyecto creado y facturación habilitada

### 2.2. Instalación de Google Cloud SDK

1. Descargar e instalar Google Cloud SDK desde: https://cloud.google.com/sdk/docs/install
2. Autenticación con Google Cloud:

```powershell
gcloud auth login
gcloud config set project <PROJECT_ID>
```

### 2.3. Configuración de Docker

Asegúrate de que Docker esté configurado para trabajar con Google Container Registry:

```powershell
gcloud auth configure-docker
```

## 3. Configuración de Google Cloud Platform

### 3.1. Habilitar APIs Necesarias

```powershell
gcloud services enable sqladmin.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable logging.googleapis.com
gcloud services enable monitoring.googleapis.com
```

### 3.2. Estructura de Archivos para Despliegue

Los siguientes archivos deben estar presentes en tu proyecto:

- **Dockerfile**: Configuración para containerizar la aplicación
- **requirements.txt**: Dependencias de la aplicación
- **.dockerignore**: Archivos a excluir del contenedor
- **cloudbuild.yaml**: Configuración para CI/CD
- **app.yaml**: Configuración para despliegue en GCP (opcional)

## 4. Configuración de Base de Datos (Cloud SQL)

### 4.1. Crear Instancia de Cloud SQL

```powershell
gcloud sql instances create barberia-db `
  --database-version=POSTGRES_15 `
  --cpu=1 `
  --memory=4GB `
  --region=us-central1 `
  --root-password="<MASTER_PASSWORD>" `
  --storage-type=SSD `
  --storage-size=10
```

### 4.2. Crear Base de Datos y Usuario

```powershell
# Crear la base de datos
gcloud sql databases create barberia_db --instance=barberia-db

# Crear usuario para la aplicación
gcloud sql users create barberia_user --instance=barberia-db --password="<USER_PASSWORD>"
```

### 4.3. Configuración de Conexión desde la Aplicación

La aplicación se conectará a Cloud SQL utilizando el módulo `cloud_connection.py` que implementamos, el cual utiliza el Cloud SQL Python Connector para establecer conexiones seguras.

## 5. Configuración de Almacenamiento de Archivos (Cloud Storage)

### 5.1. Crear Bucket para Archivos Estáticos y Uploads

```powershell
gcloud storage buckets create gs://barberia-uploads --location=us-central1 --uniform-bucket-level-access

# Hacer el bucket públicamente accesible para lectura
gcloud storage buckets add-iam-policy-binding gs://barberia-uploads --member=allUsers --role=roles/storage.objectViewer
```

### 5.2. Configuración de la Aplicación para Usar Cloud Storage

La aplicación utilizará el módulo `cloud_storage.py` que implementamos para gestionar la carga y descarga de archivos.

## 6. Configuración de Secretos y Variables de Entorno

### 6.1. Almacenar Secretos en Secret Manager

```powershell
# Credenciales de base de datos
echo "barberia_user" | gcloud secrets create db_user --data-file=-
echo "<USER_PASSWORD>" | gcloud secrets create db_pass --data-file=-
echo "barberia_db" | gcloud secrets create db_name --data-file=-

# Clave secreta de la aplicación
echo "<SECRET_KEY>" | gcloud secrets create secret_key --data-file=-

# Configuración de email
echo "smtp.gmail.com" | gcloud secrets create mail_server --data-file=-
echo "587" | gcloud secrets create mail_port --data-file=-
echo "True" | gcloud secrets create mail_use_tls --data-file=-
echo "<MAIL_USERNAME>" | gcloud secrets create mail_username --data-file=-
echo "<MAIL_PASSWORD>" | gcloud secrets create mail_password --data-file=-
echo "Barber Brothers" | gcloud secrets create mail_sender --data-file=-
```

### 6.2. Variables de Entorno en Cloud Run

Las variables de entorno se configurarán durante el despliegue en Cloud Run, incluyendo:

- `FLASK_ENV=production`
- `INSTANCE_CONNECTION_NAME=<PROJECT_ID>:us-central1:barberia-db`
- `GCS_BUCKET_NAME=barberia-uploads`

## 7. Despliegue de la Aplicación (Cloud Run)

### 7.1. Construcción de la Imagen Docker

```powershell
# Navegar al directorio del proyecto
cd "ruta/al/proyecto"

# Construir la imagen
docker build -t gcr.io/<PROJECT_ID>/barberia-app:v1 .

# Publicar la imagen en Container Registry
docker push gcr.io/<PROJECT_ID>/barberia-app:v1
```

### 7.2. Despliegue en Cloud Run

```powershell
gcloud run deploy barberia-app `
  --image gcr.io/<PROJECT_ID>/barberia-app:v1 `
  --platform managed `
  --region us-central1 `
  --allow-unauthenticated `
  --set-env-vars="FLASK_ENV=production" `
  --set-env-vars="INSTANCE_CONNECTION_NAME=<PROJECT_ID>:us-central1:barberia-db" `
  --set-env-vars="GCS_BUCKET_NAME=barberia-uploads" `
  --add-cloudsql-instances=<PROJECT_ID>:us-central1:barberia-db `
  --set-secrets="SECRET_KEY=secret_key:latest" `
  --set-secrets="MAIL_SERVER=mail_server:latest" `
  --set-secrets="MAIL_PORT=mail_port:latest" `
  --set-secrets="MAIL_USE_TLS=mail_use_tls:latest" `
  --set-secrets="MAIL_USERNAME=mail_username:latest" `
  --set-secrets="MAIL_PASSWORD=mail_password:latest" `
  --set-secrets="MAIL_DEFAULT_SENDER=mail_sender:latest"
```

## 8. Configuración de Migraciones de Base de Datos

### 8.1. Crear Job para Migraciones

```powershell
gcloud run jobs create barberia-migrations `
  --image gcr.io/<PROJECT_ID>/barberia-app:v1 `
  --tasks 1 `
  --set-env-vars="FLASK_APP=wsgi.py" `
  --command="python" `
  --args="-m","flask","db","upgrade" `
  --set-env-vars="INSTANCE_CONNECTION_NAME=<PROJECT_ID>:us-central1:barberia-db" `
  --set-env-vars="GCS_BUCKET_NAME=barberia-uploads" `
  --add-cloudsql-instances=<PROJECT_ID>:us-central1:barberia-db `
  --set-secrets="SECRET_KEY=secret_key:latest" `
  --region us-central1
```

### 8.2. Ejecutar Migraciones

```powershell
gcloud run jobs execute barberia-migrations --region us-central1
```

## 9. Implementación de CI/CD con Cloud Build

### 9.1. Configurar Trigger de Cloud Build

```powershell
gcloud builds triggers create github `
  --name="deploy-barberia-app" `
  --repo="<GITHUB_USER>/barber-brothers" `
  --branch-pattern="main" `
  --build-config="cloudbuild.yaml"
```

### 9.2. Archivo cloudbuild.yaml

El archivo `cloudbuild.yaml` creado anteriormente automatiza:
- Construcción de la imagen Docker
- Publicación en Container Registry
- Despliegue en Cloud Run
- Ejecución de migraciones de base de datos

## 10. Monitoreo y Logging

### 10.1. Configuración de Cloud Logging

La aplicación ya está configurada para enviar logs a Cloud Logging mediante el módulo `cloud_logging.py` que implementamos.

### 10.2. Configuración de Alertas

Puedes configurar alertas para:

```powershell
# Alerta para latencia alta
gcloud alpha monitoring policies create `
  --display-name="Alerta de latencia alta" `
  --condition-display-name="Latencia > 2s" `
  --condition-filter="resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"barberia-app\" AND metric.type = \"run.googleapis.com/request_latencies\" AND metric.labels.response_code_class = \"2xx\" AND metric.labels.quantile = \"99%\"" `
  --condition-threshold-value="2000" `
  --condition-threshold-filter="GREATER_THAN" `
  --condition-aggregations-alignmentPeriod="60s" `
  --condition-aggregations-crossSeriesReducer="REDUCE_PERCENTILE_99" `
  --condition-aggregations-perSeriesAligner="ALIGN_PERCENTILE_99" `
  --condition-duration="60s" `
  --notification-channels="email:<EMAIL>"
```

### 10.3. Dashboard Personalizado

Puedes crear un dashboard personalizado desde la consola web de GCP para visualizar métricas como:
- Tiempo de respuesta
- Solicitudes por minuto
- Errores
- Uso de CPU y memoria

## 11. Seguridad y Mejores Prácticas

### 11.1. Gestión de Secretos

- Utiliza Secret Manager para todas las credenciales y datos sensibles
- Evita hardcodear credenciales en el código
- Rota las credenciales regularmente

### 11.2. HTTPS y seguridad

- Cloud Run proporciona HTTPS por defecto
- Considera implementar Cloud Armor para protección adicional contra ataques
- Utiliza IAM para gestionar permisos de forma granular

### 11.3. Backup y Recuperación

Configura backups automáticos para Cloud SQL:

```powershell
gcloud sql instances patch barberia-db --backup-start-time="23:00"
```

## 12. Solución de Problemas

### 12.1. Ver Logs de la Aplicación

```powershell
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=barberia-app" --limit 50
```

### 12.2. Problemas de Conexión a Base de Datos

- Verifica que la instancia de Cloud SQL esté en ejecución
- Comprueba que los secretos estén correctamente configurados
- Verifica permisos y configuración de red

### 12.3. Problemas de Almacenamiento de Archivos

- Verifica permisos del bucket de Cloud Storage
- Comprueba la variable de entorno `GCS_BUCKET_NAME`
- Revisa los logs para errores relacionados con el almacenamiento

---

Para más información sobre los servicios de Google Cloud, consulta la documentación oficial:
- [Cloud Run](https://cloud.google.com/run/docs)
- [Cloud SQL](https://cloud.google.com/sql/docs)
- [Cloud Storage](https://cloud.google.com/storage/docs)
- [Secret Manager](https://cloud.google.com/secret-manager/docs)
- [Cloud Monitoring](https://cloud.google.com/monitoring/docs)
- [Cloud Build](https://cloud.google.com/build/docs)
