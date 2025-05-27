# Variables de configuración
$PROJECT_ID = "barber-brothers-460514"
$REGION = "us-east1"                  # Región para Cloud Run
$DB_REGION = "us-central1"            # Región para Cloud SQL
$SERVICE_NAME = "barberia-app"
$INSTANCE_NAME = "barberia-db"
$DB_NAME = "barberia-db"
$DB_USER = "postgres"  # Usuario por defecto de Postgres
$DB_PASS = "y3WhoYFS"  # Asegúrate de usar la contraseña correcta

# Nombre completo de la conexión
$INSTANCE_CONNECTION_NAME = "${PROJECT_ID}:${DB_REGION}:${INSTANCE_NAME}"

# Mostrar los valores para confirmación
Write-Host "=== Configuración de despliegue ===" -ForegroundColor Green
Write-Host "Proyecto: $PROJECT_ID"
Write-Host "Región: $REGION"
Write-Host "Servicio: $SERVICE_NAME"
Write-Host "Instancia SQL: $INSTANCE_NAME"
Write-Host "Conexión completa: $INSTANCE_CONNECTION_NAME"
