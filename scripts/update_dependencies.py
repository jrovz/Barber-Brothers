"""
Script para instalar las dependencias necesarias para todos los scripts
del proyecto Barber Brothers y verificar que estén instaladas correctamente.
"""
import subprocess
import sys
import os
import importlib
import pkg_resources

# Lista de dependencias requeridas
dependencies = [
    "sqlalchemy",
    "pg8000",
    "google-cloud-secret-manager",
    "google-cloud-sql-connector",
    "werkzeug",
    "alembic",
    "flask",
    "flask-sqlalchemy",
    "gunicorn",
    "psycopg2-binary",
    "requests"
]

def check_dependency(package_name):
    """Verifica si una dependencia está instalada"""
    try:
        importlib.import_module(package_name.replace('-', '_'))
        print(f"✅ {package_name} está instalado")
        return True
    except ImportError:
        try:
            # Intentar verificar con pkg_resources (para paquetes con guiones)
            pkg_resources.get_distribution(package_name)
            print(f"✅ {package_name} está instalado")
            return True
        except pkg_resources.DistributionNotFound:
            print(f"❌ {package_name} no está instalado")
            return False

def install_dependency(package_name):
    """Instala una dependencia utilizando pip"""
    print(f"Instalando {package_name}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        return True
    except subprocess.CalledProcessError:
        print(f"Error al instalar {package_name}")
        return False

def main():
    """Función principal"""
    print("Verificando dependencias para Barber Brothers...")
    
    # Crear lista de dependencias faltantes
    missing_dependencies = []
    for dep in dependencies:
        if not check_dependency(dep):
            missing_dependencies.append(dep)
    
    # Instalar dependencias faltantes
    if missing_dependencies:
        print("\nSe encontraron dependencias faltantes. Instalando...")
        for dep in missing_dependencies:
            install_dependency(dep)
        
        # Verificar nuevamente
        print("\nVerificando instalación de dependencias...")
        all_installed = True
        for dep in missing_dependencies:
            if not check_dependency(dep):
                all_installed = False
        
        if all_installed:
            print("\n✅ Todas las dependencias han sido instaladas correctamente.")
        else:
            print("\n❌ Algunas dependencias no pudieron ser instaladas.")
    else:
        print("\n✅ Todas las dependencias necesarias ya están instaladas.")
    
    # Actualizar requirements.txt
    update_requirements = input("\n¿Deseas actualizar el archivo requirements.txt con estas dependencias? (s/n): ")
    if update_requirements.lower() == 's':
        with open('requirements.txt', 'r') as f:
            current_requirements = f.read()
        
        # Verificar qué dependencias no están en el archivo
        new_dependencies = []
        for dep in dependencies:
            if dep not in current_requirements:
                new_dependencies.append(dep)
        
        # Agregar nuevas dependencias
        if new_dependencies:
            with open('requirements.txt', 'a') as f:
                f.write("\n# Dependencias agregadas automáticamente\n")
                for dep in new_dependencies:
                    f.write(f"{dep}\n")
            print(f"✅ Se agregaron {len(new_dependencies)} nuevas dependencias a requirements.txt")
        else:
            print("✅ Todas las dependencias ya están en requirements.txt")

if __name__ == "__main__":
    main()
