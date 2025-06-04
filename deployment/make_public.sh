#!/bin/bash

# Script para hacer pública la aplicación Barber Brothers
# Ejecutar en el servidor VPS después de tener la app funcionando localmente

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Verificar que estamos en el directorio correcto
if [ ! -f "wsgi.py" ]; then
    print_error "Este script debe ejecutarse desde el directorio raíz del proyecto (/opt/barber-brothers)"
    exit 1
fi

print_header "CONFIGURANDO BARBER BROTHERS PARA ACCESO PÚBLICO"

# 1. Configurar Gunicorn
print_status "Configurando Gunicorn..."

# Crear archivo de configuración de Gunicorn
cat > gunicorn.conf.py << 'EOF'
# Configuración de Gunicorn para producción
bind = "127.0.0.1:5000"
workers = 3
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 30
keepalive = 2
user = "ubuntu"
group = "ubuntu"
tmp_upload_dir = None
logfile = "/var/log/barber-brothers/gunicorn.log"
loglevel = "info"
access_logfile = "/var/log/barber-brothers/access.log"
error_logfile = "/var/log/barber-brothers/error.log"
capture_output = True
enable_stdio_inheritance = True
EOF

# 2. Crear servicio systemd
print_status "Creando servicio systemd..."

sudo tee /etc/systemd/system/barber-brothers.service > /dev/null << EOF
[Unit]
Description=Barber Brothers Flask Application
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=exec
User=ubuntu
Group=ubuntu
WorkingDirectory=/opt/barber-brothers
Environment=PATH=/opt/barber-brothers/venv/bin
Environment=FLASK_ENV=production
ExecStart=/opt/barber-brothers/venv/bin/gunicorn --config gunicorn.conf.py wsgi:app
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=5
StandardOutput=append:/var/log/barber-brothers/app.log
StandardError=append:/var/log/barber-brothers/app.log

[Install]
WantedBy=multi-user.target
EOF

# 3. Configurar Nginx
print_status "Configurando Nginx..."

sudo tee /etc/nginx/sites-available/barber-brothers > /dev/null << 'EOF'
server {
    listen 80;
    server_name 144.217.86.8;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    
    # Logs específicos
    access_log /var/log/nginx/barber-brothers_access.log;
    error_log /var/log/nginx/barber-brothers_error.log;
    
    # Archivos estáticos
    location /static {
        alias /opt/barber-brothers/app/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
        try_files $uri $uri/ =404;
    }
    
    # Archivos de uploads
    location /uploads {
        alias /opt/barber-brothers/app/static/uploads;
        expires 1y;
        add_header Cache-Control "public";
    }
    
    # Proxy a la aplicación Flask
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        proxy_buffering off;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:5000/health;
        access_log off;
    }
    
    # Error pages
    error_page 502 503 504 /50x.html;
    location = /50x.html {
        root /var/www/html;
    }
}
EOF

# 4. Habilitar sitio en Nginx
print_status "Habilitando sitio en Nginx..."
sudo ln -sf /etc/nginx/sites-available/barber-brothers /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# 5. Probar configuración de Nginx
print_status "Probando configuración de Nginx..."
sudo nginx -t

# 6. Configurar logs
print_status "Configurando logs..."
sudo mkdir -p /var/log/barber-brothers
sudo chown ubuntu:ubuntu /var/log/barber-brothers
sudo chmod 755 /var/log/barber-brothers

# 7. Recargar servicios
print_status "Recargando servicios..."
sudo systemctl daemon-reload
sudo systemctl enable barber-brothers
sudo systemctl restart nginx

# 8. Configurar firewall
print_status "Configurando firewall..."
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
sudo ufw --force enable

# 9. Iniciar aplicación
print_status "Iniciando aplicación..."
sudo systemctl start barber-brothers

# Esperar a que inicie
sleep 5

# 10. Verificar estado
print_status "Verificando estado de servicios..."

if sudo systemctl is-active --quiet barber-brothers; then
    print_status "✅ Barber Brothers está ejecutándose"
else
    print_error "❌ Error: Barber Brothers no se inició correctamente"
    print_status "Logs del servicio:"
    sudo journalctl -u barber-brothers --no-pager -l
fi

if sudo systemctl is-active --quiet nginx; then
    print_status "✅ Nginx está ejecutándose"
else
    print_error "❌ Error: Nginx no se inició correctamente"
fi

# 11. Probar conectividad
print_status "Probando conectividad..."
sleep 3

if curl -f -s http://localhost > /dev/null; then
    print_status "✅ Aplicación responde localmente"
else
    print_warning "⚠️ Aplicación no responde localmente"
fi

print_header "CONFIGURACIÓN COMPLETADA"
print_status "¡Aplicación configurada para acceso público!"
echo ""
echo "🌐 Tu aplicación está disponible en:"
echo "   http://144.217.86.8"
echo ""
echo "📊 Comandos útiles:"
echo "   sudo systemctl status barber-brothers    # Ver estado"
echo "   sudo systemctl restart barber-brothers   # Reiniciar app"
echo "   sudo journalctl -u barber-brothers -f    # Ver logs en tiempo real"
echo "   sudo tail -f /var/log/nginx/barber-brothers_access.log  # Logs de acceso"
echo ""
print_warning "Pasos adicionales recomendados:"
echo "1. Configurar SSL/HTTPS si tienes un dominio"
echo "2. Configurar backups automáticos"
echo "3. Configurar monitoreo"
EOF
