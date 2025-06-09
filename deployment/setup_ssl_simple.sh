#!/bin/bash

# Script simplificado para SSL - Barber Brothers
# Usar después de configurar DNS

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
print_header() { echo -e "${BLUE}=== $1 ===${NC}"; }

# Solicitar dominio al usuario
print_header "CONFIGURACIÓN SSL SIMPLIFICADA"
echo ""
echo "Este script configurará SSL para tu dominio."
echo "REQUISITOS:"
echo "- Tu dominio debe apuntar a 144.217.86.8"
echo "- La aplicación debe funcionar en HTTP"
echo ""

read -p "Ingresa tu dominio (ej: barberbrothers.com): " DOMAIN
read -p "Ingresa tu email (para Let's Encrypt): " EMAIL

if [ -z "$DOMAIN" ]; then
    print_error "Dominio requerido"
    exit 1
fi

if [ -z "$EMAIL" ]; then
    EMAIL="thebarberbrothers1@gmail.com"
fi

print_status "Dominio: $DOMAIN"
print_status "Email: $EMAIL"
echo ""

# Verificar DNS
print_status "Verificando DNS..."
RESOLVED_IP=$(dig +short $DOMAIN | tail -1)
if [ "$RESOLVED_IP" != "144.217.86.8" ]; then
    print_warning "⚠️ DNS parece no estar configurado correctamente"
    print_warning "IP actual: $RESOLVED_IP"
    print_warning "IP esperada: 144.217.86.8"
    echo ""
    read -p "¿Continuar de todas formas? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Confirmar
echo ""
read -p "¿Proceder con la configuración SSL? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_status "Operación cancelada"
    exit 0
fi

print_header "INICIANDO CONFIGURACIÓN"

# 1. Actualizar paquetes
print_status "1. Actualizando sistema..."
sudo apt update

# 2. Instalar Certbot
print_status "2. Instalando Certbot..."
sudo apt install -y certbot python3-certbot-nginx

# 3. Backup configuración actual
print_status "3. Creando respaldo de configuración..."
sudo cp /etc/nginx/sites-available/barber-brothers /etc/nginx/sites-available/barber-brothers.backup.$(date +%Y%m%d_%H%M%S) || true

# 4. Crear configuración HTTP temporal
print_status "4. Configurando Nginx temporal..."
sudo tee /etc/nginx/sites-available/barber-brothers > /dev/null << EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    
    location /.well-known/acme-challenge/ {
        root /var/www/html;
        allow all;
    }
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    location /static/ {
        alias /opt/barber-brothers/app/static/;
        expires 1y;
    }
}
EOF

# 5. Crear directorio para challenges
sudo mkdir -p /var/www/html
sudo chown -R www-data:www-data /var/www/html

# 6. Recargar Nginx
print_status "5. Recargando Nginx..."
if sudo nginx -t; then
    sudo systemctl reload nginx
else
    print_error "Error en configuración de Nginx"
    exit 1
fi

# 7. Obtener certificado SSL
print_status "6. Obteniendo certificado SSL..."
if sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos --email $EMAIL --redirect; then
    print_status "✅ Certificado SSL configurado automáticamente"
else
    print_error "Error obteniendo certificado. Intentando método manual..."
    
    # Método alternativo
    if sudo certbot certonly --webroot -w /var/www/html -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos --email $EMAIL; then
        print_status "✅ Certificado obtenido. Configurando Nginx manualmente..."
        
        # Configurar Nginx con SSL
        sudo tee /etc/nginx/sites-available/barber-brothers > /dev/null << EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN www.$DOMAIN;
    
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header X-Forwarded-Host \$server_name;
    }
    
    location /static/ {
        alias /opt/barber-brothers/app/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF
        
        if sudo nginx -t; then
            sudo systemctl reload nginx
            print_status "✅ Configuración HTTPS aplicada"
        else
            print_error "Error en configuración HTTPS"
            exit 1
        fi
    else
        print_error "No se pudo obtener certificado SSL"
        exit 1
    fi
fi

# 8. Configurar renovación automática
print_status "7. Configurando renovación automática..."
(sudo crontab -l 2>/dev/null | grep -v 'certbot renew'; echo "0 3 * * * certbot renew --quiet --post-hook 'systemctl reload nginx'") | sudo crontab -

# 9. Configurar firewall
print_status "8. Configurando firewall..."
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

print_header "CONFIGURACIÓN COMPLETADA"

# Verificaciones finales
print_status "Realizando verificaciones..."

# Test HTTP → HTTPS redirect
if curl -s -I http://$DOMAIN | grep -q "301\|302"; then
    print_status "✅ Redirección HTTP → HTTPS funcionando"
else
    print_warning "⚠️ Redirección HTTP → HTTPS no detectada"
fi

# Test HTTPS
if curl -s -I https://$DOMAIN | grep -q "200"; then
    print_status "✅ HTTPS funcionando correctamente"
else
    print_warning "⚠️ HTTPS no responde correctamente"
fi

echo ""
print_header "🎉 SSL CONFIGURADO EXITOSAMENTE"
echo ""
print_status "🌐 Tu sitio está disponible en:"
print_status "   → https://$DOMAIN"
print_status "   → https://www.$DOMAIN"
print_status "   → https://$DOMAIN/admin/login"
echo ""
print_status "📋 Información del certificado:"
print_status "   → Emisor: Let's Encrypt"
print_status "   → Válido por: 90 días"
print_status "   → Renovación: Automática"
echo ""
print_status "🔧 Comandos útiles:"
print_status "   → Ver certificados: sudo certbot certificates"
print_status "   → Renovar: sudo certbot renew"
print_status "   → Test SSL: curl -I https://$DOMAIN"
echo ""
print_warning "📝 Próximos pasos:"
print_warning "1. Prueba tu sitio en https://$DOMAIN"
print_warning "2. Actualiza URLs en tu aplicación si es necesario"
print_warning "3. Considera configurar CSP headers adicionales"
