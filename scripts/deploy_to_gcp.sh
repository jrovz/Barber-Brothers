#!/bin/bash
# Script para desplegar la aplicación en GCP Cloud Run con conexión a PostgreSQL

# Variables de configuración
PROJECT_ID="barber-brothers-460514"
REGION="us-east1"
SERVICE_NAME="barberia-app"
INSTANCE_NAME="barberia-db"
DB_NAME="barberia-db"
DB_USER="barberia-db"
DB_PASS="y3WhoYFS" # Deberías cambiar esto a tu contraseña real

# Nombres completos
INSTANCE_CONNECTION_NAME="${PROJECT_ID}:${REGION}:${INSTANCE_NAME}"

echo "=== Desplegando la aplicación en Cloud Run con conexión a PostgreSQL ==="
echo "Proyecto: $PROJECT_ID"
echo "Región: $REGION"
echo "Instancia SQL: $INSTANCE_CONNECTION_NAME"

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

# Construir y desplegar la aplicación en Cloud Run
echo "Construyendo y desplegando la aplicación en Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --platform=managed \
  --region=$REGION \
  --allow-unauthenticated \
  --add-cloudsql-instances=$INSTANCE_CONNECTION_NAME \
  --set-env-vars="INSTANCE_CONNECTION_NAME=$INSTANCE_CONNECTION_NAME" \
  --set-env-vars="DB_ENGINE=postgresql" \
  --set-env-vars="DB_NAME=$DB_NAME" \
  --set-env-vars="DB_USER=$DB_USER" \
  --set-env-vars="DB_PASS=$DB_PASS" \
  --set-env-vars="FLASK_ENV=production" \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID" \
  --source=.

# Verificar si el despliegue fue exitoso
if [ $? -eq 0 ]; then
    echo "✅ Aplicación desplegada exitosamente."
    echo "Para migrar la base de datos, ejecuta:"
    echo "gcloud run jobs create barberia-migrations --image=\$(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(spec.template.spec.containers[0].image)') --set-env-vars=FLASK_APP=wsgi.py --command=python --args=-m,flask,db,upgrade --region=$REGION --add-cloudsql-instances=$INSTANCE_CONNECTION_NAME"
    echo "gcloud run jobs execute barberia-migrations --region=$REGION"
else
    echo "❌ Error al desplegar la aplicación."
fi
