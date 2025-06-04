#!/bin/bash

# Script para ejecutar migraciones de Flask en el servidor
# Ejecutar desde el directorio del proyecto (/opt/barber-brothers)

set -e

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

# Verificar directorio
if [ ! -f "wsgi.py" ]; then
    print_error "Este script debe ejecutarse desde el directorio del proyecto"
    print_error "Ejemplo: cd /opt/barber-brothers && bash deployment/run_migrations.sh"
    exit 1
fi

print_header "EJECUTANDO MIGRACIONES DE FLASK"

# 1. Configurar variables de entorno
print_status "Configurando variables de entorno..."
export FLASK_APP=wsgi.py
export FLASK_ENV=production

# Si existe archivo .env.production, cargarlo
if [ -f ".env.production" ]; then
    print_status "Cargando configuración de producción..."
    set -a
    source .env.production
    set +a
else
    print_warning "No se encontró .env.production, usando configuración por defecto"
    export DATABASE_URL="postgresql://barber_user:barber_password_2024@localhost:5432/barber_brothers_db"
fi

# 2. Activar entorno virtual si existe
if [ -d "venv" ]; then
    print_status "Activando entorno virtual..."
    source venv/bin/activate
else
    print_warning "No se encontró entorno virtual"
fi

# 3. Verificar conexión a la base de datos
print_status "Verificando conexión a PostgreSQL..."
if ! pg_isready -h localhost -p 5432 -U barber_user -d barber_brothers_db; then
    print_error "No se puede conectar a PostgreSQL"
    print_error "Verifica que PostgreSQL esté ejecutándose y la base de datos exista"
    exit 1
fi

print_status "✅ Conexión a PostgreSQL exitosa"

# 4. Verificar instalación de Flask-Migrate
print_status "Verificando Flask-Migrate..."
if ! python -c "import flask_migrate" 2>/dev/null; then
    print_error "Flask-Migrate no está instalado"
    print_status "Instalando Flask-Migrate..."
    pip install Flask-Migrate
fi

# 5. Inicializar migraciones si es necesario
if [ ! -d "migrations" ]; then
    print_status "Inicializando migraciones..."
    flask db init
    print_status "✅ Migraciones inicializadas"
else
    print_status "✅ Directorio de migraciones ya existe"
fi

# 6. Crear migración si hay cambios pendientes
print_status "Verificando cambios en modelos..."
flask db migrate -m "Auto migration $(date '+%Y%m%d_%H%M%S')" || print_warning "No hay cambios detectados en modelos"

# 7. Ejecutar migraciones
print_status "Ejecutando migraciones..."
flask db upgrade

if [ $? -eq 0 ]; then
    print_status "✅ Migraciones ejecutadas exitosamente"
else
    print_error "❌ Error ejecutando migraciones"
    exit 1
fi

# 8. Verificar tablas creadas
print_status "Verificando tablas en la base de datos..."
PGPASSWORD=barber_password_2024 psql -h localhost -U barber_user -d barber_brothers_db -c "\dt" || print_warning "No se pudo listar tablas"

# 9. Mostrar estado actual de migraciones
print_status "Estado actual de migraciones:"
flask db current || print_warning "No se pudo obtener estado de migraciones"

print_status "Historial de migraciones:"
flask db history || print_warning "No se pudo obtener historial"

print_header "✅ MIGRACIONES COMPLETADAS"
print_status "La base de datos está lista para usar"
print_warning "Recuerda crear un usuario administrador si es necesario"
