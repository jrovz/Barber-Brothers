#!/bin/bash
# vpc_connector_setup.sh - Script para configurar un VPC Connector para Cloud Run

# Variables de configuración
PROJECT_ID="barber-brothers-460514"
REGION="us-central1"
VPC_NAME="barberia-vpc"
SUBNET_NAME="barberia-connector-subnet"
CONNECTOR_NAME="barberia-vpc-connector"
IP_RANGE="10.8.0.0/28"
SERVICE_NAME="barberia-app"

# Colores para los mensajes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Función para imprimir mensajes informativos
info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

# Función para imprimir advertencias
warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Función para imprimir errores
error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Función para verificar si un comando se ejecutó correctamente
check_result() {
    if [ $? -eq 0 ]; then
        info "$1"
    else
        error "$2"
        exit 1
    fi
}

# Verificar que gcloud esté instalado
if ! command -v gcloud &> /dev/null; then
    error "gcloud no está instalado. Por favor, instala Google Cloud SDK primero."
    exit 1
fi

# Asegurarse de que el usuario está autenticado y el proyecto configurado
info "Verificando autenticación de gcloud..."
gcloud auth list --filter=status:ACTIVE --format="value(account)" > /dev/null 2>&1
check_result "Usuario autenticado correctamente." "No se ha iniciado sesión en gcloud. Ejecuta 'gcloud auth login' primero."

info "Configurando proyecto: $PROJECT_ID"
gcloud config set project $PROJECT_ID
check_result "Proyecto configurado correctamente." "Error al configurar el proyecto."

# Habilitar las APIs necesarias
info "Habilitando APIs necesarias..."
gcloud services enable compute.googleapis.com vpcaccess.googleapis.com
check_result "APIs habilitadas correctamente." "Error al habilitar las APIs."

# Verificar si la red VPC ya existe
info "Verificando si la red VPC '$VPC_NAME' ya existe..."
if gcloud compute networks list --filter="name=$VPC_NAME" --format="get(name)" | grep -q "$VPC_NAME"; then
    info "La red VPC '$VPC_NAME' ya existe."
else
    info "Creando red VPC '$VPC_NAME'..."
    gcloud compute networks create $VPC_NAME --subnet-mode=custom
    check_result "Red VPC creada correctamente." "Error al crear la red VPC."
fi

# Verificar si la subnet ya existe
info "Verificando si la subnet '$SUBNET_NAME' ya existe..."
if gcloud compute networks subnets list --filter="name=$SUBNET_NAME" --format="get(name)" | grep -q "$SUBNET_NAME"; then
    info "La subnet '$SUBNET_NAME' ya existe."
else
    info "Creando subnet '$SUBNET_NAME'..."
    gcloud compute networks subnets create $SUBNET_NAME \
      --network=$VPC_NAME \
      --region=$REGION \
      --range=$IP_RANGE
    check_result "Subnet creada correctamente." "Error al crear la subnet."
fi

# Verificar si el VPC Connector ya existe
info "Verificando si el VPC Connector '$CONNECTOR_NAME' ya existe..."
if gcloud compute networks vpc-access connectors list --region=$REGION --filter="name:$CONNECTOR_NAME" --format="get(name)" | grep -q "$CONNECTOR_NAME"; then
    info "El VPC Connector '$CONNECTOR_NAME' ya existe."
else
    info "Creando VPC Connector '$CONNECTOR_NAME'..."
    gcloud compute networks vpc-access connectors create $CONNECTOR_NAME \
      --network=$VPC_NAME \
      --region=$REGION \
      --range=$IP_RANGE \
      --min-instances=2 \
      --max-instances=10
    check_result "VPC Connector creado correctamente." "Error al crear el VPC Connector."
fi

# Actualizar el servicio Cloud Run para usar el VPC Connector
info "Actualizando servicio Cloud Run '$SERVICE_NAME' para usar el VPC Connector..."
gcloud run services update $SERVICE_NAME \
  --vpc-connector=$CONNECTOR_NAME \
  --region=$REGION
check_result "Servicio Cloud Run actualizado correctamente." "Error al actualizar el servicio Cloud Run."

# Verificar el estado del VPC Connector
info "Verificando estado del VPC Connector..."
gcloud compute networks vpc-access connectors describe $CONNECTOR_NAME \
  --region=$REGION --format="yaml"

info "Configuración de VPC Connector completada exitosamente."
info "El servicio '$SERVICE_NAME' ahora está configurado para usar el VPC Connector '$CONNECTOR_NAME'."
info "Esto permitirá conexiones seguras a Cloud SQL y otros servicios a través de la red privada."
