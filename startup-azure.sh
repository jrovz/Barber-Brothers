#!/bin/bash
# Script de inicio para Azure App Service

echo "Starting Barberia App service on Azure..."
echo "Environment variables:"
echo "- DB_USER: $DB_USER"
echo "- DB_NAME: $DB_NAME"
echo "- DB_HOST: $DB_HOST"
echo "- FLASK_ENV: $FLASK_ENV"

echo "Database initialization starting..."
python -u setup_db_azure.py || echo "Database setup exited with code $?. Continuing anyway..."
echo "Database initialization completed."

echo "Starting Gunicorn server..."
exec gunicorn --bind :8000 --workers 1 --threads 8 --timeout 120 wsgi:app
