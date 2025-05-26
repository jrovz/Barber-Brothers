"""
Script para verificar o crear un usuario administrador

Este script verifica si existe un usuario administrador y lo crea si no existe.
Funciona con base de datos local (SQLite).
"""
import os
import sys
import sqlite3
from werkzeug.security import generate_password_hash
from datetime import datetime

def get_admin_info():
    """
    Función que solicita al usuario la información para crear un administrador
    """
    print("\nIngresa la información para crear un usuario administrador:")
    username = input("Nombre de usuario (admin): ") or "admin"
    email = input("Correo electrónico (admin@barberbrothers.com): ") or "admin@barberbrothers.com"
    password = input("Contraseña (AdminBB2023): ") or "AdminBB2023"
    
    return username, email, password

def create_admin(username="admin", email="admin@barberbrothers.com", password="AdminBB2023"):
    """
    Verifica si existe un usuario administrador y lo crea si no existe
    """
    # Ruta a la base de datos SQLite
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'app.db')
    
    if not os.path.exists(db_path):
        print(f"ERROR: No se encontró la base de datos en {db_path}")
        print("Ejecuta primero 'python setup_local_db.py' para configurar la base de datos local")
        return False
    
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
        
        # Buscar usuarios administradores
        cursor.execute("SELECT id, username, email, role FROM user WHERE role = 'admin'")
        admin_users = cursor.fetchall()
        
        if admin_users:
            print("\nUsuarios administradores existentes:")
            for admin in admin_users:
                print(f"  - ID: {admin[0]}, Usuario: {admin[1]}, Email: {admin[2]}, Rol: {admin[3]}")
            
            update = input("\n¿Deseas crear otro usuario administrador? (s/n): ").lower()
            if update != 's':
                conn.close()
                return True
        
        # Crear un nuevo usuario administrador
        password_hash = generate_password_hash(password)
        now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        
        # Verificar si el usuario ya existe
        cursor.execute("SELECT id, role FROM user WHERE username = ?", (username,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            user_id, role = existing_user
            print(f"\nEl usuario '{username}' ya existe con rol '{role}'")
            
            if role == 'admin':
                print("Ya es administrador. No se realizaron cambios.")
            else:
                update = input(f"¿Quieres actualizar el rol de '{role}' a 'admin'? (s/n): ").lower()
                if update == 's':
                    cursor.execute("UPDATE user SET role = 'admin' WHERE id = ?", (user_id,))
                    conn.commit()
                    print(f"Usuario {username} actualizado con rol de administrador")
        else:
            # Insertar nuevo usuario administrador
            cursor.execute(
                "INSERT INTO user (username, email, password_hash, role, creado) VALUES (?, ?, ?, ?, ?)",
                (username, email, password_hash, 'admin', now)
            )
            conn.commit()
            print(f"\nUsuario administrador '{username}' creado exitosamente")
        
        # Mostrar todos los usuarios
        cursor.execute("SELECT id, username, email, role FROM user")
        users = cursor.fetchall()
        
        print("\nUsuarios en la base de datos:")
        for user in users:
            print(f"  - ID: {user[0]}, Usuario: {user[1]}, Email: {user[2]}, Rol: {user[3]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Si se proporcionan argumentos, usarlos como credenciales
        if len(sys.argv) >= 4:
            create_admin(
                username=sys.argv[1],
                email=sys.argv[2],
                password=sys.argv[3]
            )
        else:
            print("Uso: python check_admin.py <username> <email> <password>")
    else:
        # Interactivo
        create_admin(*get_admin_info())
