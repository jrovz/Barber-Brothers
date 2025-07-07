#!/bin/bash

# Script para cambiar ID del admin de 1 a 0 y crear Leonardo barbero con ID 1
# Ejecutar en el servidor Ubuntu OVH

echo "🔄 REORGANIZACIÓN DE IDs: Admin ID 1→0, Leonardo→Barbero ID 1"
echo "============================================================="

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

# Verificar estado actual
echo "🔍 VERIFICANDO ESTADO ACTUAL:"
echo "============================="

sudo -u $DB_USER psql $DB_NAME << 'EOF'
-- Ver usuarios actuales
\echo '👥 USUARIOS ACTUALES:'
SELECT id, username, email, role FROM "user" ORDER BY id;

-- Ver barberos actuales  
\echo '💈 BARBEROS ACTUALES:'
SELECT id, nombre, username, activo FROM barbero ORDER BY id;

-- Verificar si existe user ID 0
\echo '🔍 ¿EXISTE USER ID 0?'
SELECT CASE WHEN EXISTS(SELECT 1 FROM "user" WHERE id = 0) 
       THEN 'SÍ EXISTE - CONFLICTO' 
       ELSE 'NO EXISTE - OK' END as estado_id_0;

-- Verificar restricciones de clave foránea en tabla user
\echo '🔗 RESTRICCIONES DE CLAVE FORÁNEA:'
SELECT 
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc 
JOIN information_schema.key_column_usage AS kcu ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY' AND ccu.table_name = 'user';
EOF

echo ""
echo "❓ OPCIONES DE REORGANIZACIÓN:"
echo "============================="
echo ""
echo "1️⃣  Cambiar admin a ID 0 y crear Leonardo barbero ID 1"
echo "2️⃣  Solo cambiar admin a ID 0 (sin crear barbero)"
echo "3️⃣  Crear Leonardo barbero con próximo ID disponible"
echo "4️⃣  Cancelar operación"
echo ""
read -p "Elige opción (1-4): " opcion

case $opcion in
    1)
        echo ""
        echo "🚀 OPCIÓN 1: Reorganización completa..."
        echo "======================================"
        
        # Verificar conflictos
        id_0_exists=$(sudo -u $DB_USER psql $DB_NAME -t -c "SELECT COUNT(*) FROM \"user\" WHERE id = 0;")
        
        if [ "$id_0_exists" -gt 0 ]; then
            echo "❌ ERROR: Ya existe un usuario con ID 0"
            echo "Necesitas resolver este conflicto primero."
            exit 1
        fi
        
        echo "✅ ID 0 disponible, procediendo..."
        
        sudo -u $DB_USER psql $DB_NAME << 'EOF'
-- PASO 1: Cambiar ID del admin de 1 a 0
BEGIN;

-- Desactivar temporalmente restricciones de clave foránea si existen
SET session_replication_role = replica;

-- Cambiar ID del usuario admin
UPDATE "user" SET id = 0 WHERE id = 1;

-- Reactivar restricciones
SET session_replication_role = DEFAULT;

-- Reiniciar secuencia para que el próximo ID sea 1
ALTER SEQUENCE user_id_seq RESTART WITH 1;

COMMIT;

\echo '✅ PASO 1 COMPLETADO: Admin ahora tiene ID 0'

-- PASO 2: Crear nuevo usuario Leonardo con ID 1
INSERT INTO "user" (username, email, password_hash, role, creado) 
VALUES ('leonardo', 'leonardo@barberia.com', 
        (SELECT password_hash FROM "user" WHERE id = 0), 
        'barbero', NOW());

\echo '✅ PASO 2 COMPLETADO: Usuario Leonardo creado con ID 1'

-- PASO 3: Crear barbero Leonardo con ID 1
INSERT INTO barbero (nombre, especialidad, descripcion, activo, username, password_hash, tiene_acceso_web, creado) 
SELECT 
    'Leonardo Mora' as nombre,
    'Barbero General' as especialidad,
    'Barbero especializado en cortes modernos y estilos clásicos' as descripcion,
    true as activo,
    'leonardo' as username,
    password_hash,
    true as tiene_acceso_web,
    NOW() as creado
FROM "user" WHERE id = 1;

\echo '✅ PASO 3 COMPLETADO: Barbero Leonardo creado con ID 1'

-- PASO 4: Crear disponibilidad para barbero ID 1
INSERT INTO disponibilidad_barbero (barbero_id, dia_semana, hora_inicio, hora_fin, activo) VALUES
(1, 0, '08:00:00', '12:00:00', true), (1, 1, '08:00:00', '12:00:00', true), (1, 2, '08:00:00', '12:00:00', true),
(1, 3, '08:00:00', '12:00:00', true), (1, 4, '08:00:00', '12:00:00', true), (1, 5, '08:00:00', '12:00:00', true),
(1, 0, '14:00:00', '20:00:00', true), (1, 1, '14:00:00', '20:00:00', true), (1, 2, '14:00:00', '20:00:00', true),
(1, 3, '14:00:00', '20:00:00', true), (1, 4, '14:00:00', '20:00:00', true), (1, 5, '14:00:00', '20:00:00', true);

\echo '✅ PASO 4 COMPLETADO: Horarios configurados'

-- VERIFICACIÓN FINAL
\echo ''
\echo '🎯 RESULTADO FINAL:'
\echo '=================='
\echo 'USUARIOS:'
SELECT id, username, email, role FROM "user" ORDER BY id;

\echo 'BARBEROS:'
SELECT id, nombre, username, activo FROM barbero ORDER BY id;

\echo 'HORARIOS DE LEONARDO:'
SELECT 
    CASE db.dia_semana 
        WHEN 0 THEN 'Lunes' WHEN 1 THEN 'Martes' WHEN 2 THEN 'Miércoles'
        WHEN 3 THEN 'Jueves' WHEN 4 THEN 'Viernes' WHEN 5 THEN 'Sábado'
    END as dia,
    db.hora_inicio, 
    db.hora_fin
FROM barbero b 
JOIN disponibilidad_barbero db ON b.id = db.barbero_id 
WHERE b.id = 1
ORDER BY db.dia_semana, db.hora_inicio;
EOF
        
        echo ""
        echo "✅ REORGANIZACIÓN COMPLETADA"
        echo "============================="
        echo "📊 ESTRUCTURA FINAL:"
        echo "   - Admin (ID 0): labarberbrothers"
        echo "   - Barbero (ID 1): leonardo / Leonardo Mora"
        echo ""
        echo "🔑 ACCESOS:"
        echo "   - Admin: labarberbrothers + contraseña original → /admin/"
        echo "   - Barbero: leonardo + contraseña original → /barbero/"
        ;;
        
    2)
        echo ""
        echo "🚀 OPCIÓN 2: Solo cambiar admin a ID 0..."
        echo "========================================"
        
        id_0_exists=$(sudo -u $DB_USER psql $DB_NAME -t -c "SELECT COUNT(*) FROM \"user\" WHERE id = 0;")
        
        if [ "$id_0_exists" -gt 0 ]; then
            echo "❌ ERROR: Ya existe un usuario con ID 0"
            exit 1
        fi
        
        sudo -u $DB_USER psql $DB_NAME << 'EOF'
-- Cambiar ID del admin de 1 a 0
BEGIN;

SET session_replication_role = replica;
UPDATE "user" SET id = 0 WHERE id = 1;
SET session_replication_role = DEFAULT;

-- Reiniciar secuencia
ALTER SEQUENCE user_id_seq RESTART WITH 1;

COMMIT;

-- Verificar
SELECT 'RESULTADO:', id, username, role FROM "user" ORDER BY id;
EOF
        
        echo "✅ Admin cambiado a ID 0"
        ;;
        
    3)
        echo ""
        echo "🚀 OPCIÓN 3: Crear Leonardo con próximo ID..."
        echo "============================================"
        
        sudo -u $DB_USER psql $DB_NAME << 'EOF'
-- Cambiar user actual a barbero y crear Leonardo
UPDATE "user" SET role = 'barbero' WHERE id = 1;

-- Crear barbero Leonardo Mora
INSERT INTO barbero (nombre, especialidad, descripcion, activo, username, password_hash, tiene_acceso_web, creado) 
SELECT 
    'Leonardo Mora',
    'Barbero General',
    'Barbero especializado en cortes modernos',
    true,
    'leonardo',
    password_hash,
    true,
    NOW()
FROM "user" WHERE id = 1;

-- Cambiar username
UPDATE "user" SET username = 'leonardo' WHERE id = 1;

-- Crear disponibilidad
INSERT INTO disponibilidad_barbero (barbero_id, dia_semana, hora_inicio, hora_fin, activo) VALUES
(1, 0, '08:00:00', '12:00:00', true), (1, 1, '08:00:00', '12:00:00', true), (1, 2, '08:00:00', '12:00:00', true),
(1, 3, '08:00:00', '12:00:00', true), (1, 4, '08:00:00', '12:00:00', true), (1, 5, '08:00:00', '12:00:00', true),
(1, 0, '14:00:00', '20:00:00', true), (1, 1, '14:00:00', '20:00:00', true), (1, 2, '14:00:00', '20:00:00', true),
(1, 3, '14:00:00', '20:00:00', true), (1, 4, '14:00:00', '20:00:00', true), (1, 5, '14:00:00', '20:00:00', true);

SELECT 'RESULTADO:', id, username, role FROM "user";
SELECT 'BARBERO:', id, nombre, username FROM barbero;
EOF
        
        echo "✅ Leonardo barbero creado con ID actual"
        ;;
        
    4)
        echo ""
        echo "❌ OPERACIÓN CANCELADA"
        ;;
        
    *)
        echo "❌ OPCIÓN INVÁLIDA"
        ;;
esac

echo ""
echo "🎯 PROCESO COMPLETADO"
echo "====================" 