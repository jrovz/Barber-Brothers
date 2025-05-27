# Script para despliegue manual a Azure App Service
# Este script empaqueta la aplicación y la despliega a Azure App Service

param(
    [string]$ResourceGroup = "barberia-rg",
    [string]$AppName = "barberia-app"
)

Write-Host "Preparando despliegue para $AppName en $ResourceGroup" -ForegroundColor Green

# Verificar que estamos en la raíz del proyecto
if (-not (Test-Path "./app" -PathType Container)) {
    Write-Host "Error: Ejecuta este script desde la raíz del proyecto" -ForegroundColor Red
    exit 1
}

# Verificar si se ha iniciado sesión en Azure
try {
    $account = az account show | ConvertFrom-Json
    Write-Host "Autenticado como: $($account.user.name)" -ForegroundColor Green
}
catch {
    Write-Host "No se ha iniciado sesión en Azure. Ejecutando az login..." -ForegroundColor Yellow
    az login
}

# Crear directorio temporal
$tempDir = [System.IO.Path]::GetTempPath() + [System.Guid]::NewGuid().ToString()
New-Item -ItemType Directory -Path $tempDir | Out-Null

try {
    # Crear paquete de despliegue
    $deployZip = "$tempDir\deploy.zip"
    Write-Host "Creando paquete de despliegue en $deployZip..." -ForegroundColor Yellow
    
    # Copiar archivos al directorio temporal, excluyendo los no necesarios
    $excludeDirs = @(".git", ".github", ".pytest_cache", "__pycache__", "venv", "env")
    $excludeFiles = @("*.pyc", "azure-credentials.txt")
    
    # Copiar archivos
    Get-ChildItem -Path . -Recurse |
        Where-Object { 
            $item = $_
            -not ($excludeDirs | Where-Object { $item.FullName -like "*\$_\*" }) -and
            -not ($excludeFiles | Where-Object { $item.Name -like $_ })
        } |
        ForEach-Object {
            $targetPath = $_.FullName.Replace($PWD.Path, $tempDir)
            
            if ($_.PSIsContainer) {
                # Es un directorio
                if (-not (Test-Path $targetPath)) {
                    New-Item -ItemType Directory -Path $targetPath | Out-Null
                }
            } else {
                # Es un archivo
                $targetDir = Split-Path $targetPath -Parent
                if (-not (Test-Path $targetDir)) {
                    New-Item -ItemType Directory -Path $targetDir | Out-Null
                }
                Copy-Item $_.FullName -Destination $targetPath
            }
        }
    
    # Comprimir para el despliegue
    Compress-Archive -Path "$tempDir\*" -DestinationPath $deployZip -Force
    
    # Desplegar a Azure
    Write-Host "Desplegando a Azure App Service..." -ForegroundColor Yellow
    az webapp deployment source config-zip --resource-group $ResourceGroup --name $AppName --src $deployZip
    
    # Verificar estado del despliegue
    Write-Host "Verificando estado de la aplicación..." -ForegroundColor Yellow
    $status = az webapp show --resource-group $ResourceGroup --name $AppName --query state -o tsv
    
    if ($status -eq "Running") {
        Write-Host "Aplicación desplegada y ejecutándose en: https://$AppName.azurewebsites.net" -ForegroundColor Green
    } else {
        Write-Host "Aplicación desplegada pero su estado actual es: $status" -ForegroundColor Yellow
        Write-Host "Verifica el estado en: https://$AppName.azurewebsites.net" -ForegroundColor Yellow
    }
    
} finally {
    # Limpiar
    Write-Host "Limpiando archivos temporales..." -ForegroundColor Gray
    Remove-Item -Path $tempDir -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host "Proceso de despliegue completado" -ForegroundColor Green
