#!/bin/bash
# Script de inicio para Azure App Service (Plan F1 - Económico)

echo "Starting Barberia App service on Azure App Service (Economic Plan)..."
echo "Environment variables:"
echo "- DB_USER: $DB_USER"
echo "- DB_NAME: $DB_NAME"
echo "- DB_HOST: $DB_HOST"
echo "- FLASK_ENV: $FLASK_ENV"

# Crear directorios necesarios si no existen
mkdir -p app/static/uploads
mkdir -p logs

echo "Database initialization starting..."
python -u setup_db_azure.py || echo "Database setup exited with code $?. Continuing anyway..."
echo "Database initialization completed."

# Configuración para plan F1 económico - reducir workers y threads
echo "Starting Gunicorn server (optimized for F1 plan)..."
exec gunicorn --bind :8000 --workers 1 --threads 2 --timeout 120 --access-logfile - --error-logfile - wsgi:app
