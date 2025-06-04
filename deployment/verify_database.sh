#!/bin/bash

# Script de verificación completa de la base de datos
# Verifica PostgreSQL, conexiones, tablas y funcionalidad

set -e

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() { echo -e "${GREEN}[INFO]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }
print_header() { echo -e "${BLUE}================================${NC}"; echo -e "${BLUE}$1${NC}"; echo -e "${BLUE}================================${NC}"; }

# Configuración de base de datos
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="barber_brothers_db"
DB_USER="barber_user"
DB_PASS="barber_password_2024"

print_header "VERIFICACIÓN COMPLETA DE BASE DE DATOS"

# 1. Verificar servicio PostgreSQL
print_status "1. Verificando servicio PostgreSQL..."
if systemctl is-active --quiet postgresql; then
    print_status "✅ PostgreSQL está ejecutándose"
    systemctl status postgresql --no-pager -l
else
    print_error "❌ PostgreSQL no está ejecutándose"
    print_status "Iniciando PostgreSQL..."
    sudo systemctl start postgresql
    sleep 3
fi

# 2. Verificar conectividad
print_status "2. Verificando conectividad..."
if pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME; then
    print_status "✅ Base de datos accesible"
else
    print_error "❌ No se puede conectar a la base de datos"
    print_status "Verificando configuración..."
    
    # Verificar si la base de datos existe
    if PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U postgres -lqt | cut -d \| -f 1 | grep -qw $DB_NAME; then
        print_status "✅ Base de datos existe"
    else
        print_error "❌ Base de datos no existe"
        print_status "Para crear la base de datos, ejecuta como postgres:"
        echo "sudo -u postgres createdb $DB_NAME"
        echo "sudo -u postgres psql -c \"CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';\""
        echo "sudo -u postgres psql -c \"GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;\""
        exit 1
    fi
fi

# 3. Verificar tablas
print_status "3. Verificando estructura de tablas..."
TABLES=$(PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name;")

if [ -n "$TABLES" ]; then
    print_status "✅ Tablas encontradas:"
    echo "$TABLES" | while read table; do
        if [ -n "$table" ]; then
            print_status "  - $table"
        fi
    done
else
    print_warning "⚠️  No se encontraron tablas"
    print_status "Ejecuta las migraciones: bash deployment/run_migrations.sh"
fi

# 4. Verificar datos básicos
print_status "4. Verificando datos en tablas principales..."

# Función para contar registros
count_records() {
    local table=$1
    local count=$(PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM $table;" 2>/dev/null || echo "0")
    echo "$count" | tr -d ' '
}

# Verificar tablas principales
main_tables=("usuario" "barbero" "cliente" "servicio" "producto" "categoria" "cita")

for table in "${main_tables[@]}"; do
    if PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "\d $table" &>/dev/null; then
        count=$(count_records $table)
        print_status "✅ Tabla $table: $count registros"
    else
        print_warning "⚠️  Tabla $table no encontrada"
    fi
done

# 5. Verificar usuario administrador
print_status "5. Verificando usuario administrador..."
admin_count=$(PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM usuario WHERE es_admin = true;" 2>/dev/null || echo "0")
admin_count=$(echo "$admin_count" | tr -d ' ')

if [ "$admin_count" -gt 0 ]; then
    print_status "✅ $admin_count usuario(s) administrador(es) encontrado(s)"
    PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT nombre, email, activo FROM usuario WHERE es_admin = true;"
else
    print_warning "⚠️  No se encontraron usuarios administradores"
    print_status "Para crear un admin, ejecuta: python3 deployment/create_admin.py"
fi

# 6. Verificar índices
print_status "6. Verificando índices..."
index_count=$(PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public';" 2>/dev/null || echo "0")
index_count=$(echo "$index_count" | tr -d ' ')
print_status "✅ $index_count índices encontrados"

# 7. Verificar tamaño de la base de datos
print_status "7. Verificando tamaño de la base de datos..."
db_size=$(PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT pg_size_pretty(pg_database_size('$DB_NAME'));" 2>/dev/null || echo "N/A")
db_size=$(echo "$db_size" | tr -d ' ')
print_status "📊 Tamaño de la base de datos: $db_size"

# 8. Test de funcionalidad básica
print_status "8. Ejecutando test de funcionalidad..."
test_result=$(PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
BEGIN;
INSERT INTO categoria (nombre, descripcion) VALUES ('Test Category', 'Test Description') ON CONFLICT (nombre) DO NOTHING;
SELECT 'Test INSERT OK' as result;
SELECT COUNT(*) as total_categories FROM categoria;
ROLLBACK;
" 2>/dev/null || echo "Test failed")

if [[ $test_result == *"Test INSERT OK"* ]]; then
    print_status "✅ Test de funcionalidad exitoso"
else
    print_warning "⚠️  Test de funcionalidad falló"
fi

# 9. Verificar configuración de PostgreSQL
print_status "9. Verificando configuración de PostgreSQL..."
pg_version=$(PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT version();" 2>/dev/null || echo "N/A")
print_status "PostgreSQL Version: $(echo $pg_version | cut -d',' -f1)"

max_connections=$(PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SHOW max_connections;" 2>/dev/null || echo "N/A")
print_status "Max Connections: $(echo $max_connections | tr -d ' ')"

# 10. Verificar logs recientes
print_status "10. Verificando logs recientes de PostgreSQL..."
if [ -d "/var/log/postgresql" ]; then
    latest_log=$(ls -t /var/log/postgresql/*.log 2>/dev/null | head -1)
    if [ -n "$latest_log" ]; then
        print_status "Log más reciente: $latest_log"
        print_status "Últimas 5 líneas:"
        tail -5 "$latest_log" || print_warning "No se pudo leer el log"
    fi
else
    print_warning "⚠️  Directorio de logs no encontrado"
fi

print_header "RESUMEN DE VERIFICACIÓN"
print_status "✅ Verificación completa finalizada"
print_status "Si hay advertencias, revisa los pasos sugeridos arriba"
print_status "Para más ayuda, revisa los logs de PostgreSQL y de la aplicación"

# Mostrar comandos útiles
print_header "COMANDOS ÚTILES"
echo "Conectar a la base de datos:"
echo "  PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME"
echo ""
echo "Ver tablas:"
echo "  \dt"
echo ""
echo "Ejecutar migraciones:"
echo "  bash deployment/run_migrations.sh"
echo ""
echo "Crear usuario admin:"
echo "  python3 deployment/create_admin.py"
