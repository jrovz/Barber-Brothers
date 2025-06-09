#!/bin/bash

# Script para configurar HTTPS con Let's Encrypt en Barber Brothers
# Ejecutar en el servidor VPS después de tener HTTP funcionando

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

# Configuración
DOMAIN="144.217.86.8"  # Tu IP pública
EMAIL="thebarberbrothers1@gmail.com"  # Email para notificaciones de Let's Encrypt

print_header "CONFIGURANDO HTTPS PARA BARBER BROTHERS"

# 1. Verificar que estamos en el directorio correcto
if [ ! -f "/opt/barber-brothers/wsgi.py" ]; then
    print_error "La aplicación debe estar en /opt/barber-brothers"
    exit 1
fi

# 2. Verificar que Nginx esté funcionando
print_status "Verificando Nginx..."
if ! systemctl is-active --quiet nginx; then
    print_error "Nginx no está ejecutándose. Configura HTTP primero."
    exit 1
fi

# 3. Verificar que la aplicación esté accesible por HTTP
print_status "Verificando acceso HTTP..."
if ! curl -s http://144.217.86.8 > /dev/null; then
    print_warning "No se puede acceder a http://144.217.86.8"
    print_status "Asegúrate de que la aplicación esté funcionando en HTTP primero"
fi

# 4. Instalar Certbot y el plugin de Nginx
print_status "Instalando Certbot..."
apt update
apt install -y certbot python3-certbot-nginx

# 5. Verificar la configuración actual de Nginx
print_status "Verificando configuración de Nginx..."
nginx -t
if [ $? -ne 0 ]; then
    print_error "Error en la configuración de Nginx. Corrige los errores primero."
    exit 1
fi

# 6. Crear configuración Nginx para HTTPS
print_status "Configurando Nginx para HTTPS..."

sudo tee /etc/nginx/sites-available/barber-brothers-ssl > /dev/null << 'EOF'
# Configuración HTTP (redirección a HTTPS)
server {
    listen 80;
    server_name 144.217.86.8;
    
    # Permitir challenges de Let's Encrypt
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    # Redireccionar todo lo demás a HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# Configuración HTTPS
server {
    listen 443 ssl http2;
    server_name 144.217.86.8;
    
    # Configuración SSL (Certbot completará esto)
    ssl_certificate /etc/letsencrypt/live/144.217.86.8/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/144.217.86.8/privkey.pem;
    
    # Configuraciones de seguridad SSL
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Headers de seguridad
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "strict-origin-when-cross-origin";
    
    # Configuración de la aplicación Flask
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $server_name;
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Buffer settings
        proxy_buffering on;
        proxy_buffer_size 128k;
        proxy_buffers 4 256k;
        proxy_busy_buffers_size 256k;
    }
    
    # Servir archivos estáticos directamente
    location /static/ {
        alias /opt/barber-brothers/app/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        
        # Compresión
        location ~* \.(css|js)$ {
            gzip on;
            gzip_types text/css application/javascript;
        }
    }
    
    # Manejo de uploads
    location /static/uploads/ {
        alias /opt/barber-brothers/app/static/uploads/;
        expires 1y;
        add_header Cache-Control "public";
    }
    
    # Health check
    location /health {
        proxy_pass http://127.0.0.1:5000/health;
        access_log off;
    }
    
    # Favicon
    location = /favicon.ico {
        alias /opt/barber-brothers/app/static/images/favicon.ico;
        log_not_found off;
        access_log off;
    }
    
    # Robots.txt
    location = /robots.txt {
        alias /opt/barber-brothers/app/static/robots.txt;
        log_not_found off;
        access_log off;
    }
}
EOF

print_status "✅ Configuración de Nginx creada"

# 7. Crear directorio para challenges
sudo mkdir -p /var/www/html
sudo chown -R www-data:www-data /var/www/html

# 8. Activar la nueva configuración temporalmente (solo HTTP para obtener certificado)
print_status "Configurando Nginx temporalmente para obtener certificado..."

# Crear configuración temporal solo HTTP
sudo tee /etc/nginx/sites-available/barber-brothers-temp > /dev/null << 'EOF'
server {
    listen 80;
    server_name 144.217.86.8;
    
    # Permitir challenges de Let's Encrypt
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    # Aplicación Flask para otras rutas
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Activar configuración temporal
sudo rm -f /etc/nginx/sites-enabled/barber-brothers
sudo ln -sf /etc/nginx/sites-available/barber-brothers-temp /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# 9. Obtener certificado SSL
print_status "Obteniendo certificado SSL de Let's Encrypt..."

# Usar --standalone porque es más confiable con IPs
certbot certonly \
    --nginx \
    --non-interactive \
    --agree-tos \
    --email $EMAIL \
    --domains $DOMAIN \
    --expand

if [ $? -eq 0 ]; then
    print_status "✅ Certificado SSL obtenido exitosamente"
else
    print_error "❌ Error obteniendo certificado SSL"
    print_status "Intentando con método standalone..."
    
    # Parar nginx temporalmente para standalone
    sudo systemctl stop nginx
    
    certbot certonly \
        --standalone \
        --non-interactive \
        --agree-tos \
        --email $EMAIL \
        --domains $DOMAIN
    
    if [ $? -eq 0 ]; then
        print_status "✅ Certificado SSL obtenido con método standalone"
        sudo systemctl start nginx
    else
        print_error "❌ No se pudo obtener el certificado SSL"
        sudo systemctl start nginx
        exit 1
    fi
fi

# 10. Activar configuración HTTPS completa
print_status "Activando configuración HTTPS..."
sudo rm -f /etc/nginx/sites-enabled/barber-brothers-temp
sudo ln -sf /etc/nginx/sites-available/barber-brothers-ssl /etc/nginx/sites-enabled/barber-brothers

# Verificar configuración
sudo nginx -t
if [ $? -eq 0 ]; then
    sudo systemctl reload nginx
    print_status "✅ Nginx reconfigurado para HTTPS"
else
    print_error "❌ Error en configuración de Nginx"
    # Volver a configuración temporal
    sudo rm -f /etc/nginx/sites-enabled/barber-brothers
    sudo ln -sf /etc/nginx/sites-available/barber-brothers-temp /etc/nginx/sites-enabled/
    sudo systemctl reload nginx
    exit 1
fi

# 11. Configurar renovación automática
print_status "Configurando renovación automática..."
sudo crontab -l 2>/dev/null | grep -v 'certbot renew' | sudo crontab -
(sudo crontab -l 2>/dev/null; echo "0 3 * * * certbot renew --quiet --post-hook 'systemctl reload nginx'") | sudo crontab -

# 12. Configurar firewall para HTTPS
print_status "Configurando firewall..."
sudo ufw allow 443/tcp
sudo ufw status

# 13. Verificar configuración SSL
print_status "Verificando configuración SSL..."
if command -v openssl &> /dev/null; then
    echo | openssl s_client -servername $DOMAIN -connect $DOMAIN:443 2>/dev/null | openssl x509 -noout -dates
fi

print_header "✅ HTTPS CONFIGURADO EXITOSAMENTE"

print_status "🌐 Tu aplicación ahora está disponible en:"
print_status "   HTTPS: https://144.217.86.8"
print_status "   HTTP: http://144.217.86.8 (redirige a HTTPS)"

print_status "🔒 Detalles del certificado SSL:"
print_status "   Emisor: Let's Encrypt"
print_status "   Válido por: 90 días"
print_status "   Renovación automática: Configurada"

print_status "🛠️ Comandos útiles:"
print_status "   Ver certificados: certbot certificates"
print_status "   Renovar manualmente: certbot renew"
print_status "   Verificar SSL: curl -I https://144.217.86.8"

print_warning "⚠️  IMPORTANTE:"
print_warning "   - El certificado se renueva automáticamente cada 90 días"
print_warning "   - Verifica que el firewall permita el puerto 443"
print_warning "   - Algunos navegadores pueden mostrar advertencia por usar IP en lugar de dominio"
