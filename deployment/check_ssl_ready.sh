#!/bin/bash

# Script de verificación pre-SSL
# Verifica que todo esté listo para configurar SSL

set -e

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() { echo -e "${GREEN}✅${NC} $1"; }
print_warning() { echo -e "${YELLOW}⚠️${NC} $1"; }
print_error() { echo -e "${RED}❌${NC} $1"; }
print_header() { echo -e "${BLUE}=== $1 ===${NC}"; }

DOMAIN=$1
ERRORS=0

if [ -z "$DOMAIN" ]; then
    echo "Uso: $0 tudominio.com"
    exit 1
fi

print_header "VERIFICACIÓN PRE-SSL: $DOMAIN"
echo ""

# 1. Verificar DNS
echo "1. 🌐 Verificando DNS..."
RESOLVED_IP=$(dig +short $DOMAIN | tail -1)
if [ "$RESOLVED_IP" = "144.217.86.8" ]; then
    print_status "DNS configurado correctamente: $RESOLVED_IP"
else
    print_error "DNS no apunta a 144.217.86.8 (actual: $RESOLVED_IP)"
    ERRORS=$((ERRORS + 1))
fi

# Verificar www
WWW_IP=$(dig +short www.$DOMAIN | tail -1)
if [ "$WWW_IP" = "144.217.86.8" ]; then
    print_status "www.$DOMAIN configurado correctamente"
else
    print_error "www.$DOMAIN no apunta a 144.217.86.8 (actual: $WWW_IP)"
    ERRORS=$((ERRORS + 1))
fi

# 2. Verificar conectividad HTTP
echo ""
echo "2. 🌍 Verificando conectividad HTTP..."
if curl -s -o /dev/null -w "%{http_code}" http://$DOMAIN | grep -q "200\|301\|302"; then
    print_status "Dominio accesible por HTTP"
else
    print_error "Dominio no accesible por HTTP"
    ERRORS=$((ERRORS + 1))
fi

if curl -s -o /dev/null -w "%{http_code}" http://www.$DOMAIN | grep -q "200\|301\|302"; then
    print_status "www.$DOMAIN accesible por HTTP"
else
    print_error "www.$DOMAIN no accesible por HTTP"
    ERRORS=$((ERRORS + 1))
fi

# 3. Verificar aplicación Flask
echo ""
echo "3. 🐍 Verificando aplicación Flask..."
if systemctl is-active --quiet barber-brothers; then
    print_status "Aplicación Flask ejecutándose"
else
    print_error "Aplicación Flask no está ejecutándose"
    ERRORS=$((ERRORS + 1))
fi

# 4. Verificar Nginx
echo ""
echo "4. 🌐 Verificando Nginx..."
if systemctl is-active --quiet nginx; then
    print_status "Nginx ejecutándose"
else
    print_error "Nginx no está ejecutándose"
    ERRORS=$((ERRORS + 1))
fi

if nginx -t &>/dev/null; then
    print_status "Configuración de Nginx válida"
else
    print_error "Configuración de Nginx inválida"
    ERRORS=$((ERRORS + 1))
fi

# 5. Verificar puertos
echo ""
echo "5. 🔌 Verificando puertos..."
if netstat -tulpn | grep -q ":80.*LISTEN"; then
    print_status "Puerto 80 (HTTP) abierto"
else
    print_error "Puerto 80 (HTTP) no disponible"
    ERRORS=$((ERRORS + 1))
fi

if netstat -tulpn | grep -q ":5000.*LISTEN"; then
    print_status "Puerto 5000 (Flask) abierto"
else
    print_error "Puerto 5000 (Flask) no disponible"
    ERRORS=$((ERRORS + 1))
fi

# 6. Verificar certificados existentes
echo ""
echo "6. 🔒 Verificando certificados existentes..."
if [ -d "/etc/letsencrypt/live/$DOMAIN" ]; then
    print_warning "Certificado para $DOMAIN ya existe"
    print_warning "Será renovado/actualizado"
else
    print_status "No hay certificados existentes (correcto para primera instalación)"
fi

# 7. Verificar espacio en disco
echo ""
echo "7. 💾 Verificando espacio en disco..."
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -lt 90 ]; then
    print_status "Espacio en disco suficiente (${DISK_USAGE}% usado)"
else
    print_error "Espacio en disco insuficiente (${DISK_USAGE}% usado)"
    ERRORS=$((ERRORS + 1))
fi

# 8. Verificar permisos
echo ""
echo "8. 🔐 Verificando permisos..."
if [ -w "/etc/nginx/sites-available" ]; then
    print_status "Permisos de escritura en Nginx"
else
    print_error "Sin permisos de escritura en Nginx"
    ERRORS=$((ERRORS + 1))
fi

# Resumen
echo ""
print_header "RESUMEN DE VERIFICACIÓN"
echo ""

if [ $ERRORS -eq 0 ]; then
    print_status "✅ TODOS LOS CHECKS PASARON"
    echo ""
    print_status "🚀 LISTO PARA CONFIGURAR SSL"
    echo ""
    echo "Ejecuta uno de estos comandos:"
    echo "  sudo ./setup_ssl_simple.sh"
    echo "  sudo ./setup_ssl_domain.sh"
    echo ""
else
    print_error "❌ ENCONTRADOS $ERRORS ERRORES"
    echo ""
    print_error "🛠️ CORRIGE LOS ERRORES ANTES DE CONTINUAR"
    echo ""
    
    if echo "$RESOLVED_IP" | grep -q "144.217.86.8"; then
        :
    else
        echo "Para corregir DNS:"
        echo "1. Ve al panel de control de tu dominio"
        echo "2. Configura registro A: @ → 144.217.86.8"
        echo "3. Configura registro A: www → 144.217.86.8"
        echo "4. Espera 5-60 minutos para propagación"
        echo ""
    fi
    
    if systemctl is-active --quiet barber-brothers; then
        :
    else
        echo "Para corregir Flask:"
        echo "sudo systemctl start barber-brothers"
        echo "sudo systemctl enable barber-brothers"
        echo ""
    fi
    
    if systemctl is-active --quiet nginx; then
        :
    else
        echo "Para corregir Nginx:"
        echo "sudo systemctl start nginx"
        echo "sudo systemctl enable nginx"
        echo ""
    fi
fi

echo ""
print_header "INFORMACIÓN ADICIONAL"
echo ""
echo "🌐 Dominio: $DOMAIN"
echo "📧 IP resuelta: $RESOLVED_IP"
echo "🎯 IP objetivo: 144.217.86.8"
echo "🔗 Test URL: http://$DOMAIN"
echo ""
echo "📋 Herramientas útiles:"
echo "  - Test DNS: dig $DOMAIN"
echo "  - Test HTTP: curl -I http://$DOMAIN"
echo "  - Test conectividad: ping $DOMAIN"
echo "  - Verificar propagación: https://dnschecker.org/"

exit $ERRORS
