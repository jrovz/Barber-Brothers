"""
Script para habilitar la depuración detallada de autenticación

Este script configura el modo depuración para el proceso de autenticación
en la aplicación Flask desplegada en Cloud Run.
"""

import os
import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description='Habilitar o deshabilitar depuración en Cloud Run')
    parser.add_argument('--enable', action='store_true', help='Habilitar modo depuración')
    parser.add_argument('--disable', action='store_true', help='Deshabilitar modo depuración')
    args = parser.parse_args()

    if not args.enable and not args.disable:
        print("Debe especificar --enable o --disable")
        sys.exit(1)

    if args.enable and args.disable:
        print("No puede especificar ambos --enable y --disable")
        sys.exit(1)

    # Configurar variables de entorno
    enable_debug = args.enable
    
    # Construir comando de gcloud
    debug_value = "True" if enable_debug else "False"
    
    print(f"{'Habilitando' if enable_debug else 'Deshabilitando'} modo depuración en Cloud Run...")
    
    # Comandos para ejecutar en la terminal
    print("\nEjecute los siguientes comandos en su terminal:")
    print("------------------------------------------------")
    
    # Comando para actualizar servicio de Cloud Run
    print(f"""gcloud run services update barberia-app \\
    --set-env-vars="FLASK_DEBUG_GCP={debug_value}" \\
    --region=us-central1""")
    
    # Si se está habilitando el debug, mostrar comandos para revisar logs
    if enable_debug:
        print("\nUna vez actualizado, puede revisar los logs detallados con:")
        print("------------------------------------------------")
        print("""gcloud logging read "resource.type=cloud_run_revision AND \\
resource.labels.service_name=barberia-app AND severity>=INFO AND \\
(textPayload:login OR textPayload:auth OR textPayload:admin)"\\
--limit=50 --format="table(timestamp,severity,textPayload)"
""")

if __name__ == "__main__":
    main()
