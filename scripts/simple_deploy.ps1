# Script para desplegar la aplicación en GCP con un solo comando

# Importar la configuración
. "$PSScriptRoot\deploy_config.ps1"

Write-Host "=== Desplegando la aplicación en Cloud Run con configuración simplificada ===" -ForegroundColor Green
Write-Host "Proyecto: $PROJECT_ID"
Write-Host "Región Cloud Run: $REGION"
Write-Host "Región Cloud SQL: $DB_REGION"
Write-Host "Instancia SQL: $INSTANCE_NAME"
Write-Host "Conexión completa: $INSTANCE_CONNECTION_NAME"

# Construir el comando como una sola línea
$deployCommand = "gcloud run deploy $SERVICE_NAME --platform=managed --region=$REGION --allow-unauthenticated --add-cloudsql-instances=$INSTANCE_CONNECTION_NAME --set-env-vars=""INSTANCE_CONNECTION_NAME=$INSTANCE_CONNECTION_NAME,DB_ENGINE=postgresql,DB_NAME=$DB_NAME,DB_USER=$DB_USER,DB_PASS=$DB_PASS,FLASK_ENV=production,GOOGLE_CLOUD_PROJECT=$PROJECT_ID,REGION=$DB_REGION,INSTANCE_NAME=$INSTANCE_NAME,FLASK_DEBUG=1,FLASK_DEBUG_GCP=True,LOG_LEVEL=DEBUG"" --cpu=1 --memory=512Mi --timeout=300 --source=.."

Write-Host "Ejecutando comando de despliegue:" -ForegroundColor Cyan
Write-Host $deployCommand -ForegroundColor Gray

# Ejecutar el comando
Invoke-Expression $deployCommand

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Aplicación desplegada exitosamente." -ForegroundColor Green
    
    # Obtener la URL del servicio
    $serviceUrl = gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)"
    Write-Host "🌐 URL del servicio: $serviceUrl" -ForegroundColor Green
    
    # Ver los logs para depuración
    Write-Host "Para ver los logs del servicio, ejecuta:" -ForegroundColor Yellow
    Write-Host "gcloud logging read 'resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME' --limit=50" -ForegroundColor Cyan
} else {
    Write-Host "❌ Error al desplegar la aplicación." -ForegroundColor Red
    Write-Host "Revisa los errores arriba y consulta la guía de solución de problemas." -ForegroundColor Yellow
}
