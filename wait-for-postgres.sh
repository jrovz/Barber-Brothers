#!/bin/bash
# wait-for-postgres.sh

set -e

host="$1"
shift
cmd="$@"

# Comprobar que las variables de entorno estén configuradas
if [ -z "$POSTGRES_PASSWORD" ] || [ -z "$POSTGRES_USER" ] || [ -z "$POSTGRES_DB" ]; then
  echo "Error: Variables de entorno POSTGRES_USER, POSTGRES_PASSWORD o POSTGRES_DB no están configuradas"
  exit 1
fi

# Intentar conectar a postgres, con un timeout después de 60 intentos
count=0
until PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$host" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\q'; do
  >&2 echo "Postgres is unavailable - sleeping (intento $count/60)"
  sleep 1
  count=$((count+1))
  if [ $count -gt 60 ]; then
    >&2 echo "¡Timeout esperando a Postgres!"
    exit 1
  fi
done

>&2 echo "Postgres is up - executing command"
exec $cmd
