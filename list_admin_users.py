"""
Script para verificar usuarios admin en PostgreSQL usando SQLAlchemy

Este script lista los usuarios administradores en PostgreSQL
"""
import os
import sys
import sqlalchemy
from sqlalchemy import text
from sqlalchemy import create_engine, MetaData, Table, select, inspect

def list_admin_users():
    """
    Lista todos los usuarios administradores en la base de datos PostgreSQL
    """
    try:
        # Obtener la URL de conexión
        db_url = os.environ.get('DATABASE_URL')
        if not db_url or 'postgresql' not in db_url:
            print("ERROR: No se encontró una URL de conexión válida para PostgreSQL")
            print("Establece la variable de entorno DATABASE_URL con el formato:")
            print("  postgresql://usuario:contraseña@servidor:puerto/nombre_db")
            return False
        
        print(f"Usando conexión PostgreSQL: {db_url.split('@')[1] if '@' in db_url else '***OCULTO***'}")
        
        # Crear el motor de SQLAlchemy
        engine = create_engine(db_url)
        
        # Listar tablas
        print("\nTablas en la base de datos:")
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        for table in tables:
            print(f"  - {table}")
        
        # Verificar si existe la tabla user
        if "user" not in tables:
            print("ERROR: La tabla 'user' no existe en la base de datos")
            return False
            
        # Consultar usuarios administradores
        with engine.connect() as connection:
            result = connection.execute(text('SELECT id, username, email, role FROM "user" WHERE role = \'admin\''))
            admin_users = result.fetchall()
            
            if admin_users:
                print("\nUsuarios administradores encontrados:")
                for user in admin_users:
                    print(f"  - ID: {user[0]}, Usuario: {user[1]}, Email: {user[2]}, Rol: {user[3]}")
                return True
            else:
                print("No se encontraron usuarios administradores en la base de datos.")
                return False
    
    except Exception as e:
        print(f"Error al consultar usuarios administradores: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = list_admin_users()
    sys.exit(0 if success else 1)
