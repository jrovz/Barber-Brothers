#!/bin/bash
# Script simple para solucionar el error 413 'Request Entity Too Large'
# Barber Brothers - Producción

echo "🛠️ SOLUCIONANDO ERROR 413 - BARBER BROTHERS"
echo "=============================================="

# Verificar si se ejecuta como root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Este script debe ejecutarse como root"
    echo "Ejecuta: sudo bash fix_413_simple.sh"
    exit 1
fi

echo "✅ Ejecutando como root"

# 1. Backup de configuración actual
echo "📋 Creando backup de configuración nginx..."
cp /etc/nginx/sites-available/barber-brothers /etc/nginx/sites-available/barber-brothers.backup.$(date +%Y%m%d_%H%M%S)

# 2. Aumentar límite en nginx
echo "🔧 Aumentando límite de nginx a 50MB..."
sed -i 's/client_max_body_size 16M;/client_max_body_size 50M;/' /etc/nginx/sites-available/barber-brothers

# 3. Verificar cambios en nginx
echo "🔍 Verificando cambios en nginx:"
grep -n "client_max_body_size" /etc/nginx/sites-available/barber-brothers

# 4. Actualizar configuración de Flask
echo "🔧 Actualizando configuración de Flask..."
sed -i 's/MAX_CONTENT_LENGTH = 16 \* 1024 \* 1024/MAX_CONTENT_LENGTH = 50 * 1024 * 1024/' /opt/barber-brothers/app/config/__init__.py

# 5. Crear configuración de gunicorn
echo "🔧 Creando configuración de gunicorn..."
cat > /opt/barber-brothers/gunicorn.conf.py << 'EOF'
# Gunicorn configuration for Barber Brothers
bind = "127.0.0.1:5000"
workers = 3
timeout = 120
keepalive = 2
max_requests = 1000
max_requests_jitter = 50
preload_app = True
worker_class = "sync"
worker_connections = 1000

# Configuración de tamaño máximo para uploads
limit_request_line = 8190
limit_request_fields = 100
limit_request_field_size = 8190

# Configuración de memoria y buffers
worker_tmp_dir = "/dev/shm"

# Logs
accesslog = "/var/log/barber-brothers/gunicorn_access.log"
errorlog = "/var/log/barber-brothers/gunicorn_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Configuración de seguridad
forwarded_allow_ips = "127.0.0.1"
proxy_allow_ips = "127.0.0.1"
EOF

# 6. Cambiar permisos
chown ubuntu:ubuntu /opt/barber-brothers/gunicorn.conf.py

# 7. Verificar configuración de nginx
echo "🔍 Verificando configuración de nginx..."
if nginx -t; then
    echo "✅ Configuración de nginx válida"
    
    # 8. Reiniciar nginx
    echo "🔄 Reiniciando nginx..."
    systemctl reload nginx
    
    if [ $? -eq 0 ]; then
        echo "✅ Nginx reiniciado exitosamente"
    else
        echo "❌ Error al reiniciar nginx"
        exit 1
    fi
else
    echo "❌ Error en configuración nginx - restaurando backup"
    cp /etc/nginx/sites-available/barber-brothers.backup.$(date +%Y%m%d) /etc/nginx/sites-available/barber-brothers
    exit 1
fi

# 9. Reiniciar aplicación
echo "🔄 Reiniciando aplicación barber-brothers..."
systemctl restart barber-brothers

if [ $? -eq 0 ]; then
    echo "✅ Aplicación reiniciada exitosamente"
else
    echo "❌ Error al reiniciar la aplicación"
    echo "📋 Verificando logs..."
    journalctl -u barber-brothers --no-pager -l --since '1 minute ago'
    exit 1
fi

# 10. Verificar estado
echo "🔍 Verificando estado de servicios..."
sleep 3

if systemctl is-active --quiet barber-brothers; then
    echo "✅ Barber Brothers está ejecutándose"
else
    echo "❌ Barber Brothers no está ejecutándose"
    systemctl status barber-brothers --no-pager -l
    exit 1
fi

if systemctl is-active --quiet nginx; then
    echo "✅ Nginx está ejecutándose"
else
    echo "❌ Nginx no está ejecutándose"
    exit 1
fi

echo ""
echo "🎉 SOLUCIÓN COMPLETADA"
echo "======================"
echo "✅ El error 413 debería estar solucionado"
echo "✅ Límites actualizados:"
echo "   • Nginx: 50MB"
echo "   • Flask: 50MB"
echo "   • Gunicorn: Configurado optimamente"
echo ""
echo "🧪 PRUEBA LA SUBIDA DE ARCHIVOS:"
echo "1. Ve a tu panel de admin"
echo "2. Intenta subir una imagen a los sliders"
echo ""
echo "📋 Si aún tienes problemas, verifica logs:"
echo "   sudo tail -f /var/log/nginx/barber-brothers_error.log"
echo "   sudo journalctl -u barber-brothers -f"
echo ""
echo "📊 Configuraciones aplicadas:"
grep -n "client_max_body_size" /etc/nginx/sites-available/barber-brothers
grep -n "MAX_CONTENT_LENGTH" /opt/barber-brothers/app/config/__init__.py
echo ""
echo "🔧 Si necesitas aumentar más el límite, edita:"
echo "   /etc/nginx/sites-available/barber-brothers"
echo "   /opt/barber-brothers/app/config/__init__.py" 