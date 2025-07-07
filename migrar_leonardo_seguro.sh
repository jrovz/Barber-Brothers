#!/bin/bash

# Script SEGURO para migrar Leonardo Mora de admin a barbero
# Incluye verificaciones y opciones según datos existentes

echo "🔍 MIGRACIÓN SEGURA: Leonardo Mora (Admin → Barbero)"
echo "==================================================="

DB_NAME="barber_brothers_db"
DB_USER="postgres"

echo "📋 Base de datos: $DB_NAME"
echo ""

# Verificar PostgreSQL
if ! systemctl is-active --quiet postgresql; then
    echo "❌ ERROR: PostgreSQL no está corriendo"
    exit 1
fi

echo "✅ PostgreSQL corriendo"
echo ""

# Crear script de verificación
cat > /tmp/verificar_leonardo.sql << 'EOF'
-- VERIFICACIÓN DE DATOS EXISTENTES
\echo '🔍 1. LEONARDO EN TABLA USER:'
SELECT id, username, email, role FROM "user" WHERE username ILIKE '%leonardo%' OR email ILIKE '%leonardo%';

\echo ''
\echo '🔍 2. LEONARDO EN TABLA BARBERO:'
SELECT id, nombre, username, activo, tiene_acceso_web FROM barbero WHERE nombre ILIKE '%leonardo%' OR username ILIKE '%leonardo%';

\echo ''
\echo '📊 3. TODOS LOS USUARIOS:'
SELECT id, username, email, role FROM "user" ORDER BY id;

\echo ''
\echo '💈 4. TODOS LOS BARBEROS:'
SELECT id, nombre, username, activo FROM barbero ORDER BY id;
EOF

echo "🔍 VERIFICANDO DATOS EXISTENTES..."
echo "================================="

# Ejecutar verificación
sudo -u $DB_USER psql $DB_NAME -f /tmp/verificar_leonardo.sql

echo ""
echo "⚠️  PAUSA PARA REVISIÓN"
echo "======================"
echo ""
echo "Revisa los resultados arriba y elige una opción:"
echo ""
echo "1️⃣  Leonardo NO existe como barbero → Crear nuevo barbero"
echo "2️⃣  Leonardo YA es barbero → Solo verificar configuración"
echo "3️⃣  Hay conflicto/duplicado → Resolver manualmente"
echo "4️⃣  Cancelar operación"
echo ""
read -p "Elige opción (1-4): " opcion

case $opcion in
    1)
        echo ""
        echo "🚀 OPCIÓN 1: Creando nuevo barbero..."
        echo "===================================="
        
        cat > /tmp/crear_barbero.sql << 'EOF'
-- Crear barbero desde user ID 1
INSERT INTO barbero (nombre, especialidad, descripcion, activo, username, password_hash, tiene_acceso_web, creado) 
SELECT 
    'Leonardo Mora' as nombre,
    'Barbero General' as especialidad,
    'Barbero especializado en cortes modernos y estilos clásicos' as descripcion,
    true as activo,
    username,
    password_hash,
    true as tiene_acceso_web,
    NOW() as creado
FROM "user" WHERE id = 1;

-- Cambiar role en user
UPDATE "user" SET role = 'barbero' WHERE id = 1;

-- Crear disponibilidad (L-S: 8:00-12:00 y 14:00-20:00)
INSERT INTO disponibilidad_barbero (barbero_id, dia_semana, hora_inicio, hora_fin, activo) VALUES
(1, 0, '08:00:00', '12:00:00', true), (1, 1, '08:00:00', '12:00:00', true), (1, 2, '08:00:00', '12:00:00', true),
(1, 3, '08:00:00', '12:00:00', true), (1, 4, '08:00:00', '12:00:00', true), (1, 5, '08:00:00', '12:00:00', true),
(1, 0, '14:00:00', '20:00:00', true), (1, 1, '14:00:00', '20:00:00', true), (1, 2, '14:00:00', '20:00:00', true),
(1, 3, '14:00:00', '20:00:00', true), (1, 4, '14:00:00', '20:00:00', true), (1, 5, '14:00:00', '20:00:00', true);

-- Verificar resultado
\echo 'RESULTADO:'
SELECT 'USER:' as tabla, id::text, username, role as info FROM "user" WHERE id = 1
UNION ALL
SELECT 'BARBERO:' as tabla, id::text, nombre, activo::text FROM barbero WHERE id = 1;
EOF
        
        sudo -u $DB_USER psql $DB_NAME -f /tmp/crear_barbero.sql
        echo "✅ Barbero creado exitosamente"
        ;;
        
    2)
        echo ""
        echo "🔧 OPCIÓN 2: Verificando configuración existente..."
        echo "================================================="
        
        cat > /tmp/verificar_config.sql << 'EOF'
-- Verificar configuración actual del barbero Leonardo
SELECT 
    'BARBERO:' as tipo,
    id::text,
    nombre,
    username,
    activo::text as estado,
    tiene_acceso_web::text as acceso_web
FROM barbero WHERE nombre ILIKE '%leonardo%' OR username ILIKE '%leonardo%'
UNION ALL
SELECT 
    'USER:' as tipo,
    id::text,
    username,
    email,
    role,
    'N/A' as acceso_web
FROM "user" WHERE username ILIKE '%leonardo%' OR email ILIKE '%leonardo%';

-- Ver disponibilidad
\echo 'HORARIOS CONFIGURADOS:'
SELECT 
    CASE db.dia_semana 
        WHEN 0 THEN 'Lunes' WHEN 1 THEN 'Martes' WHEN 2 THEN 'Miércoles'
        WHEN 3 THEN 'Jueves' WHEN 4 THEN 'Viernes' WHEN 5 THEN 'Sábado'
    END as dia,
    db.hora_inicio, 
    db.hora_fin,
    db.activo
FROM barbero b 
JOIN disponibilidad_barbero db ON b.id = db.barbero_id 
WHERE b.nombre ILIKE '%leonardo%' OR b.username ILIKE '%leonardo%'
ORDER BY db.dia_semana, db.hora_inicio;
EOF
        
        sudo -u $DB_USER psql $DB_NAME -f /tmp/verificar_config.sql
        echo "✅ Configuración verificada"
        ;;
        
    3)
        echo ""
        echo "⚠️  OPCIÓN 3: Conflicto detectado"
        echo "================================"
        echo "Por favor, revisa manualmente los datos y decide qué hacer."
        echo "Puedes usar los comandos SQL individuales según sea necesario."
        ;;
        
    4)
        echo ""
        echo "❌ OPERACIÓN CANCELADA"
        echo "====================="
        echo "No se realizaron cambios en la base de datos."
        ;;
        
    *)
        echo ""
        echo "❌ OPCIÓN INVÁLIDA"
        echo "=================="
        echo "Ejecuta el script nuevamente y elige 1, 2, 3 o 4."
        ;;
esac

# Limpiar archivos temporales
rm -f /tmp/verificar_leonardo.sql /tmp/crear_barbero.sql /tmp/verificar_config.sql

echo ""
echo "🎯 PROCESO COMPLETADO"
echo "====================" 