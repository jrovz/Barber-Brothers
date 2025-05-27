#!/bin/bash
# Script para configurar Secret Manager en GCP
# Este script configura Secret Manager con las credenciales y configuraciones necesarias

# Variables de configuración
PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-"barber-brothers-460514"}
REGION=${REGION:-"us-east1"}
DB_REGION=${DB_REGION:-$REGION}
INSTANCE_NAME=${INSTANCE_NAME:-"barberia-db"}

# Colores para mensajes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Configurando Secret Manager para Barber Brothers ===${NC}"
echo "Proyecto: $PROJECT_ID"

# Habilitar API de Secret Manager si no está habilitada
echo "Habilitando Secret Manager API..."
gcloud services enable secretmanager.googleapis.com

# Función para crear o actualizar un secreto
create_or_update_secret() {
    local secret_id=$1
    local secret_value=$2
    local description=$3

    # Verificar si el secreto ya existe
    if gcloud secrets describe $secret_id --project=$PROJECT_ID > /dev/null 2>&1; then
        echo -e "${YELLOW}El secreto $secret_id ya existe. ¿Deseas actualizarlo? (s/N)${NC}"
        read -r response
        if [[ "$response" =~ ^([sS][iI]|[sS])$ ]]; then
            echo "$secret_value" | gcloud secrets versions add $secret_id --data-file=- --project=$PROJECT_ID
            echo -e "${GREEN}✅ Secreto $secret_id actualizado correctamente.${NC}"
        else
            echo -e "${YELLOW}⚠️ El secreto $secret_id no fue modificado.${NC}"
        fi
    else
        echo "Creando secreto $secret_id..."
        echo "$secret_value" | gcloud secrets create $secret_id --data-file=- --project=$PROJECT_ID --replication-policy="automatic"
        echo -e "${GREEN}✅ Secreto $secret_id creado correctamente.${NC}"
    fi
}

# Solicitar credenciales de base de datos al usuario
echo -e "${YELLOW}Por favor, ingresa las credenciales para la base de datos:${NC}"

# Usuario de la base de datos
echo -n "Usuario de la base de datos (default: barberia_user): "
read -r db_user
db_user=${db_user:-"barberia_user"}

# Contraseña de la base de datos
echo -n "Contraseña de la base de datos: "
read -rs db_pass
echo
if [ -z "$db_pass" ]; then
    echo -e "${RED}⚠️ La contraseña no puede estar vacía. Por favor, ingresa una contraseña.${NC}"
    exit 1
fi

# Nombre de la base de datos
echo -n "Nombre de la base de datos (default: barberia_db): "
read -r db_name
db_name=${db_name:-"barberia_db"}

# Crear secretos para credenciales de base de datos
echo -e "\n${GREEN}Configurando secretos para la base de datos...${NC}"
create_or_update_secret "db_user" "$db_user" "Usuario de la base de datos PostgreSQL"
create_or_update_secret "db_pass" "$db_pass" "Contraseña de la base de datos PostgreSQL"
create_or_update_secret "db_name" "$db_name" "Nombre de la base de datos PostgreSQL"

# Secreto para la clave secreta de la aplicación
echo -e "\n${YELLOW}¿Deseas configurar una clave secreta para la aplicación? (s/N)${NC}"
read -r response
if [[ "$response" =~ ^([sS][iI]|[sS])$ ]]; then
    # Generar una clave secreta aleatoria
    secret_key=$(openssl rand -base64 32)
    create_or_update_secret "secret_key" "$secret_key" "Clave secreta para la aplicación Flask"
fi

# Configuración de correo electrónico
echo -e "\n${YELLOW}¿Deseas configurar las credenciales de correo electrónico? (s/N)${NC}"
read -r response
if [[ "$response" =~ ^([sS][iI]|[sS])$ ]]; then
    echo -n "Servidor SMTP (default: smtp.gmail.com): "
    read -r mail_server
    mail_server=${mail_server:-"smtp.gmail.com"}
    
    echo -n "Puerto SMTP (default: 587): "
    read -r mail_port
    mail_port=${mail_port:-"587"}
    
    echo -n "Usar TLS (True/false, default: True): "
    read -r mail_use_tls
    mail_use_tls=${mail_use_tls:-"True"}
    
    echo -n "Usuario de correo: "
    read -r mail_username
    
    echo -n "Contraseña de correo: "
    read -rs mail_password
    echo
    
    echo -n "Nombre del remitente (default: Barber Brothers): "
    read -r mail_sender
    mail_sender=${mail_sender:-"Barber Brothers"}
    
    # Crear secretos para el correo electrónico
    echo -e "\n${GREEN}Configurando secretos para el correo electrónico...${NC}"
    create_or_update_secret "mail_server" "$mail_server" "Servidor SMTP"
    create_or_update_secret "mail_port" "$mail_port" "Puerto SMTP"
    create_or_update_secret "mail_use_tls" "$mail_use_tls" "Usar TLS para SMTP"
    create_or_update_secret "mail_username" "$mail_username" "Usuario de correo electrónico"
    create_or_update_secret "mail_password" "$mail_password" "Contraseña de correo electrónico"
    create_or_update_secret "mail_sender" "$mail_sender" "Nombre del remitente"
fi

# Guardar la configuración regional
echo -e "\n${GREEN}Configurando secretos para regiones...${NC}"
create_or_update_secret "region" "$REGION" "Región principal de GCP"
create_or_update_secret "db_region" "$DB_REGION" "Región de Cloud SQL"
create_or_update_secret "instance_name" "$INSTANCE_NAME" "Nombre de la instancia de Cloud SQL"

echo -e "\n${GREEN}=== Configuración de Secret Manager completada ===${NC}"
echo "Ahora puedes desplegar tu aplicación con estas credenciales seguras."
echo -e "Usa ${YELLOW}./scripts/deploy_to_gcp.sh${NC} para desplegar la aplicación."
