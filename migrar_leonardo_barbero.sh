#!/bin/bash

# Script para cambiar Leonardo Mora (ID 1) de admin a barbero
# Ejecutar en el servidor Ubuntu OVH

echo "🚀 INICIANDO MIGRACIÓN: Leonardo Mora (Admin → Barbero)"
echo "=================================================="

# Configuración de la base de datos (ajustar según tu configuración)
DB_NAME="barber_brothers_db"  # Base de datos del proyecto
DB_USER="postgres"

echo "📋 Base de datos: $DB_NAME"
echo "👤 Usuario: $DB_USER"
echo ""

# Verificar que PostgreSQL está corriendo
if ! systemctl is-active --quiet postgresql; then
    echo "❌ ERROR: PostgreSQL no está corriendo"
    echo "Ejecuta: sudo systemctl start postgresql"
    exit 1
fi

echo "✅ PostgreSQL está corriendo"

# Crear archivo temporal con los comandos SQL
cat > /tmp/migrar_leonardo.sql << 'EOF'
-- ==========================================
-- CAMBIAR LEONARDO MORA (USER ID 1) A BARBERO
-- ==========================================

\echo '1. Verificando datos actuales del usuario ID 1:'
SELECT id, username, email, role, creado FROM "user" WHERE id = 1;

\echo '2. Creando barbero usando datos del user ID 1:'
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

\echo '3. Cambiando role de admin a barbero:'
UPDATE "user" SET role = 'barbero' WHERE id = 1;

\echo '4. Creando disponibilidad MAÑANAS (8:00-12:00):'
INSERT INTO disponibilidad_barbero (barbero_id, dia_semana, hora_inicio, hora_fin, activo) VALUES
(1, 0, '08:00:00', '12:00:00', true),
(1, 1, '08:00:00', '12:00:00', true),
(1, 2, '08:00:00', '12:00:00', true),
(1, 3, '08:00:00', '12:00:00', true),
(1, 4, '08:00:00', '12:00:00', true),
(1, 5, '08:00:00', '12:00:00', true);

\echo '5. Creando disponibilidad TARDES (14:00-20:00):'
INSERT INTO disponibilidad_barbero (barbero_id, dia_semana, hora_inicio, hora_fin, activo) VALUES
(1, 0, '14:00:00', '20:00:00', true),
(1, 1, '14:00:00', '20:00:00', true),
(1, 2, '14:00:00', '20:00:00', true),
(1, 3, '14:00:00', '20:00:00', true),
(1, 4, '14:00:00', '20:00:00', true),
(1, 5, '14:00:00', '20:00:00', true);

\echo '6. VERIFICANDO RESULTADOS:'
\echo 'Usuario actualizado:'
SELECT id, username, email, role FROM "user" WHERE id = 1;

\echo 'Barbero creado:'
SELECT id, nombre, username, tiene_acceso_web, activo FROM barbero WHERE id = 1;

\echo '7. Horarios creados:'
SELECT 
    b.nombre, 
    CASE db.dia_semana 
        WHEN 0 THEN 'Lunes'
        WHEN 1 THEN 'Martes' 
        WHEN 2 THEN 'Miércoles'
        WHEN 3 THEN 'Jueves'
        WHEN 4 THEN 'Viernes'
        WHEN 5 THEN 'Sábado'
    END as dia,
    db.hora_inicio, 
    db.hora_fin 
FROM barbero b 
JOIN disponibilidad_barbero db ON b.id = db.barbero_id 
WHERE b.id = 1 
ORDER BY db.dia_semana, db.hora_inicio;

\echo '✅ MIGRACIÓN COMPLETADA'
EOF

echo "🗄️ Ejecutando comandos SQL..."
echo ""

# Ejecutar los comandos SQL
sudo -u $DB_USER psql $DB_NAME -f /tmp/migrar_leonardo.sql

# Limpiar archivo temporal
rm /tmp/migrar_leonardo.sql

echo ""
echo "🎉 PROCESO TERMINADO"
echo ""
echo "📝 NOTAS IMPORTANTES:"
echo "- Leonardo ahora puede acceder en: tu-dominio.com/barbero/login"
echo "- Mantiene el mismo username y contraseña"
echo "- Horarios: L-S de 8:00-12:00 y 14:00-20:00"
echo "- Para verificar: inicia sesión en el panel de barbero" 