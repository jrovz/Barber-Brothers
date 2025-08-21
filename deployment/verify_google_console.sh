#!/bin/bash

# Script para verificar la configuración de Google Search Console
# Uso: ./verify_google_console.sh [DOMINIO]

DOMAIN=${1:-"localhost:5000"}

echo "🔍 Verificando configuración de Google Search Console..."
echo "Dominio: $DOMAIN"
echo ""

# Verificar archivo de verificación
echo "📄 Verificando archivo de verificación..."
VERIFICATION_URL="http://$DOMAIN/google17b126f9a1dae6ef.html"
echo "URL: $VERIFICATION_URL"

if curl -s -I "$VERIFICATION_URL" | grep -q "200 OK"; then
    echo "✅ Archivo de verificación accesible"
    echo "Contenido:"
    curl -s "$VERIFICATION_URL"
else
    echo "❌ Error: Archivo de verificación no accesible"
    curl -I "$VERIFICATION_URL"
fi

echo ""
echo "🔍 Verificando robots.txt..."
ROBOTS_URL="http://$DOMAIN/robots.txt"
if curl -s -I "$ROBOTS_URL" | grep -q "200 OK"; then
    echo "✅ robots.txt accesible"
    echo "Contenido:"
    curl -s "$ROBOTS_URL"
else
    echo "❌ Error: robots.txt no accesible"
fi

echo ""
echo "🔍 Verificando sitemap..."
SITEMAP_URL="http://$DOMAIN/sitemap.xml"
if curl -s -I "$SITEMAP_URL" | grep -q "200 OK"; then
    echo "✅ sitemap.xml accesible"
    echo "Primeras líneas:"
    curl -s "$SITEMAP_URL" | head -10
else
    echo "❌ Error: sitemap.xml no accesible"
fi

echo ""
echo "🎯 Próximos pasos:"
echo "1. Ve a https://search.google.com/search-console"
echo "2. Añade tu propiedad: $DOMAIN"
echo "3. Selecciona 'Archivo HTML' como método de verificación"
echo "4. Confirma que el archivo sea accesible en: $VERIFICATION_URL"
echo "5. Haz clic en 'Verificar'"
echo ""
echo "✅ Configuración completada!"
