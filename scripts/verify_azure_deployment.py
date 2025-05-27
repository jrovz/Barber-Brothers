#!/usr/bin/env python
"""
Script para verificar el funcionamiento de la aplicación en Azure App Service
"""
import requests
import sys
import time

# URL base de la aplicación
BASE_URL = "https://barberia-app.azurewebsites.net"

def check_endpoint(endpoint, method="GET", expected_status=200, auth=None, data=None):
    """Verifica un endpoint específico de la aplicación"""
    url = f"{BASE_URL}{endpoint}"
    print(f"Verificando {method} {url}...")
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, auth=auth, timeout=30)
        elif method.upper() == "POST":
            response = requests.post(url, auth=auth, json=data, timeout=30)
        else:
            print(f"Método no soportado: {method}")
            return False
        
        if response.status_code == expected_status:
            print(f"✅ Éxito: {response.status_code}")
            return True
        else:
            print(f"❌ Error: Código de estado {response.status_code} (esperado {expected_status})")
            print(f"Respuesta: {response.text[:200]}...")
            return False
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

def main():
    """Función principal para verificar el funcionamiento de la aplicación"""
    print("Iniciando verificación de la aplicación en Azure App Service...")
    print(f"URL base: {BASE_URL}\n")
    
    # Lista de endpoints a verificar
    endpoints = [
        # Endpoints públicos
        ("/", "GET", 200),
        ("/api/health", "GET", 200),
        ("/servicios", "GET", 200),
        ("/productos", "GET", 200),
        ("/barberos", "GET", 200),
        
        # Endpoints administrativos (verificar solo accesibilidad)
        ("/admin/login", "GET", 200),
    ]
    
    # Verificar cada endpoint
    results = []
    for endpoint_data in endpoints:
        endpoint, method, expected_status = endpoint_data
        result = check_endpoint(endpoint, method, expected_status)
        results.append((endpoint, result))
        # Esperar un poco entre solicitudes para no sobrecargar
        time.sleep(1)
    
    # Mostrar resumen
    print("\n=== RESUMEN DE VERIFICACIÓN ===")
    success_count = sum(1 for _, result in results if result)
    total_count = len(results)
    
    for endpoint, result in results:
        status = "✅ Correcto" if result else "❌ Fallido"
        print(f"{status}: {endpoint}")
    
    print(f"\nTotal: {success_count}/{total_count} endpoints funcionando correctamente")
    
    # Salir con código de error si alguna verificación falló
    if success_count < total_count:
        print("\n⚠️ Algunas verificaciones fallaron. Revisa los logs de Azure para más detalles.")
        sys.exit(1)
    else:
        print("\n🎉 Todas las verificaciones fueron exitosas. ¡La aplicación está funcionando correctamente!")
        sys.exit(0)

if __name__ == "__main__":
    main()
