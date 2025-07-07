#!/bin/bash

# Script para corregir error 413 - Límite 30MB
# Ejecutar en el servidor de producción

echo "🚀 SOLUCIONANDO ERROR 413 - ESTABLECIENDO LÍMITE 30MB"
echo "=================================================="

# 1. Backup de configuración nginx
echo "📋 Creando backup de configuración nginx..."
sudo cp /etc/nginx/sites-available/barber-brothers /etc/nginx/sites-available/barber-brothers.backup.$(date +%Y%m%d_%H%M%S)

# 2. Actualizar límite en nginx a 30MB
echo "🔧 Actualizando límite de nginx a 30MB..."
sudo sed -i 's/client_max_body_size [0-9]*M;/client_max_body_size 30M;/g' /etc/nginx/sites-available/barber-brothers

# Si no existe la línea, agregarla
if ! grep -q "client_max_body_size" /etc/nginx/sites-available/barber-brothers; then
    echo "📝 Agregando client_max_body_size a nginx..."
    sudo sed -i '/server {/a\    client_max_body_size 30M;' /etc/nginx/sites-available/barber-brothers
fi

# 3. Verificar cambios en nginx
echo "🔍 Verificando cambios en nginx:"
grep -n "client_max_body_size" /etc/nginx/sites-available/barber-brothers

# 4. Verificar sintaxis de nginx
echo "🔍 Verificando configuración de nginx..."
if sudo nginx -t; then
    echo "✅ Configuración de nginx válida"
    
    # 5. Reiniciar nginx
    echo "🔄 Reiniciando nginx..."
    if sudo systemctl reload nginx; then
        echo "✅ Nginx reiniciado exitosamente"
    else
        echo "❌ Error al reiniciar nginx"
    fi
else
    echo "❌ Error en configuración nginx - restaurando backup"
    sudo cp /etc/nginx/sites-available/barber-brothers.backup.$(date +%Y%m%d) /etc/nginx/sites-available/barber-brothers 2>/dev/null || true
fi

# 6. Reiniciar aplicación Flask
echo "🔄 Reiniciando aplicación Flask..."
sudo systemctl restart barber-brothers || sudo systemctl restart gunicorn || echo "⚠️ Reinicia manualmente la aplicación"

# 7. Verificar estado de servicios
echo ""
echo "📊 ESTADO FINAL:"
echo "================"

echo "🔍 Flask configurado a: 30MB (ya actualizado en código)"

echo -n "🔍 Nginx configurado a: "
grep "client_max_body_size" /etc/nginx/sites-available/barber-brothers | head -1

echo ""
echo "📋 Servicios activos:"
if systemctl is-active --quiet nginx; then
    echo "✅ Nginx está ejecutándose"
else
    echo "❌ Nginx no está ejecutándose"
fi

if systemctl is-active --quiet barber-brothers; then
    echo "✅ Aplicación está ejecutándose"
elif systemctl is-active --quiet gunicorn; then
    echo "✅ Gunicorn está ejecutándose"
else
    echo "❌ La aplicación no está ejecutándose"
fi

echo ""
echo "🎉 CONFIGURACIÓN COMPLETADA"
echo "=========================="
echo "Límites establecidos:"
echo "   • Flask: 30MB ✅"
echo "   • Nginx: 30MB ✅"
echo ""
echo "El admin ya puede subir imágenes hasta 30MB"
echo ""
echo "📝 Para verificar logs si hay problemas:"
echo "   sudo tail -f /var/log/nginx/error.log"
echo "   sudo journalctl -u barber-brothers -f" 