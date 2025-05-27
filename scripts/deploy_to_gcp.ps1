# Script para desplegar la aplicación en GCP Cloud Run con conexión a PostgreSQL

# Importar la configuración
. "$PSScriptRoot\deploy_config.ps1"

Write-Host "=== Desplegando la aplicación en Cloud Run con conexión a PostgreSQL ===" -ForegroundColor Green
Write-Host "Proyecto: $PROJECT_ID"
Write-Host "Región Cloud Run: $REGION"
Write-Host "Región Cloud SQL: $DB_REGION"
Write-Host "Instancia SQL: $INSTANCE_NAME"
Write-Host "Conexión completa: $INSTANCE_CONNECTION_NAME"

# Asegurarse de que las APIs necesarias estén habilitadas
Write-Host "Habilitando APIs necesarias..." -ForegroundColor Yellow
gcloud services enable run.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable secretmanager.googleapis.com

# Verificar que la instancia de Cloud SQL existe
Write-Host "Verificando instancia de Cloud SQL..." -ForegroundColor Yellow
$instanceExists = $null
try {
    $instanceExists = gcloud sql instances describe $INSTANCE_NAME --project=$PROJECT_ID 2>$null
} catch {
    # No hacer nada, la variable seguirá siendo $null
}

if ($instanceExists) {
    Write-Host "La instancia $INSTANCE_NAME ya existe." -ForegroundColor Green
} else {
    Write-Host "ERROR: La instancia $INSTANCE_NAME no existe. Debes crearla primero." -ForegroundColor Red
    exit 1
}

# Construir y desplegar la aplicación en Cloud Run
Write-Host "Construyendo y desplegando la aplicación en Cloud Run..." -ForegroundColor Yellow

$deployCommand = @"
gcloud run deploy $SERVICE_NAME `
  --platform=managed `
  --region=$REGION `
  --allow-unauthenticated `
  --add-cloudsql-instances=$INSTANCE_CONNECTION_NAME `
  --set-env-vars="INSTANCE_CONNECTION_NAME=$INSTANCE_CONNECTION_NAME" `
  --set-env-vars="DB_ENGINE=postgresql" `
  --set-env-vars="DB_NAME=$DB_NAME" `
  --set-env-vars="DB_USER=$DB_USER" `
  --set-env-vars="DB_PASS=$DB_PASS" `
  --set-env-vars="FLASK_ENV=production" `
  --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID" `
  --set-env-vars="REGION=$DB_REGION" `
  --set-env-vars="INSTANCE_NAME=$INSTANCE_NAME" `
  --cpu=1 `
  --memory=512Mi `
  --timeout=300 `
  --source=..
"@

Write-Host "Ejecutando comando de despliegue:" -ForegroundColor Cyan
Write-Host $deployCommand -ForegroundColor Gray

# Ejecutar el comando de despliegue
Invoke-Expression $deployCommand

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Aplicación desplegada exitosamente." -ForegroundColor Green
    Write-Host "Para migrar la base de datos, ejecuta:" -ForegroundColor Yellow
    
    $imageUrl = gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(spec.template.spec.containers[0].image)'
    
    Write-Host "gcloud run jobs create barberia-migrations --image=$imageUrl --set-env-vars=FLASK_APP=wsgi.py --command=python --args=-m,flask,db,upgrade --region=$REGION --add-cloudsql-instances=$INSTANCE_CONNECTION_NAME" -ForegroundColor Cyan
    Write-Host "gcloud run jobs execute barberia-migrations --region=$REGION" -ForegroundColor Cyan
} else {
    Write-Host "❌ Error al desplegar la aplicación." -ForegroundColor Red
}
