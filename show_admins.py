"""
Script para mostrar información de usuarios administradores en SQLite
"""
import os
import sys
import sqlite3

def show_admins():
    """Muestra información de usuarios administradores en SQLite"""
    
    # Ruta a la base de datos SQLite
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'app.db')
    
    if not os.path.exists(db_path):
        print(f"ERROR: No se encontró la base de datos en {db_path}")
        print("Ejecuta primero 'python setup_local_db.py' para configurar la base de datos local")
        return False
    
    print(f"Base de datos encontrada: {db_path} ({os.path.getsize(db_path)} bytes)")
    
    try:
        # Conectar a la base de datos SQLite
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar si existe la tabla user
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user'")
        if not cursor.fetchone():
            print("ERROR: La tabla 'user' no existe en la base de datos")
            conn.close()
            return False
        
        # Mostrar todos los usuarios
        print("\nTodos los usuarios en la base de datos:")
        cursor.execute("SELECT id, username, email, role FROM user")
        users = cursor.fetchall()
        
        if not users:
            print("No hay usuarios en la base de datos.")
        else:
            for user in users:
                print(f"  - ID: {user[0]}, Usuario: {user[1]}, Email: {user[2]}, Rol: {user[3]}")
        
        # Buscar usuarios administradores
        cursor.execute("SELECT id, username, email, role FROM user WHERE role = 'admin'")
        admin_users = cursor.fetchall()
        
        print("\nUsuarios administradores:")
        if not admin_users:
            print("No hay usuarios administradores en la base de datos.")
            print("\nPuedes crear un administrador con el siguiente comando:")
            print("python create_admin_sqlite.py admin admin@barberbrothers.com AdminBB2023")
        else:
            for admin in admin_users:
                print(f"  - ID: {admin[0]}, Usuario: {admin[1]}, Email: {admin[2]}, Rol: {admin[3]}")
            print("\nPuedes acceder con cualquiera de estos usuarios administradores.")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error al consultar la base de datos: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    show_admins()
