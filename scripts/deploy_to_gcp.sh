#!/bin/bash
# Script para desplegar la aplicación en GCP Cloud Run con conexión a PostgreSQL

# Variables de configuración
PROJECT_ID="barber-brothers-460514"
REGION="us-east1"
SERVICE_NAME="barberia-app"
INSTANCE_NAME="barberia-db"
DB_NAME="barberia-db"
# Dejamos vacías las credenciales para usar Secret Manager
DB_USER=""
DB_PASS=""

# Nombres completos
INSTANCE_CONNECTION_NAME="${PROJECT_ID}:${REGION}:${INSTANCE_NAME}"

echo "=== Desplegando la aplicación en Cloud Run con conexión a PostgreSQL ==="
echo "Proyecto: $PROJECT_ID"
echo "Región: $REGION"
echo "Instancia SQL: $INSTANCE_CONNECTION_NAME"
echo "Credenciales: Se usarán desde Secret Manager"

# Asegurarse de que las APIs necesarias estén habilitadas
echo "Habilitando APIs necesarias..."
gcloud services enable run.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable secretmanager.googleapis.com

# Verificar que la instancia de Cloud SQL existe
echo "Verificando instancia de Cloud SQL..."
if gcloud sql instances describe $INSTANCE_NAME --project=$PROJECT_ID > /dev/null 2>&1; then
    echo "La instancia $INSTANCE_NAME ya existe."
else
    echo "ERROR: La instancia $INSTANCE_NAME no existe. Debes crearla primero."
    exit 1
fi

# Verificar que los secretos existen
echo "Verificando secretos en Secret Manager..."
SECRET_EXISTS=0
if gcloud secrets describe db_user --project=$PROJECT_ID > /dev/null 2>&1; then
    echo "✅ Secreto db_user encontrado."
    SECRET_EXISTS=1
fi

if gcloud secrets describe db_pass --project=$PROJECT_ID > /dev/null 2>&1; then
    echo "✅ Secreto db_pass encontrado."
    SECRET_EXISTS=1
fi

if gcloud secrets describe db_name --project=$PROJECT_ID > /dev/null 2>&1; then
    echo "✅ Secreto db_name encontrado."
    SECRET_EXISTS=1
fi

if [ $SECRET_EXISTS -eq 0 ]; then
    echo "⚠️ No se encontraron secretos en Secret Manager. Se usarán variables de entorno."
fi

# Construir y desplegar la aplicación en Cloud Run
echo "Construyendo y desplegando la aplicación en Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --platform=managed \
  --region=$REGION \
  --allow-unauthenticated \
  --add-cloudsql-instances=$INSTANCE_CONNECTION_NAME \
  --set-env-vars="INSTANCE_CONNECTION_NAME=$INSTANCE_CONNECTION_NAME" \
  --set-env-vars="DB_ENGINE=postgresql" \
  --set-env-vars="REGION=$REGION" \
  --set-env-vars="DB_REGION=$REGION" \
  --set-env-vars="INSTANCE_NAME=$INSTANCE_NAME" \
  --set-env-vars="FLASK_ENV=production" \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID" \
  --set-secrets="db_user=db_user:latest" \
  --set-secrets="db_pass=db_pass:latest" \
  --set-secrets="db_name=db_name:latest" \
  --source=.

# Verificar si el despliegue fue exitoso
if [ $? -eq 0 ]; then
    echo "✅ Aplicación desplegada exitosamente."
    echo "Para migrar la base de datos, ejecuta:"
    echo "gcloud run jobs create barberia-migrations --image=\$(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(spec.template.spec.containers[0].image)') --set-env-vars=FLASK_APP=wsgi.py --command=python --args=-m,flask,db,upgrade --region=$REGION --add-cloudsql-instances=$INSTANCE_CONNECTION_NAME --set-secrets=db_user=db_user:latest --set-secrets=db_pass=db_pass:latest --set-secrets=db_name=db_name:latest"
    echo "gcloud run jobs execute barberia-migrations --region=$REGION"
else
    echo "❌ Error al desplegar la aplicación."
fi
