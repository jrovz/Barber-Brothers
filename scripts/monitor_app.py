#!/usr/bin/env python
"""
Script para monitorear periódicamente la aplicación en Azure App Service
Ejecutar este script en segundo plano o como tarea programada
"""
import requests
import time
import datetime
import os
import smtplib
from email.mime.text import MIMEText
import csv
import sys

# URL base de la aplicación
BASE_URL = "https://barberia-app.azurewebsites.net"

# Configuración
CHECK_INTERVAL = 15 * 60  # 15 minutos en segundos
LOG_FILE = "monitoring_log.csv"
ALERT_EMAIL = "tu@email.com"  # Cambiar por tu email

def check_availability():
    """Verifica la disponibilidad de la aplicación"""
    endpoints = [
        "/",                # Página principal
        "/api/health",      # Health check
        "/servicios"        # Una página que requiere DB
    ]
    
    results = {}
    all_ok = True
    timestamp = datetime.datetime.now()
    
    for endpoint in endpoints:
        url = f"{BASE_URL}{endpoint}"
        try:
            start_time = time.time()
            response = requests.get(url, timeout=30)
            response_time = time.time() - start_time
            
            status = response.status_code
            success = 200 <= status < 400
            
            if not success:
                all_ok = False
                
            results[endpoint] = {
                "status": status,
                "response_time": response_time,
                "success": success
            }
            
        except Exception as e:
            all_ok = False
            results[endpoint] = {
                "status": "Error",
                "response_time": 0,
                "success": False,
                "error": str(e)
            }
    
    return {
        "timestamp": timestamp,
        "all_ok": all_ok,
        "results": results
    }

def log_results(results):
    """Guarda los resultados en un archivo CSV"""
    timestamp = results["timestamp"]
    all_ok = results["all_ok"]
    
    # Crear el archivo con encabezados si no existe
    file_exists = os.path.isfile(LOG_FILE)
    
    with open(LOG_FILE, 'a', newline='') as csvfile:
        fieldnames = ['timestamp', 'all_ok', 'endpoint', 'status', 'response_time']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        for endpoint, data in results["results"].items():
            writer.writerow({
                'timestamp': timestamp,
                'all_ok': all_ok,
                'endpoint': endpoint,
                'status': data["status"],
                'response_time': data["response_time"]
            })

def send_alert(results):
    """Envía una alerta por email si hay problemas"""
    if not results["all_ok"]:
        subject = f"⚠️ Alerta: Problemas en la aplicación Barbería"
        
        # Construir el cuerpo del mensaje
        message_body = f"Se detectaron problemas en la aplicación a las {results['timestamp']}:\n\n"
        
        for endpoint, data in results["results"].items():
            if not data["success"]:
                message_body += f"- Endpoint {endpoint}: "
                if data["status"] == "Error":
                    message_body += f"Error de conexión - {data.get('error', 'Desconocido')}\n"
                else:
                    message_body += f"Código de estado {data['status']}\n"
        
        message_body += f"\nPor favor, verifica la aplicación en {BASE_URL}"
        
        # Configurar el email - Nota: para usar esto necesitas configurar un servidor SMTP
        # o usar una biblioteca como yagmail para Gmail
        try:
            msg = MIMEText(message_body)
            msg['Subject'] = subject
            msg['From'] = ALERT_EMAIL
            msg['To'] = ALERT_EMAIL
            
            # Comentado para evitar errores si no está configurado
            # with smtplib.SMTP('smtp.gmail.com', 587) as server:
            #     server.starttls()
            #     server.login(SMTP_USER, SMTP_PASSWORD)
            #     server.send_message(msg)
            
            print(f"⚠️ Alerta: Se detectaron problemas. Ver detalles en {LOG_FILE}")
            print(message_body)
        except Exception as e:
            print(f"Error al enviar alerta: {e}")

def main():
    """Función principal para monitorear la aplicación"""
    print(f"Iniciando monitoreo de {BASE_URL}")
    print(f"Intervalo: {CHECK_INTERVAL / 60} minutos")
    print(f"Logs guardados en: {LOG_FILE}")
    
    # Si se pasa --once como argumento, solo ejecutar una vez
    run_once = "--once" in sys.argv
    
    try:
        while True:
            print(f"\nVerificando disponibilidad a las {datetime.datetime.now()}")
            results = check_availability()
            log_results(results)
            
            if results["all_ok"]:
                print("✅ Todos los endpoints están funcionando correctamente")
            else:
                print("❌ Se detectaron problemas en algunos endpoints")
                send_alert(results)
            
            if run_once:
                break
                
            # Esperar hasta la próxima verificación
            print(f"Próxima verificación en {CHECK_INTERVAL / 60} minutos")
            time.sleep(CHECK_INTERVAL)
            
    except KeyboardInterrupt:
        print("\nMonitoreo detenido por el usuario")
    except Exception as e:
        print(f"Error durante el monitoreo: {e}")

if __name__ == "__main__":
    main()
