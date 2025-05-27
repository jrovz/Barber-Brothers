#!/bin/bash
# Script para preparar la aplicación durante el despliegue en Azure App Service

echo "Preparing Barberia App for deployment on Azure..."

# Asegurar que los scripts sean ejecutables
chmod +x startup-azure.sh
chmod +x setup_db_azure.py

# Crear la estructura de directorios necesaria
mkdir -p app/static/uploads
mkdir -p logs

# Crear un archivo .env vacío para configurar con variables de entorno de App Service
touch .env

echo "Deployment preparation completed successfully."
