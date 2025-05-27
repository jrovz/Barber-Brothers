# Script PowerShell para instalar dependencias necesarias para el proyecto Barber Brothers
# Este script instala todas las dependencias Python requeridas para los scripts del proyecto

Write-Host "Instalador de dependencias para Barber Brothers" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

# Lista de dependencias requeridas
$dependencies = @(
    "sqlalchemy",
    "pg8000",
    "google-cloud-secret-manager",
    "google-cloud-sql-connector",
    "werkzeug",
    "alembic",
    "flask",
    "flask-sqlalchemy",
    "gunicorn",
    "psycopg2-binary",
    "requests"
)

# Verificar si Python está instalado
try {
    $pythonVersion = python --version
    Write-Host "✅ Python detectado: $pythonVersion" -ForegroundColor Green
}
catch {
    Write-Host "❌ Python no encontrado. Por favor, instala Python antes de continuar." -ForegroundColor Red
    exit 1
}

# Función para verificar si un paquete está instalado
function Test-PythonPackage {
    param (
        [string]$PackageName
    )
    
    $result = python -c "import importlib.util; print(importlib.util.find_spec('$($PackageName -replace '-', '_')') is not None)" 2>$null
    
    if ($result -eq "True") {
        return $true
    }
    else {
        # Intentar método alternativo con pip list
        $pipList = pip list 2>$null
        foreach ($line in $pipList) {
            if ($line -match "^$PackageName ") {
                return $true
            }
        }
        return $false
    }
}

# Verificar dependencias
Write-Host "`nVerificando dependencias..." -ForegroundColor Cyan
$missingDependencies = @()

foreach ($dep in $dependencies) {
    if (Test-PythonPackage -PackageName $dep) {
        Write-Host "✅ $dep está instalado" -ForegroundColor Green
    }
    else {
        Write-Host "❌ $dep no está instalado" -ForegroundColor Red
        $missingDependencies += $dep
    }
}

# Instalar dependencias faltantes
if ($missingDependencies.Count -gt 0) {
    Write-Host "`nSe encontraron $($missingDependencies.Count) dependencias faltantes. Instalando..." -ForegroundColor Yellow
    
    foreach ($dep in $missingDependencies) {
        Write-Host "Instalando $dep..." -ForegroundColor Cyan
        python -m pip install $dep
        
        # Verificar instalación
        if (Test-PythonPackage -PackageName $dep) {
            Write-Host "✅ $dep instalado correctamente" -ForegroundColor Green
        }
        else {
            Write-Host "❌ Error al instalar $dep" -ForegroundColor Red
        }
    }
    
    Write-Host "`nInstalación de dependencias completa." -ForegroundColor Green
}
else {
    Write-Host "`n✅ Todas las dependencias necesarias ya están instaladas." -ForegroundColor Green
}

# Actualizar requirements.txt
$updateRequirements = Read-Host "`n¿Deseas actualizar el archivo requirements.txt con estas dependencias? (s/n)"
if ($updateRequirements -eq "s") {
    $requirementsPath = Join-Path $PSScriptRoot "..\requirements.txt"
    
    if (Test-Path $requirementsPath) {
        $currentRequirements = Get-Content $requirementsPath -Raw
        $newDependencies = @()
        
        foreach ($dep in $dependencies) {
            if ($currentRequirements -notmatch $dep) {
                $newDependencies += $dep
            }
        }
        
        if ($newDependencies.Count -gt 0) {
            Add-Content $requirementsPath "`n# Dependencias agregadas automáticamente"
            foreach ($dep in $newDependencies) {
                Add-Content $requirementsPath $dep
            }
            Write-Host "✅ Se agregaron $($newDependencies.Count) nuevas dependencias a requirements.txt" -ForegroundColor Green
        }
        else {
            Write-Host "✅ Todas las dependencias ya están en requirements.txt" -ForegroundColor Green
        }
    }
    else {
        Write-Host "❌ No se encontró el archivo requirements.txt" -ForegroundColor Red
    }
}

Write-Host "`nProceso completado. Ya puedes ejecutar los scripts del proyecto." -ForegroundColor Cyan
