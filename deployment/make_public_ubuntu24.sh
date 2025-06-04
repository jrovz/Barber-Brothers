#!/bin/bash

# Script compatible con Ubuntu 22.04, 24.04 y 24.10
# Detecta automáticamente la versión y se adapta

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

# Detectar versión de Ubuntu
detect_ubuntu_version() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        UBUNTU_VERSION=$VERSION_ID
        UBUNTU_CODENAME=$VERSION_CODENAME
        print_status "Detectado: Ubuntu $VERSION ($UBUNTU_CODENAME)"
    else
        print_warning "No se pudo detectar la versión de Ubuntu. Asumiendo Ubuntu 22.04"
        UBUNTU_VERSION="22.04"
        UBUNTU_CODENAME="jammy"
    fi
}

# Instalar dependencias específicas por versión
install_dependencies() {
    print_status "Instalando dependencias para Ubuntu $UBUNTU_VERSION..."
    
    # Actualizar repositorios
    apt update && apt upgrade -y
    
    # Dependencias base (compatibles con todas las versiones)
    BASE_PACKAGES="python3 python3-pip python3-venv python3-dev build-essential pkg-config"
    BASE_PACKAGES="$BASE_PACKAGES postgresql postgresql-contrib nginx ufw git curl wget unzip"
    BASE_PACKAGES="$BASE_PACKAGES libpq-dev libssl-dev libffi-dev"
    
    # Dependencias para imágenes (Pillow)
    IMAGE_PACKAGES="libjpeg-dev libpng-dev zlib1g-dev libtiff-dev"
    IMAGE_PACKAGES="$IMAGE_PACKAGES libfreetype6-dev liblcms2-dev libwebp-dev"
    
    # Dependencias adicionales para Ubuntu 24.x
    if [[ "$UBUNTU_VERSION" == "24."* ]]; then
        print_status "Configurando para Ubuntu 24.x..."
        EXTRA_PACKAGES="libharfbuzz-dev libfribidi-dev libxcb1-dev python3-setuptools"
        
        # En Ubuntu 24.x, python3-distutils puede no estar disponible por defecto
        if apt-cache show python3-distutils >/dev/null 2>&1; then
            EXTRA_PACKAGES="$EXTRA_PACKAGES python3-distutils"
        fi
    else
        print_status "Configurando para Ubuntu 22.04..."
        EXTRA_PACKAGES="python3-distutils"
    fi
    
    # Instalar todos los paquetes
    apt install -y $BASE_PACKAGES $IMAGE_PACKAGES $EXTRA_PACKAGES
    
    print_status "✅ Dependencias instaladas correctamente"
}

# Configurar Python y pip
setup_python() {
    print_status "Configurando Python para Ubuntu $UBUNTU_VERSION..."
    
    # En Ubuntu 24.x, pip puede requerir configuración adicional
    if [[ "$UBUNTU_VERSION" == "24."* ]]; then
        # Actualizar pip con método compatible
        python3 -m pip install --upgrade pip --break-system-packages || python3 -m pip install --upgrade pip
        
        # Configurar entorno virtual con configuraciones adicionales para Ubuntu 24.x
        export PIP_BREAK_SYSTEM_PACKAGES=1
    else
        # Ubuntu 22.04 - configuración estándar
        python3 -m pip install --upgrade pip
    fi
    
    print_status "✅ Python configurado correctamente"
}

# Verificar que estamos en el directorio correcto
if [ ! -f "wsgi.py" ]; then
    print_error "Este script debe ejecutarse desde el directorio raíz del proyecto (/opt/barber-brothers)"
    exit 1
fi

print_header "CONFIGURANDO BARBER BROTHERS PARA UBUNTU"

# Detectar versión
detect_ubuntu_version

# Instalar dependencias si es necesario
if [ "$1" = "--install-deps" ]; then
    install_dependencies
    setup_python
fi

print_header "CONFIGURANDO APLICACIÓN PARA ACCESO PÚBLICO"

# 1. Configurar Gunicorn
print_status "Configurando Gunicorn..."

cat > gunicorn.conf.py << 'EOF'
# Configuración de Gunicorn para producción - Compatible con Ubuntu 22.04/24.x
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

# 2. Crear servicio systemd (compatible con todas las versiones)
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
Environment=PYTHONPATH=/opt/barber-brothers
ExecStart=/opt/barber-brothers/venv/bin/gunicorn --config gunicorn.conf.py wsgi:app
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=5
StandardOutput=append:/var/log/barber-brothers/app.log
StandardError=append:/var/log/barber-brothers/app.log

# Configuraciones de seguridad adicionales para Ubuntu 24.x
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/barber-brothers /var/log/barber-brothers

[Install]
WantedBy=multi-user.target
EOF

# 3. Configurar Nginx (compatible con todas las versiones)
print_status "Configurando Nginx..."

sudo tee /etc/nginx/sites-available/barber-brothers > /dev/null << 'EOF'
server {
    listen 80;
    server_name 144.217.86.8;
    
    # Security headers mejorados para Ubuntu 24.x
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'; font-src 'self' data: https:;" always;
    
    # Logs específicos
    access_log /var/log/nginx/barber-brothers_access.log;
    error_log /var/log/nginx/barber-brothers_error.log;
    
    # Configuración de buffers para mejor rendimiento
    client_max_body_size 16M;
    client_body_buffer_size 128k;
    
    # Archivos estáticos
    location /static {
        alias /opt/barber-brothers/app/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
        try_files $uri $uri/ =404;
        
        # Compresión para archivos estáticos
        location ~* \.(css|js|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
            gzip on;
            gzip_vary on;
            gzip_types text/css application/javascript image/svg+xml;
        }
    }
    
    # Archivos de uploads
    location /uploads {
        alias /opt/barber-brothers/app/static/uploads;
        expires 1y;
        add_header Cache-Control "public";
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:5000/health;
        access_log off;
        proxy_connect_timeout 5s;
        proxy_send_timeout 5s;
        proxy_read_timeout 5s;
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
        
        # Buffer configurations
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
        proxy_busy_buffers_size 8k;
    }
    
    # Error pages
    error_page 502 503 504 /50x.html;
    location = /50x.html {
        root /var/www/html;
    }
}
EOF

# 4. Configurar logs y permisos
print_status "Configurando logs y permisos..."
sudo mkdir -p /var/log/barber-brothers
sudo chown ubuntu:ubuntu /var/log/barber-brothers
sudo chmod 755 /var/log/barber-brothers

# 5. Habilitar sitio en Nginx
print_status "Habilitando sitio en Nginx..."
sudo ln -sf /etc/nginx/sites-available/barber-brothers /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# 6. Verificar configuración de Nginx
print_status "Verificando configuración de Nginx..."
if sudo nginx -t; then
    print_status "✅ Configuración de Nginx válida"
else
    print_error "❌ Error en configuración de Nginx"
    exit 1
fi

# 7. Configurar firewall
print_status "Configurando firewall..."
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
sudo ufw --force enable

# 8. Recargar servicios
print_status "Recargando servicios..."
sudo systemctl daemon-reload
sudo systemctl enable barber-brothers
sudo systemctl restart nginx

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

if sudo systemctl is-active --quiet postgresql; then
    print_status "✅ PostgreSQL está ejecutándose"
else
    print_warning "⚠️ PostgreSQL puede no estar ejecutándose"
fi

# 11. Probar conectividad
print_status "Probando conectividad..."
sleep 3

if curl -f -s http://localhost > /dev/null; then
    print_status "✅ Aplicación responde localmente"
else
    print_warning "⚠️ Aplicación no responde localmente - revisa logs"
fi

print_header "CONFIGURACIÓN COMPLETADA"
print_status "¡Aplicación configurada para acceso público en Ubuntu $UBUNTU_VERSION!"
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
echo "🔍 Troubleshooting:"
echo "   sudo journalctl -u barber-brothers --no-pager -l  # Ver errores del servicio"
echo "   sudo nginx -t                            # Verificar config de Nginx"
echo "   curl -I http://localhost                 # Probar conectividad local"
echo ""
print_warning "Pasos adicionales recomendados:"
echo "1. Configurar SSL/HTTPS si tienes un dominio"
echo "2. Configurar backups automáticos"
echo "3. Configurar monitoreo"
echo "4. Actualizar .env.production con configuraciones específicas"
