#!/usr/bin/env python3
"""
Script de prueba para verificar las correcciones SEO implementadas.
Verifica que sitemap.xml y favicon.ico funcionen correctamente.
"""

import requests
import sys
from urllib.parse import urljoin

def test_sitemap(base_url):
    """Prueba que el sitemap.xml funcione correctamente."""
    print("🔍 Probando sitemap.xml...")
    
    try:
        sitemap_url = urljoin(base_url, '/sitemap.xml')
        response = requests.get(sitemap_url, timeout=10)
        
        if response.status_code == 200:
            print("✅ sitemap.xml: OK (200)")
            
            # Verificar que el contenido sea XML válido
            content = response.text
            if '<?xml version="1.0" encoding="UTF-8"?>' in content:
                print("✅ sitemap.xml: Contenido XML válido")
            else:
                print("❌ sitemap.xml: Contenido XML inválido")
                return False
                
            # Verificar que contenga URLs principales
            if 'urlset' in content and 'url' in content:
                print("✅ sitemap.xml: Estructura de sitemap válida")
            else:
                print("❌ sitemap.xml: Estructura de sitemap inválida")
                return False
                
            return True
        else:
            print(f"❌ sitemap.xml: Error {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ sitemap.xml: Error de conexión - {e}")
        return False

def test_favicon(base_url):
    """Prueba que el favicon.ico funcione correctamente."""
    print("🔍 Probando favicon.ico...")
    
    try:
        favicon_url = urljoin(base_url, '/favicon.ico')
        response = requests.get(favicon_url, timeout=10)
        
        if response.status_code == 200:
            print("✅ favicon.ico: OK (200)")
            
            # Verificar que el contenido sea una imagen
            content_type = response.headers.get('content-type', '')
            if 'image' in content_type:
                print(f"✅ favicon.ico: Tipo de contenido válido ({content_type})")
            else:
                print(f"⚠️ favicon.ico: Tipo de contenido inesperado ({content_type})")
                
            return True
        else:
            print(f"❌ favicon.ico: Error {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ favicon.ico: Error de conexión - {e}")
        return False

def test_redirects(base_url):
    """Prueba que las redirecciones 301 funcionen correctamente."""
    print("🔍 Probando redirecciones 301...")
    
    redirect_tests = [
        ('/index', '/'),
        ('/home', '/'),
        ('/inicio', '/'),
        ('/service', '/servicios'),
        ('/services', '/servicios'),
        ('/product', '/productos'),
        ('/products', '/productos'),
        ('/producto', '/productos'),
        ('/tienda', '/productos')
    ]
    
    success_count = 0
    
    for from_path, to_path in redirect_tests:
        try:
            from_url = urljoin(base_url, from_path)
            response = requests.get(from_url, timeout=10, allow_redirects=False)
            
            if response.status_code == 301:
                location = response.headers.get('location', '')
                if to_path in location:
                    print(f"✅ {from_path} → {to_path}: OK (301)")
                    success_count += 1
                else:
                    print(f"❌ {from_path} → {to_path}: Redirección incorrecta ({location})")
            else:
                print(f"❌ {from_path} → {to_path}: Error {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ {from_path} → {to_path}: Error de conexión - {e}")
    
    print(f"📊 Redirecciones: {success_count}/{len(redirect_tests)} exitosas")
    return success_count == len(redirect_tests)

def test_canonical_urls(base_url):
    """Prueba que las canonical URLs estén configuradas correctamente."""
    print("🔍 Probando canonical URLs...")
    
    test_pages = ['/', '/servicios', '/productos']
    success_count = 0
    
    for page in test_pages:
        try:
            page_url = urljoin(base_url, page)
            response = requests.get(page_url, timeout=10)
            
            if response.status_code == 200:
                content = response.text
                if 'rel="canonical"' in content:
                    print(f"✅ {page}: Canonical URL presente")
                    success_count += 1
                else:
                    print(f"❌ {page}: Canonical URL ausente")
            else:
                print(f"❌ {page}: Error {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ {page}: Error de conexión - {e}")
    
    print(f"📊 Canonical URLs: {success_count}/{len(test_pages)} exitosas")
    return success_count == len(test_pages)

def main():
    """Función principal de prueba."""
    print("🚀 Iniciando pruebas de correcciones SEO...")
    print("=" * 50)
    
    # URL base del sitio (cambiar por tu dominio)
    base_url = "http://localhost:5000"  # Cambiar por tu URL de producción
    
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    
    print(f"🌐 Probando en: {base_url}")
    print()
    
    # Ejecutar pruebas
    tests = [
        ("Sitemap XML", lambda: test_sitemap(base_url)),
        ("Favicon", lambda: test_favicon(base_url)),
        ("Redirecciones 301", lambda: test_redirects(base_url)),
        ("Canonical URLs", lambda: test_canonical_urls(base_url))
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"🧪 {test_name}:")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}: Error inesperado - {e}")
            results.append((test_name, False))
        print()
    
    # Resumen final
    print("=" * 50)
    print("📋 RESUMEN DE PRUEBAS:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Resultado: {passed}/{len(results)} pruebas exitosas")
    
    if passed == len(results):
        print("🎉 ¡Todas las correcciones SEO funcionan correctamente!")
        return 0
    else:
        print("⚠️ Algunas correcciones necesitan atención.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
