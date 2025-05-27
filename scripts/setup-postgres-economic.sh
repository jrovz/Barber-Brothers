#!/bin/bash
# Script para configurar PostgreSQL en VM económica de Azure

# Variables para la base de datos
DB_USER="barberia_user"
DB_PASSWORD="barberia_password"  # Cambiar por una contraseña segura
DB_NAME="barberia_db"

# Actualizar paquetes
sudo apt update
sudo apt upgrade -y

# Instalar PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Configurar usuario y base de datos
sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
sudo -u postgres psql -c "ALTER USER $DB_USER WITH SUPERUSER;"

# Configurar PostgreSQL para aceptar conexiones remotas
sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/" /etc/postgresql/*/main/postgresql.conf

# Configurar autenticación por contraseña
echo "host    all             all             0.0.0.0/0               md5" | sudo tee -a /etc/postgresql/*/main/pg_hba.conf

# Reiniciar PostgreSQL
sudo systemctl restart postgresql

# Crear directorio para backups
mkdir -p ~/backups
chmod 755 ~/backups

# Configurar backup automático diario
(crontab -l 2>/dev/null; echo "0 2 * * * pg_dump -U postgres $DB_NAME > ~/backups/barberia_backup_\$(date +\%Y\%m\%d).sql") | crontab -

echo "Configuración de PostgreSQL completada. La base de datos está lista para usar."
