#!/usr/bin/env python
"""
Script para exportar la base de datos y prepararla para importación en Azure
"""
import os
import sys
import subprocess
import tempfile

def main():
    print("Preparando base de datos para migración a Azure...")
    
    # Determinar si tenemos acceso a la base de datos actual
    try:
        # Intentar obtener una lista de tablas
        cmd = ["psql", "-c", "\\dt", "barberia_db"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print("No se pudo conectar a la base de datos local.")
            print(result.stderr)
            sys.exit(1)
        
        # Generar archivo SQL de respaldo
        backup_file = os.path.join(tempfile.gettempdir(), "barberia_backup.sql")
        print(f"Exportando a {backup_file}...")
        cmd = ["pg_dump", "-U", "postgres", "-d", "barberia_db", "-f", backup_file]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print("Error al exportar la base de datos.")
            print(result.stderr)
            sys.exit(1)
        
        print(f"Base de datos exportada exitosamente a {backup_file}")
        print("Usa este archivo para importar los datos a la VM de Azure.")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
