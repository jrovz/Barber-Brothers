# Script para obtener el perfil de publicación de Azure App Service
# Ejecutar desde PowerShell con permisos de administrador
# Debes tener instalada la CLI de Azure (az)

# Verificar que Azure CLI está instalado
try {
    $azVersion = az --version
    Write-Host "Azure CLI encontrado. Versión:" -ForegroundColor Green
    $azVersion[0]
}
catch {
    Write-Host "Azure CLI no está instalado. Por favor, instálalo desde: https://docs.microsoft.com/es-es/cli/azure/install-azure-cli" -ForegroundColor Red
    exit
}

# Iniciar sesión en Azure si no está autenticado
try {
    $accountInfo = az account show --output json | ConvertFrom-Json
    Write-Host "Ya has iniciado sesión como: $($accountInfo.user.name)" -ForegroundColor Green
}
catch {
    Write-Host "Iniciando sesión en Azure..." -ForegroundColor Yellow
    az login
    $accountInfo = az account show --output json | ConvertFrom-Json
}

# Mostrar suscripción actual
Write-Host "Suscripción actual: $($accountInfo.name) ($($accountInfo.id))" -ForegroundColor Cyan

# Preguntar si quiere usar esta suscripción
$usarSuscripcionActual = Read-Host "¿Quieres usar esta suscripción? (S/N)"
if ($usarSuscripcionActual -ne "S" -and $usarSuscripcionActual -ne "s") {
    # Mostrar todas las suscripciones
    Write-Host "Suscripciones disponibles:" -ForegroundColor Yellow
    az account list --query "[].{Name:name, Id:id, Default:isDefault}" --output table
    
    # Solicitar ID de suscripción
    $subscriptionId = Read-Host "Introduce el ID de la suscripción que quieres usar"
    az account set --subscription $subscriptionId
    $accountInfo = az account show --output json | ConvertFrom-Json
    Write-Host "Suscripción cambiada a: $($accountInfo.name)" -ForegroundColor Green
}
else {
    $subscriptionId = $accountInfo.id
}

# Obtener los App Services disponibles
Write-Host "Obteniendo App Services disponibles..." -ForegroundColor Yellow
$webApps = az webapp list --query "[].{Name:name, ResourceGroup:resourceGroup}" --output json | ConvertFrom-Json

if ($webApps.Count -eq 0) {
    Write-Host "No se encontraron aplicaciones web en esta suscripción." -ForegroundColor Red
    exit
}

# Mostrar App Services
Write-Host "App Services disponibles:" -ForegroundColor Cyan
for ($i = 0; $i -lt $webApps.Count; $i++) {
    Write-Host "[$i] $($webApps[$i].Name) (Grupo: $($webApps[$i].ResourceGroup))"
}

# Seleccionar App Service
$appIndex = Read-Host "Selecciona el número de la aplicación (por defecto: 0)"
if ($appIndex -eq "") { $appIndex = 0 }
$selectedApp = $webApps[$appIndex]

# Obtener el perfil de publicación
Write-Host "Obteniendo perfil de publicación para $($selectedApp.Name)..." -ForegroundColor Yellow
$profilePath = "azure_publish_profile.xml"
az webapp deployment list-publishing-profiles --name $selectedApp.Name --resource-group $selectedApp.ResourceGroup --xml > $profilePath

# Verificar que el archivo se ha creado correctamente
if (Test-Path $profilePath) {
    Write-Host "Perfil de publicación guardado en: $profilePath" -ForegroundColor Green
    
    # Mostrar instrucciones
    Write-Host "`n=== PRÓXIMOS PASOS ===" -ForegroundColor Green
    Write-Host "1. Ve a tu repositorio en GitHub." -ForegroundColor White
    Write-Host "2. Navega a Settings > Secrets and variables > Actions." -ForegroundColor White
    Write-Host "3. Haz clic en 'New repository secret'." -ForegroundColor White
    Write-Host "4. Nombre: AZURE_WEBAPP_PUBLISH_PROFILE" -ForegroundColor Cyan
    Write-Host "5. Valor: (Copia todo el contenido del archivo $profilePath)" -ForegroundColor Cyan
    Write-Host "6. Haz clic en 'Add secret'." -ForegroundColor White
    Write-Host "7. Ejecuta nuevamente el workflow desde la pestaña Actions de GitHub." -ForegroundColor White
    
    Write-Host "`nIMPORTANTE: El archivo $profilePath contiene credenciales sensibles. Elimínalo después de configurar el secreto en GitHub." -ForegroundColor Red
}
else {
    Write-Host "Error al obtener el perfil de publicación." -ForegroundColor Red
}
