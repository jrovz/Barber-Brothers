#!/bin/bash
# Este script ejecuta las migraciones de la base de datos
echo "Ejecutando migraciones de la base de datos..."

# Configurar variables de entorno si no están presentes
export FLASK_APP=${FLASK_APP:-wsgi.py}

# Verificar si tenemos las variables necesarias para la conexión
if [ -z "$DB_USER" ] || [ -z "$DB_PASS" ] || [ -z "$DB_NAME" ]; then
  echo "ADVERTENCIA: Falta alguna variable de credenciales de base de datos (DB_USER, DB_PASS, DB_NAME)"
  echo "Intentando obtener credenciales desde Secret Manager..."
  
  # Este comando fallará si no se tiene acceso a Secret Manager o si los secretos no existen
  # Pero el script continuará con lo que tenga en variables de entorno
  if command -v gcloud &> /dev/null; then
    # Solo intentar si gcloud está disponible
    DB_USER=${DB_USER:-$(gcloud secrets versions access latest --secret="db_user" 2>/dev/null || echo "")}
    DB_PASS=${DB_PASS:-$(gcloud secrets versions access latest --secret="db_pass" 2>/dev/null || echo "")}
    DB_NAME=${DB_NAME:-$(gcloud secrets versions access latest --secret="db_name" 2>/dev/null || echo "barberia_db")}
  fi
fi

# Construir el nombre de conexión a la instancia si no está presente
if [ -z "$INSTANCE_CONNECTION_NAME" ]; then
  PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-"barber-brothers-460514"}
  REGION=${DB_REGION:-${REGION:-"us-east1"}}
  INSTANCE_NAME=${INSTANCE_NAME:-"barberia-db"}
  INSTANCE_CONNECTION_NAME="${PROJECT_ID}:${REGION}:${INSTANCE_NAME}"
  echo "INSTANCE_CONNECTION_NAME construido automáticamente: $INSTANCE_CONNECTION_NAME"
fi

# Construir DATABASE_URL para PostgreSQL
if [ -n "$INSTANCE_CONNECTION_NAME" ]; then
  DB_SOCKET_DIR=${DB_SOCKET_DIR:-/cloudsql}
  export DATABASE_URL="postgresql+pg8000://${DB_USER}:${DB_PASS}@/${DB_NAME}?unix_socket=${DB_SOCKET_DIR}/${INSTANCE_CONNECTION_NAME}"
  echo "DATABASE_URL configurada para Cloud SQL"
else
  echo "ERROR: INSTANCE_CONNECTION_NAME no está configurada"
  exit 1
fi

# Ejecutar migración
cd /app
echo "Ejecutando: python -m flask db upgrade"
python -m flask db upgrade

# Verificar resultado
if [ $? -eq 0 ]; then
  echo "Migraciones completadas exitosamente"
  exit 0
else
  echo "Error durante las migraciones"
  exit 1
fi
