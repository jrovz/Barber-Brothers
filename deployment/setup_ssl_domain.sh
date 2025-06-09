#!/bin/bash

# Script para configurar SSL con dominio propio para Barber Brothers
# Configuración manual paso a paso

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

# CONFIGURACIÓN - EDITA ESTOS VALORES
DOMAIN="tudominio.com"  # Tu dominio (ej: barberbrothers.com) - CAMBIA ESTO
EMAIL="thebarberbrothers1@gmail.com"  # Email para notificaciones
SERVER_IP="144.217.86.8"  # IP de tu servidor VPS

print_header "CONFIGURACIÓN SSL CON DOMINIO PROPIO"

# Verificar que se configuró el dominio
if [ -z "$DOMAIN" ]; then
    print_error "❌ DEBES CONFIGURAR TU DOMINIO PRIMERO"
    echo ""
    echo "Edita este archivo y cambia la línea:"
    echo "DOMAIN=\"\"  # <- Pon tu dominio aquí"
    echo ""
    echo "Por ejemplo:"
    echo "DOMAIN=\"tudominio.com\""
    echo ""
    exit 1
fi

print_status "🌐 Configurando SSL para dominio: $DOMAIN"
print_status "📧 Email de contacto: $EMAIL"
print_status "🖥️  IP del servidor: $SERVER_IP"

echo ""
print_warning "⚠️  ANTES DE CONTINUAR, VERIFICA:"
print_warning "1. Que tu dominio $DOMAIN apunte a la IP $SERVER_IP"
print_warning "2. Que la aplicación esté funcionando en HTTP"
print_warning "3. Que tengas acceso SSH al servidor"
echo ""
read -p "¿Continuar? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_status "Operación cancelada"
    exit 0
fi

# 1. Verificar que estamos en el servidor correcto
print_status "1. Verificando entorno del servidor..."
if [ ! -f "/opt/barber-brothers/wsgi.py" ]; then
    print_error "❌ La aplicación debe estar en /opt/barber-brothers"
    exit 1
fi

# 2. Verificar que el dominio resuelve a la IP correcta
print_status "2. Verificando DNS del dominio..."
RESOLVED_IP=$(dig +short $DOMAIN | tail -1)
if [ "$RESOLVED_IP" != "$SERVER_IP" ]; then
    print_error "❌ El dominio $DOMAIN no apunta a la IP $SERVER_IP"
    print_error "   DNS actual: $RESOLVED_IP"
    print_error "   IP esperada: $SERVER_IP"
    echo ""
    print_warning "SOLUCIONES:"
    print_warning "1. Configurar registro A en tu proveedor de dominio:"
    print_warning "   Nombre: @ (o tu subdominio)"
    print_warning "   Tipo: A"
    print_warning "   Valor: $SERVER_IP"
    print_warning "   TTL: 300 (5 minutos)"
    print_warning ""
    print_warning "2. Si usas Cloudflare, desactiva el proxy (nube gris)"
    print_warning "3. Espera a que se propague el DNS (puede tomar hasta 24h)"
    echo ""
    read -p "¿Continuar de todas formas? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 3. Verificar servicios
print_status "3. Verificando servicios del sistema..."

# Nginx
if ! systemctl is-active --quiet nginx; then
    print_warning "Nginx no está activo, iniciando..."
    sudo systemctl start nginx
    sudo systemctl enable nginx
fi
print_status "✅ Nginx activo"

# Aplicación Flask
if ! curl -s http://localhost:5000/health > /dev/null 2>&1; then
    print_warning "⚠️  La aplicación Flask no responde en puerto 5000"
    print_status "Verificando si está ejecutándose..."
    if ! pgrep -f "python.*wsgi.py" > /dev/null; then
        print_error "❌ La aplicación Flask no está ejecutándose"
        print_status "Iniciando aplicación..."
        cd /opt/barber-brothers
        source venv/bin/activate
        nohup python wsgi.py > logs/app.log 2>&1 &
        sleep 3
    fi
fi

# 4. Instalar Certbot
print_status "4. Instalando/Actualizando Certbot..."
sudo apt update
sudo apt install -y certbot python3-certbot-nginx

# 5. Crear configuración base de Nginx
print_status "5. Configurando Nginx para el dominio..."

# Backup de configuración actual
sudo cp /etc/nginx/sites-available/barber-brothers /etc/nginx/sites-available/barber-brothers.backup || true

# Crear nueva configuración
sudo tee /etc/nginx/sites-available/barber-brothers > /dev/null << EOF
# Configuración HTTP para $DOMAIN
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    
    # Logs específicos
    access_log /var/log/nginx/${DOMAIN}_access.log;
    error_log /var/log/nginx/${DOMAIN}_error.log;
    
    # Permitir challenges de Let's Encrypt
    location /.well-known/acme-challenge/ {
        root /var/www/html;
        allow all;
    }
    
    # Proxy a la aplicación Flask
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Host \$server_name;
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Archivos estáticos
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

# 6. Crear directorio para challenges
sudo mkdir -p /var/www/html
sudo chown -R www-data:www-data /var/www/html

# 7. Activar configuración y verificar
print_status "6. Activando configuración de Nginx..."
sudo rm -f /etc/nginx/sites-enabled/barber-brothers
sudo ln -sf /etc/nginx/sites-available/barber-brothers /etc/nginx/sites-enabled/

# Verificar configuración
if sudo nginx -t; then
    sudo systemctl reload nginx
    print_status "✅ Configuración de Nginx válida y recargada"
else
    print_error "❌ Error en la configuración de Nginx"
    sudo nginx -t
    exit 1
fi

# 8. Verificar acceso HTTP
print_status "7. Verificando acceso HTTP al dominio..."
if curl -s -o /dev/null -w "%{http_code}" http://$DOMAIN | grep -q "200\|301\|302"; then
    print_status "✅ Dominio accesible por HTTP"
else
    print_warning "⚠️  No se puede acceder a http://$DOMAIN"
    print_status "Verificando resolución DNS..."
    nslookup $DOMAIN || true
fi

# 9. Obtener certificado SSL
print_status "8. Obteniendo certificado SSL de Let's Encrypt..."

# Comando certbot con todas las opciones
certbot --nginx \
    --non-interactive \
    --agree-tos \
    --email $EMAIL \
    --domains $DOMAIN,www.$DOMAIN \
    --expand \
    --redirect

if [ $? -eq 0 ]; then
    print_status "✅ Certificado SSL obtenido y configurado exitosamente"
else
    print_error "❌ Error obteniendo certificado SSL"
    print_status "Intentando con método manual..."
    
    # Método alternativo: obtener certificado sin configurar Nginx automáticamente
    certbot certonly \
        --webroot \
        --webroot-path /var/www/html \
        --non-interactive \
        --agree-tos \
        --email $EMAIL \
        --domains $DOMAIN,www.$DOMAIN \
        --expand
    
    if [ $? -eq 0 ]; then
        print_status "✅ Certificado obtenido, configurando Nginx manualmente..."
        
        # Configurar Nginx manualmente con SSL
        sudo tee /etc/nginx/sites-available/barber-brothers > /dev/null << EOF
# Redirección HTTP a HTTPS
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    
    # Challenges de Let's Encrypt
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    # Redireccionar a HTTPS
    location / {
        return 301 https://\$server_name\$request_uri;
    }
}

# Configuración HTTPS
server {
    listen 443 ssl http2;
    server_name $DOMAIN www.$DOMAIN;
    
    # Certificados SSL
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    
    # Configuración SSL moderna
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Headers de seguridad
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "strict-origin-when-cross-origin";
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self';" always;
    
    # Logs
    access_log /var/log/nginx/${DOMAIN}_ssl_access.log;
    error_log /var/log/nginx/${DOMAIN}_ssl_error.log;
    
    # Configuración de la aplicación Flask
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header X-Forwarded-Host \$server_name;
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
    
    # Archivos estáticos
    location /static/ {
        alias /opt/barber-brothers/app/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        
        # Compresión para archivos estáticos
        location ~* \.(css|js)$ {
            gzip on;
            gzip_types text/css application/javascript;
        }
    }
    
    # Uploads
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
}
EOF
        
        # Verificar y recargar
        if sudo nginx -t; then
            sudo systemctl reload nginx
            print_status "✅ Configuración HTTPS aplicada"
        else
            print_error "❌ Error en configuración HTTPS"
            exit 1
        fi
    else
        print_error "❌ No se pudo obtener el certificado SSL"
        exit 1
    fi
fi

# 10. Configurar renovación automática
print_status "9. Configurando renovación automática..."
sudo crontab -l 2>/dev/null | grep -v 'certbot renew' | sudo crontab - || true
(sudo crontab -l 2>/dev/null; echo "0 3 * * * certbot renew --quiet --post-hook 'systemctl reload nginx'") | sudo crontab -

# 11. Configurar firewall
print_status "10. Configurando firewall..."
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw status

# 12. Verificaciones finales
print_status "11. Realizando verificaciones finales..."

# Verificar certificado
print_status "Verificando certificado SSL..."
sleep 5
if timeout 10 openssl s_client -connect $DOMAIN:443 -servername $DOMAIN </dev/null 2>/dev/null | grep -q "Verification: OK"; then
    print_status "✅ Certificado SSL válido"
else
    print_warning "⚠️  Verificación de certificado SSL falló (puede ser temporal)"
fi

# Test de conectividad HTTPS
print_status "Probando conectividad HTTPS..."
if curl -s -I https://$DOMAIN | grep -q "HTTP.*200\|HTTP.*301\|HTTP.*302"; then
    print_status "✅ HTTPS funcionando correctamente"
else
    print_warning "⚠️  HTTPS no responde (puede tardar unos minutos en propagarse)"
fi

print_header "🎉 CONFIGURACIÓN SSL COMPLETADA"

print_status "🌐 Tu sitio web ahora está disponible en:"
print_status "   HTTPS: https://$DOMAIN"
print_status "   HTTPS: https://www.$DOMAIN"
print_status "   HTTP: http://$DOMAIN (redirige a HTTPS)"

print_status ""
print_status "🔒 Información del certificado SSL:"
print_status "   Emisor: Let's Encrypt"
print_status "   Válido por: 90 días"
print_status "   Dominios: $DOMAIN, www.$DOMAIN"
print_status "   Renovación automática: ✅ Configurada"

print_status ""
print_status "🛠️  Comandos útiles:"
print_status "   Ver certificados: sudo certbot certificates"
print_status "   Renovar manualmente: sudo certbot renew"
print_status "   Verificar SSL: curl -I https://$DOMAIN"
print_status "   Logs Nginx: sudo tail -f /var/log/nginx/${DOMAIN}_ssl_access.log"

print_status ""
print_warning "📝 PRÓXIMOS PASOS:"
print_warning "1. Actualiza todas las URLs en tu aplicación para usar HTTPS"
print_warning "2. Actualiza tu DNS si usas CDN (Cloudflare, etc.)"
print_warning "3. Verifica que todos los enlaces externos usen HTTPS"
print_warning "4. Considera configurar HSTS en tu aplicación Flask"

print_status ""
print_status "🎯 Prueba tu sitio web en:"
print_status "   https://$DOMAIN"
print_status "   https://$DOMAIN/admin/login"
print_status "   https://$DOMAIN/health"
