#!/bin/bash

# Script para inspeccionar la base de datos antes de migrar Leonardo
# Ejecutar en el servidor Ubuntu OVH

echo "🔍 INSPECCIÓN DE BASE DE DATOS: barber_brothers_db"
echo "================================================="

DB_NAME="barber_brothers_db"
DB_USER="postgres"

echo "📋 Base de datos: $DB_NAME"
echo "👤 Usuario: $DB_USER"
echo ""

# Verificar que PostgreSQL está corriendo
if ! systemctl is-active --quiet postgresql; then
    echo "❌ ERROR: PostgreSQL no está corriendo"
    exit 1
fi

echo "✅ PostgreSQL está corriendo"
echo ""

# Crear archivo temporal con comandos de inspección
cat > /tmp/inspeccionar.sql << 'EOF'
-- ==========================================
-- INSPECCIÓN DE BASE DE DATOS
-- ==========================================

\echo '📊 1. TODAS LAS TABLAS EN LA BASE DE DATOS:'
\dt

\echo ''
\echo '🔍 2. ESTRUCTURA DE LA TABLA USER:'
\d "user"

\echo ''
\echo '🔍 3. ESTRUCTURA DE LA TABLA BARBERO:'
\d barbero

\echo ''
\echo '🔍 4. ESTRUCTURA DE LA TABLA DISPONIBILIDAD_BARBERO:'
\d disponibilidad_barbero

\echo ''
\echo '👥 5. TODOS LOS USUARIOS EXISTENTES:'
SELECT id, username, email, role, creado FROM "user" ORDER BY id;

\echo ''
\echo '💈 6. TODOS LOS BARBEROS EXISTENTES:'
SELECT id, nombre, username, activo, tiene_acceso_web, creado FROM barbero ORDER BY id;

\echo ''
\echo '🔍 7. BUSCAR LEONARDO EN TABLA USER:'
SELECT id, username, email, role FROM "user" WHERE username ILIKE '%leonardo%' OR email ILIKE '%leonardo%';

\echo ''
\echo '🔍 8. BUSCAR LEONARDO EN TABLA BARBERO:'
SELECT id, nombre, username, activo FROM barbero WHERE nombre ILIKE '%leonardo%' OR username ILIKE '%leonardo%';

\echo ''
\echo '📅 9. DISPONIBILIDADES EXISTENTES:'
SELECT 
    b.nombre as barbero,
    db.dia_semana,
    db.hora_inicio,
    db.hora_fin,
    db.activo
FROM barbero b 
LEFT JOIN disponibilidad_barbero db ON b.id = db.barbero_id 
ORDER BY b.id, db.dia_semana, db.hora_inicio;

\echo ''
\echo '📊 10. ESTADÍSTICAS GENERALES:'
SELECT 
    'Usuarios' as tabla, COUNT(*) as total FROM "user"
UNION ALL
SELECT 
    'Barberos' as tabla, COUNT(*) as total FROM barbero
UNION ALL
SELECT 
    'Disponibilidades' as tabla, COUNT(*) as total FROM disponibilidad_barbero;

\echo ''
\echo '✅ INSPECCIÓN COMPLETADA'
EOF

echo "🗄️ Ejecutando inspección..."
echo ""

# Ejecutar los comandos SQL
sudo -u $DB_USER psql $DB_NAME -f /tmp/inspeccionar.sql

# Limpiar archivo temporal
rm /tmp/inspeccionar.sql

echo ""
echo "🎯 ANÁLISIS COMPLETADO"
echo ""
echo "📝 PRÓXIMOS PASOS:"
echo "1. Revisar si la tabla 'barbero' existe y tiene la estructura correcta"
echo "2. Verificar si Leonardo ya existe como barbero"
echo "3. Si todo está bien, proceder con la migración"
echo "4. Si hay problemas, crear/modificar las tablas necesarias" 