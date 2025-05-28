#!/bin/bash
# docker-entrypoint.sh

set -e

echo "Iniciando la aplicación..."
echo "Configuración de PostgreSQL:"
echo "Host: db"
echo "Usuario: $POSTGRES_USER"
echo "Base de datos: $POSTGRES_DB"

# Esperar a que PostgreSQL esté disponible
echo "Esperando a que PostgreSQL esté disponible..."
./wait-for-postgres.sh db

# Aplicar migraciones
echo "Aplicando migraciones a la base de datos..."
flask db upgrade || { echo "Error al aplicar migraciones"; exit 1; }

# Iniciar Gunicorn
echo "Iniciando servidor Gunicorn..."
exec gunicorn --bind 0.0.0.0:5000 wsgi:app
