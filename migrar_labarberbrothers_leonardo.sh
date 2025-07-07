#!/bin/bash

# Script para convertir labarberbrothers (ID 1) en Leonardo Mora barbero
# Ejecutar en el servidor Ubuntu OVH

echo "🔄 CONVERSIÓN: labarberbrothers → Leonardo Mora (Barbero)"
echo "======================================================="

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

# Mostrar datos actuales
echo "🔍 DATOS ACTUALES:"
echo "=================="

sudo -u $DB_USER psql $DB_NAME << 'EOF'
SELECT 'USUARIO ACTUAL:', id, username, email, role FROM "user" WHERE id = 1;
EOF

echo ""
echo "❓ OPCIONES DE CONVERSIÓN:"
echo "========================="
echo ""
echo "1️⃣  Cambiar username a 'leonardo' y crear barbero"
echo "2️⃣  Mantener username 'labarberbrothers' y crear barbero" 
echo "3️⃣  Crear nuevo usuario 'leonardo' y mantener admin actual"
echo "4️⃣  Cancelar operación"
echo ""
read -p "Elige opción (1-4): " opcion

case $opcion in
    1)
        echo ""
        echo "🚀 OPCIÓN 1: Cambiando username a 'leonardo'..."
        echo "==============================================="
        
        # Verificar si username 'leonardo' ya existe
        username_exists=$(sudo -u $DB_USER psql $DB_NAME -t -c "SELECT COUNT(*) FROM \"user\" WHERE username = 'leonardo';")
        
        if [ "$username_exists" -gt 0 ]; then
            echo "❌ ERROR: Ya existe un usuario con username 'leonardo'"
            echo "Elige otra opción o usa un username diferente."
            exit 1
        fi
        
        sudo -u $DB_USER psql $DB_NAME << 'EOF'
-- 1. Cambiar username y role del user ID 1
UPDATE "user" 
SET username = 'leonardo', 
    role = 'barbero' 
WHERE id = 1;

-- 2. Crear barbero Leonardo Mora
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

-- 3. Crear disponibilidad (L-S: 8:00-12:00 y 14:00-20:00)
INSERT INTO disponibilidad_barbero (barbero_id, dia_semana, hora_inicio, hora_fin, activo) VALUES
(1, 0, '08:00:00', '12:00:00', true), (1, 1, '08:00:00', '12:00:00', true), (1, 2, '08:00:00', '12:00:00', true),
(1, 3, '08:00:00', '12:00:00', true), (1, 4, '08:00:00', '12:00:00', true), (1, 5, '08:00:00', '12:00:00', true),
(1, 0, '14:00:00', '20:00:00', true), (1, 1, '14:00:00', '20:00:00', true), (1, 2, '14:00:00', '20:00:00', true),
(1, 3, '14:00:00', '20:00:00', true), (1, 4, '14:00:00', '20:00:00', true), (1, 5, '14:00:00', '20:00:00', true);

-- Verificar resultado
\echo 'RESULTADO FINAL:'
SELECT 'USER:' as tabla, id::text, username, role as info FROM "user" WHERE id = 1
UNION ALL
SELECT 'BARBERO:' as tabla, id::text, nombre, username FROM barbero WHERE id = 1;
EOF
        
        echo ""
        echo "✅ CONVERSIÓN COMPLETADA"
        echo "📝 Leonardo ahora puede acceder con:"
        echo "   - Username: leonardo"
        echo "   - Misma contraseña anterior"
        echo "   - URL: tu-dominio.com/barbero/login"
        ;;
        
    2)
        echo ""
        echo "🚀 OPCIÓN 2: Manteniendo username 'labarberbrothers'..."
        echo "====================================================="
        
        sudo -u $DB_USER psql $DB_NAME << 'EOF'
-- 1. Cambiar solo el role del user ID 1
UPDATE "user" SET role = 'barbero' WHERE id = 1;

-- 2. Crear barbero Leonardo Mora con username original
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

-- 3. Crear disponibilidad (L-S: 8:00-12:00 y 14:00-20:00)
INSERT INTO disponibilidad_barbero (barbero_id, dia_semana, hora_inicio, hora_fin, activo) VALUES
(1, 0, '08:00:00', '12:00:00', true), (1, 1, '08:00:00', '12:00:00', true), (1, 2, '08:00:00', '12:00:00', true),
(1, 3, '08:00:00', '12:00:00', true), (1, 4, '08:00:00', '12:00:00', true), (1, 5, '08:00:00', '12:00:00', true),
(1, 0, '14:00:00', '20:00:00', true), (1, 1, '14:00:00', '20:00:00', true), (1, 2, '14:00:00', '20:00:00', true),
(1, 3, '14:00:00', '20:00:00', true), (1, 4, '14:00:00', '20:00:00', true), (1, 5, '14:00:00', '20:00:00', true);

-- Verificar resultado
\echo 'RESULTADO FINAL:'
SELECT 'USER:' as tabla, id::text, username, role as info FROM "user" WHERE id = 1
UNION ALL
SELECT 'BARBERO:' as tabla, id::text, nombre, username FROM barbero WHERE id = 1;
EOF
        
        echo ""
        echo "✅ CONVERSIÓN COMPLETADA"
        echo "📝 Leonardo ahora puede acceder con:"
        echo "   - Username: labarberbrothers"
        echo "   - Misma contraseña anterior" 
        echo "   - URL: tu-dominio.com/barbero/login"
        ;;
        
    3)
        echo ""
        echo "🚀 OPCIÓN 3: Creando nuevo usuario 'leonardo'..."
        echo "==============================================="
        echo ""
        echo "⚠️  Esta opción requiere crear una nueva contraseña."
        read -p "¿Continuar? (s/n): " continuar
        
        if [ "$continuar" != "s" ]; then
            echo "❌ Operación cancelada"
            exit 0
        fi
        
        read -s -p "Nueva contraseña para leonardo: " password
        echo ""
        
        sudo -u $DB_USER psql $DB_NAME << EOF
-- 1. Crear nuevo usuario leonardo
INSERT INTO "user" (username, email, password_hash, role, creado) 
VALUES ('leonardo', 'leonardo@barberia.com', crypt('$password', gen_salt('bf')), 'barbero', NOW());

-- 2. Obtener ID del nuevo usuario
WITH nuevo_user AS (
    SELECT id FROM "user" WHERE username = 'leonardo'
)
-- 3. Crear barbero usando el nuevo usuario
INSERT INTO barbero (nombre, especialidad, descripcion, activo, username, password_hash, tiene_acceso_web, creado) 
SELECT 
    'Leonardo Mora' as nombre,
    'Barbero General' as especialidad,
    'Barbero especializado en cortes modernos y estilos clásicos' as descripcion,
    true as activo,
    'leonardo' as username,
    u.password_hash,
    true as tiene_acceso_web,
    NOW() as creado
FROM "user" u, nuevo_user nu WHERE u.id = nu.id;

-- Verificar resultado
\echo 'USUARIOS FINALES:'
SELECT id, username, email, role FROM "user" ORDER BY id;
\echo 'BARBEROS FINALES:'
SELECT id, nombre, username FROM barbero ORDER BY id;
EOF
        
        echo ""
        echo "✅ NUEVO USUARIO CREADO"
        echo "📝 Ahora tienes:"
        echo "   - Admin: labarberbrothers (conservado)"
        echo "   - Barbero: leonardo (nuevo)"
        ;;
        
    4)
        echo ""
        echo "❌ OPERACIÓN CANCELADA"
        echo "====================="
        echo "No se realizaron cambios."
        ;;
        
    *)
        echo ""
        echo "❌ OPCIÓN INVÁLIDA"
        echo "=================="
        echo "Ejecuta el script nuevamente."
        ;;
esac

echo ""
echo "🎯 PROCESO COMPLETADO"
echo "====================" 