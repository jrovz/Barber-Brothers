# Script para configurar Service Principal para GitHub Actions
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

# Obtener grupo de recursos
$resourceGroups = az group list --query "[].name" --output tsv
if ($resourceGroups) {
    Write-Host "Grupos de recursos disponibles:" -ForegroundColor Yellow
    $resourceGroups | ForEach-Object { Write-Host "- $_" }
    $resourceGroup = Read-Host "Introduce el nombre del grupo de recursos donde está la aplicación (por defecto: barberia-rg)"
    if (-not $resourceGroup) {
        $resourceGroup = "barberia-rg"
    }
}
else {
    Write-Host "No se encontraron grupos de recursos. Creando uno nuevo..." -ForegroundColor Yellow
    $resourceGroup = "barberia-rg"
    $location = "eastus"
    az group create --name $resourceGroup --location $location
}

# Crear Service Principal con permisos de colaborador en el grupo de recursos
Write-Host "Creando Service Principal para GitHub Actions..." -ForegroundColor Yellow
$spName = "barberia-app-github-" + (Get-Random -Maximum 99999)
$sp = az ad sp create-for-rbac --name $spName --role contributor --scopes /subscriptions/$subscriptionId/resourceGroups/$resourceGroup --output json | ConvertFrom-Json

# Mostrar información para GitHub Secrets
Write-Host "`n=== INFORMACIÓN PARA GITHUB SECRETS ===" -ForegroundColor Green
Write-Host "Configura estos secretos en GitHub (Settings > Secrets and variables > Actions):" -ForegroundColor Yellow
Write-Host "AZURE_CLIENT_ID: $($sp.appId)" -ForegroundColor Cyan
Write-Host "AZURE_TENANT_ID: $($sp.tenant)" -ForegroundColor Cyan
Write-Host "AZURE_SUBSCRIPTION_ID: $subscriptionId" -ForegroundColor Cyan
Write-Host "AZURE_CLIENT_SECRET: $($sp.password)" -ForegroundColor Cyan

# Guardar en un archivo
$secretsFile = "azure_github_secrets.txt"
@"
=== INFORMACIÓN PARA GITHUB SECRETS ===
AZURE_CLIENT_ID: $($sp.appId)
AZURE_TENANT_ID: $($sp.tenant)
AZURE_SUBSCRIPTION_ID: $subscriptionId
AZURE_CLIENT_SECRET: $($sp.password)

IMPORTANTE: Guarda esta información en un lugar seguro y elimina este archivo después de configurar los secretos.
"@ | Out-File -FilePath $secretsFile

Write-Host "`nLa información también se ha guardado en el archivo: $secretsFile" -ForegroundColor Yellow
Write-Host "IMPORTANTE: Elimina este archivo después de configurar los secretos en GitHub." -ForegroundColor Red

# Instrucciones finales
Write-Host "`n=== PRÓXIMOS PASOS ===" -ForegroundColor Green
Write-Host "1. Agrega estos secretos en tu repositorio de GitHub." -ForegroundColor White
Write-Host "2. Edita el archivo .github/workflows/azure-webapp-deploy.yml para usar estos secretos." -ForegroundColor White
Write-Host "3. Ejecuta nuevamente el workflow desde la pestaña Actions de GitHub." -ForegroundColor White
