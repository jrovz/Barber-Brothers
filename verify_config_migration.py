"""
Script de verificación para comprobar que todos los cambios relacionados con
la unificación de configuraciones de región y Secret Manager han sido implementados
correctamente en el proyecto Barber Brothers.
"""
import os
import sys
import importlib
import traceback

# Añadir directorio padre al path para importar módulos de la aplicación
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_module_imports():
    """Verifica que los módulos necesarios se puedan importar"""
    modules_to_check = [
        "app.utils.config_manager",
        "app.utils.cloud_connection_pg",
        "sqlalchemy",
        "google.cloud.secretmanager"
    ]
    
    all_passed = True
    print("Verificando importación de módulos...")
    
    for module in modules_to_check:
        try:
            importlib.import_module(module)
            print(f"✅ Módulo {module} importado correctamente")
        except ImportError as e:
            print(f"❌ Error al importar {module}: {e}")
            all_passed = False
    
    return all_passed

def check_config_manager():
    """Verifica que el módulo config_manager funcione correctamente"""
    try:
        from app.utils.config_manager import (
            get_project_id, get_gcp_region, get_instance_name, 
            get_db_credentials, build_database_url, is_production
        )
        
        print("\nVerificando funciones de config_manager.py...")
        
        # Verificar funciones de configuración de región
        project_id = get_project_id()
        region = get_gcp_region()
        instance = get_instance_name()
        
        print(f"✅ Project ID: {project_id}")
        print(f"✅ Región GCP: {region}")
        print(f"✅ Nombre de instancia: {instance}")
        
        # Verificar entorno
        env = "producción" if is_production() else "desarrollo"
        print(f"✅ Entorno detectado: {env}")
        
        # Verificar credenciales de base de datos
        try:
            db_credentials = get_db_credentials()
            masked_creds = {k: ("***" if k == "password" else v) for k, v in db_credentials.items()}
            print(f"✅ Credenciales de base de datos: {masked_creds}")
            
            # Verificar construcción de URL
            db_url = build_database_url(db_credentials)
            masked_url = db_url.replace(db_credentials.get("password", ""), "***")
            print(f"✅ URL de base de datos: {masked_url}")
            
            return True
        except Exception as e:
            print(f"❌ Error al obtener credenciales: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error al verificar config_manager: {e}")
        traceback.print_exc()
        return False

def check_scripts():
    """Verifica que los scripts principales estén actualizados"""
    scripts_to_check = [
        "scripts/verify_admin_gcp.py",
        "scripts/setup_admin_gcp.py",
        "scripts/test_db_connection.py",
        "verify_db.py"
    ]
    
    print("\nVerificando actualización de scripts...")
    all_passed = True
    
    for script_path in scripts_to_check:
        try:
            with open(script_path, 'r') as f:
                content = f.read()
                
            if "config_manager" in content:
                print(f"✅ {script_path} utiliza el módulo centralizado de configuración")
            else:
                print(f"❌ {script_path} no parece utilizar el módulo centralizado de configuración")
                all_passed = False
        except Exception as e:
            print(f"❌ Error al verificar {script_path}: {e}")
            all_passed = False
    
    return all_passed

def check_secrets_script():
    """Verifica que los scripts de configuración de Secret Manager existan"""
    scripts = [
        "scripts/setup_secrets.sh",
        "scripts/setup_secrets.ps1"
    ]
    
    print("\nVerificando scripts de configuración de Secret Manager...")
    all_passed = True
    
    for script_path in scripts:
        if os.path.exists(script_path):
            print(f"✅ {script_path} existe")
        else:
            print(f"❌ {script_path} no existe")
            all_passed = False
    
    return all_passed

def main():
    """Función principal de verificación"""
    print("=== Verificación de Unificación de Configuraciones en Barber Brothers ===\n")
    
    checks = [
        ("Importación de módulos", check_module_imports),
        ("Configuración centralizada", check_config_manager),
        ("Scripts actualizados", check_scripts),
        ("Scripts de Secret Manager", check_secrets_script)
    ]
    
    results = {}
    for name, check_func in checks:
        print(f"\n--- Verificando: {name} ---")
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"❌ Error durante la verificación: {e}")
            traceback.print_exc()
            results[name] = False
    
    # Resumen final
    print("\n=== Resumen de verificación ===")
    all_passed = True
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\n✅ Todas las verificaciones han pasado correctamente")
        print("La unificación de configuraciones se ha implementado correctamente.")
        return 0
    else:
        print("\n❌ Algunas verificaciones han fallado")
        print("Por favor, revisa los errores y corrige los problemas antes de continuar.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
