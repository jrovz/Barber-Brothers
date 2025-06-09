#!/bin/bash

# Script alternativo para HTTPS con certificado autofirmado
# Usar solo si Let's Encrypt no funciona con la IP

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

print_header "CONFIGURANDO HTTPS CON CERTIFICADO AUTOFIRMADO"

# 1. Crear directorio para certificados
print_status "Creando directorio para certificados..."
sudo mkdir -p /etc/ssl/private
sudo mkdir -p /etc/ssl/certs

# 2. Generar certificado autofirmado
print_status "Generando certificado autofirmado..."
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/private/barber-brothers.key \
    -out /etc/ssl/certs/barber-brothers.crt \
    -subj "/C=CO/ST=Bogota/L=Bogota/O=Barber Brothers/OU=IT Department/CN=144.217.86.8"

# 3. Configurar permisos
sudo chmod 600 /etc/ssl/private/barber-brothers.key
sudo chmod 644 /etc/ssl/certs/barber-brothers.crt

# 4. Crear configuración Nginx para HTTPS
print_status "Configurando Nginx para HTTPS..."

sudo tee /etc/nginx/sites-available/barber-brothers-ssl-self > /dev/null << 'EOF'
# Redirección HTTP a HTTPS
server {
    listen 80;
    server_name 144.217.86.8;
    return 301 https://$server_name$request_uri;
}

# Configuración HTTPS con certificado autofirmado
server {
    listen 443 ssl http2;
    server_name 144.217.86.8;
    
    # Certificados SSL autofirmados
    ssl_certificate /etc/ssl/certs/barber-brothers.crt;
    ssl_certificate_key /etc/ssl/private/barber-brothers.key;
    
    # Configuraciones de seguridad SSL
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Headers de seguridad (sin HSTS para certificados autofirmados)
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
    }
    
    # Servir archivos estáticos
    location /static/ {
        alias /opt/barber-brothers/app/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Health check
    location /health {
        proxy_pass http://127.0.0.1:5000/health;
        access_log off;
    }
}
EOF

# 5. Activar configuración
print_status "Activando configuración HTTPS..."
sudo rm -f /etc/nginx/sites-enabled/barber-brothers
sudo ln -sf /etc/nginx/sites-available/barber-brothers-ssl-self /etc/nginx/sites-enabled/barber-brothers

# 6. Verificar y recargar Nginx
sudo nginx -t
if [ $? -eq 0 ]; then
    sudo systemctl reload nginx
    print_status "✅ Nginx reconfigurado para HTTPS"
else
    print_error "❌ Error en configuración de Nginx"
    exit 1
fi

# 7. Configurar firewall
print_status "Configurando firewall..."
sudo ufw allow 443/tcp

print_header "✅ HTTPS CONFIGURADO CON CERTIFICADO AUTOFIRMADO"

print_status "🌐 Tu aplicación ahora está disponible en:"
print_status "   HTTPS: https://144.217.86.8"
print_status "   HTTP: http://144.217.86.8 (redirige a HTTPS)"

print_warning "⚠️  IMPORTANTE - CERTIFICADO AUTOFIRMADO:"
print_warning "   - Los navegadores mostrarán una advertencia de seguridad"
print_warning "   - Haz clic en 'Avanzado' -> 'Continuar al sitio'"
print_warning "   - El certificado es válido por 1 año"
print_warning "   - Para producción, considera obtener un dominio y usar Let's Encrypt"

print_status "🔧 Para usar Let's Encrypt en el futuro:"
print_status "   1. Obtén un dominio (ej: barberbros.com)"
print_status "   2. Apunta el dominio a tu IP (144.217.86.8)"
print_status "   3. Ejecuta: bash deployment/setup_https.sh"
