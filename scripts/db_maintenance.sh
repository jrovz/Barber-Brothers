#!/bin/bash
# Script para mantenimiento de PostgreSQL en VM Azure
# Guardar en la VM y programar como cron job

# Variables
BACKUP_DIR="/home/azureuser/backups"
DB_NAME="barberia_db"
MAX_BACKUPS=7  # Mantener una semana de backups

# Crear directorio de backups si no existe
mkdir -p $BACKUP_DIR

# Timestamp para el nombre del archivo
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/${DB_NAME}_${TIMESTAMP}.sql"

# Crear backup
sudo -u postgres pg_dump $DB_NAME > $BACKUP_FILE
echo "Backup creado: $BACKUP_FILE"

# Comprimir backup
gzip $BACKUP_FILE
echo "Backup comprimido: $BACKUP_FILE.gz"

# Eliminar backups antiguos (mantener solo los últimos MAX_BACKUPS)
ls -t $BACKUP_DIR/${DB_NAME}_*.sql.gz | tail -n +$((MAX_BACKUPS+1)) | xargs -r rm
echo "Backups antiguos eliminados, manteniendo los últimos $MAX_BACKUPS"

# Ejecutar VACUUM para optimizar la base de datos
sudo -u postgres psql -d $DB_NAME -c "VACUUM FULL ANALYZE;"
echo "VACUUM FULL completado para optimizar la base de datos"

# Verificar espacio en disco
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | tr -d '%')
if [ "$DISK_USAGE" -gt 80 ]; then
    echo "ADVERTENCIA: El uso del disco es alto ($DISK_USAGE%). Considera limpiar archivos innecesarios."
fi

echo "Mantenimiento completado: $(date)"
