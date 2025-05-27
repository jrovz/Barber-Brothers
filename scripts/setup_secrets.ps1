# Script para configurar Secret Manager en GCP
# Este script configura Secret Manager con las credenciales y configuraciones necesarias

# Variables de configuración
$PROJECT_ID = $env:GOOGLE_CLOUD_PROJECT
if (-not $PROJECT_ID) {
    $PROJECT_ID = "barber-brothers-460514"
}

$REGION = $env:REGION
if (-not $REGION) {
    $REGION = "us-east1"
}

$DB_REGION = $env:DB_REGION
if (-not $DB_REGION) {
    $DB_REGION = $REGION
}

$INSTANCE_NAME = $env:INSTANCE_NAME
if (-not $INSTANCE_NAME) {
    $INSTANCE_NAME = "barberia-db"
}

Write-Host "=== Configurando Secret Manager para Barber Brothers ===" -ForegroundColor Green
Write-Host "Proyecto: $PROJECT_ID"

# Habilitar API de Secret Manager si no está habilitada
Write-Host "Habilitando Secret Manager API..."
gcloud services enable secretmanager.googleapis.com

# Función para crear o actualizar un secreto
function Create-Or-Update-Secret {
    param (
        [string]$secretId,
        [string]$secretValue,
        [string]$description
    )

    # Verificar si el secreto ya existe
    $secretExists = $null
    try {
        $secretExists = gcloud secrets describe $secretId --project=$PROJECT_ID 2>$null
    }
    catch {}

    if ($secretExists) {
        Write-Host "El secreto $secretId ya existe. ¿Deseas actualizarlo? (s/N)" -ForegroundColor Yellow
        $response = Read-Host
        if ($response -eq "s" -or $response -eq "S" -or $response -eq "si" -or $response -eq "SI") {
            $secretValue | gcloud secrets versions add $secretId --data-file=- --project=$PROJECT_ID
            Write-Host "✅ Secreto $secretId actualizado correctamente." -ForegroundColor Green
        }
        else {
            Write-Host "⚠️ El secreto $secretId no fue modificado." -ForegroundColor Yellow
        }
    }
    else {
        Write-Host "Creando secreto $secretId..."
        $secretValue | gcloud secrets create $secretId --data-file=- --project=$PROJECT_ID --replication-policy="automatic"
        Write-Host "✅ Secreto $secretId creado correctamente." -ForegroundColor Green
    }
}

# Solicitar credenciales de base de datos al usuario
Write-Host "Por favor, ingresa las credenciales para la base de datos:" -ForegroundColor Yellow

# Usuario de la base de datos
$db_user = Read-Host "Usuario de la base de datos (default: barberia_user)"
if (-not $db_user) {
    $db_user = "barberia_user"
}

# Contraseña de la base de datos
$securePass = Read-Host "Contraseña de la base de datos" -AsSecureString
$BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePass)
$db_pass = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
if (-not $db_pass) {
    Write-Host "⚠️ La contraseña no puede estar vacía. Por favor, ingresa una contraseña." -ForegroundColor Red
    exit 1
}

# Nombre de la base de datos
$db_name = Read-Host "Nombre de la base de datos (default: barberia_db)"
if (-not $db_name) {
    $db_name = "barberia_db"
}

# Crear secretos para credenciales de base de datos
Write-Host "`nConfigurando secretos para la base de datos..." -ForegroundColor Green
Create-Or-Update-Secret "db_user" $db_user "Usuario de la base de datos PostgreSQL"
Create-Or-Update-Secret "db_pass" $db_pass "Contraseña de la base de datos PostgreSQL"
Create-Or-Update-Secret "db_name" $db_name "Nombre de la base de datos PostgreSQL"

# Secreto para la clave secreta de la aplicación
Write-Host "`n¿Deseas configurar una clave secreta para la aplicación? (s/N)" -ForegroundColor Yellow
$response = Read-Host
if ($response -eq "s" -or $response -eq "S" -or $response -eq "si" -or $response -eq "SI") {
    # Generar una clave secreta aleatoria
    $random = New-Object System.Security.Cryptography.RNGCryptoServiceProvider
    $bytes = New-Object byte[](32)
    $random.GetBytes($bytes)
    $secret_key = [Convert]::ToBase64String($bytes)
    Create-Or-Update-Secret "secret_key" $secret_key "Clave secreta para la aplicación Flask"
}

# Configuración de correo electrónico
Write-Host "`n¿Deseas configurar las credenciales de correo electrónico? (s/N)" -ForegroundColor Yellow
$response = Read-Host
if ($response -eq "s" -or $response -eq "S" -or $response -eq "si" -or $response -eq "SI") {
    $mail_server = Read-Host "Servidor SMTP (default: smtp.gmail.com)"
    if (-not $mail_server) {
        $mail_server = "smtp.gmail.com"
    }
    
    $mail_port = Read-Host "Puerto SMTP (default: 587)"
    if (-not $mail_port) {
        $mail_port = "587"
    }
    
    $mail_use_tls = Read-Host "Usar TLS (True/false, default: True)"
    if (-not $mail_use_tls) {
        $mail_use_tls = "True"
    }
    
    $mail_username = Read-Host "Usuario de correo"
    
    $mail_password_secure = Read-Host "Contraseña de correo" -AsSecureString
    $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($mail_password_secure)
    $mail_password = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
    
    $mail_sender = Read-Host "Nombre del remitente (default: Barber Brothers)"
    if (-not $mail_sender) {
        $mail_sender = "Barber Brothers"
    }
    
    # Crear secretos para el correo electrónico
    Write-Host "`nConfigurando secretos para el correo electrónico..." -ForegroundColor Green
    Create-Or-Update-Secret "mail_server" $mail_server "Servidor SMTP"
    Create-Or-Update-Secret "mail_port" $mail_port "Puerto SMTP"
    Create-Or-Update-Secret "mail_use_tls" $mail_use_tls "Usar TLS para SMTP"
    Create-Or-Update-Secret "mail_username" $mail_username "Usuario de correo electrónico"
    Create-Or-Update-Secret "mail_password" $mail_password "Contraseña de correo electrónico"
    Create-Or-Update-Secret "mail_sender" $mail_sender "Nombre del remitente"
}

# Guardar la configuración regional
Write-Host "`nConfigurando secretos para regiones..." -ForegroundColor Green
Create-Or-Update-Secret "region" $REGION "Región principal de GCP"
Create-Or-Update-Secret "db_region" $DB_REGION "Región de Cloud SQL"
Create-Or-Update-Secret "instance_name" $INSTANCE_NAME "Nombre de la instancia de Cloud SQL"

Write-Host "`n=== Configuración de Secret Manager completada ===" -ForegroundColor Green
Write-Host "Ahora puedes desplegar tu aplicación con estas credenciales seguras."
Write-Host "Usa .\scripts\deploy_to_gcp.ps1 para desplegar la aplicación." -ForegroundColor Yellow
