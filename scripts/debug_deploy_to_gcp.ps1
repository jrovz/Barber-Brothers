# Script para desplegar la aplicación en GCP Cloud Run con mejor soporte de depuración

# Importar la configuración
. "$PSScriptRoot\deploy_config.ps1"

Write-Host "=== Desplegando la aplicación en Cloud Run con modo de depuración activado ===" -ForegroundColor Green
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

# Implementar la aplicación en modo de depuración
Write-Host "Construyendo y desplegando la aplicación en Cloud Run con log level DEBUG..." -ForegroundColor Yellow

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
  --set-env-vars="FLASK_DEBUG=1" `
  --set-env-vars="FLASK_DEBUG_GCP=True" `
  --set-env-vars="LOG_LEVEL=DEBUG" `
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
    Write-Host "✅ Aplicación desplegada exitosamente en modo depuración." -ForegroundColor Green
    
    # Obtener la URL del servicio desplegado
    $serviceUrl = gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)'
    Write-Host "🌐 URL del servicio: $serviceUrl" -ForegroundColor Green
    
    # Ver los logs para depuración
    Write-Host "Para ver los logs del servicio, ejecuta:" -ForegroundColor Yellow
    Write-Host "gcloud logging read 'resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME' --limit=50 --format='json'" -ForegroundColor Cyan
} else {
    Write-Host "❌ Error al desplegar la aplicación." -ForegroundColor Red
    
    # Instrucciones para depuración
    Write-Host "Para obtener más información sobre el error, ejecuta:" -ForegroundColor Yellow
    Write-Host "gcloud builds list --filter='status=FAILURE' --limit=1" -ForegroundColor Cyan
    Write-Host "Y luego para ver los logs detallados del build fallido:" -ForegroundColor Yellow
    Write-Host "gcloud builds log \$(gcloud builds list --filter='status=FAILURE' --limit=1 --format='value(id)')" -ForegroundColor Cyan
}
