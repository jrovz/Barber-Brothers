"""
Script para crear un usuario administrador directamente en la base de datos SQLite
"""
import os
import sys
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash

def create_admin_user(username="admin", email="admin@barberbrothers.com", password="adminBB2025"):
    """
    Crear un usuario administrador directamente en la base de datos SQLite
    """
    # Ruta a la base de datos
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'app.db')
    
    print(f"Intentando conectar a la base de datos SQLite: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"ERROR: No se encontró la base de datos en {db_path}")
        print("Ejecuta primero 'python setup_local_db.py' para configurar la base de datos")
        return False
        
    print(f"Base de datos encontrada: {db_path} ({os.path.getsize(db_path)} bytes)")
    
    try:
        # Conectar a la base de datos SQLite
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Listar todas las tablas en la base de datos
        print("\nTablas en la base de datos:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        for table in tables:
            print(f"  - {table[0]}")
            
        # Verificar si la tabla user existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user';")
        if not cursor.fetchone():
            print("ERROR: La tabla 'user' no existe en la base de datos")
            conn.close()
            return False
            
        # Verificar si el usuario ya existe
        cursor.execute("SELECT id, role FROM user WHERE username = ?", (username,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            user_id, role = existing_user
            print(f"El usuario '{username}' ya existe con ID {user_id} y rol '{role}'")
            
            if role == 'admin':
                print("Ya es administrador. No se realizaron cambios.")
            else:
                print(f"Actualizando rol de usuario de '{role}' a 'admin'")
                cursor.execute("UPDATE user SET role = 'admin' WHERE id = ?", (user_id,))
                conn.commit()
                print(f"Usuario {username} actualizado con rol de administrador")
        else:
            # Crear un nuevo usuario admin
            now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            password_hash = generate_password_hash(password)
            
            cursor.execute(
                "INSERT INTO user (username, email, password_hash, role, creado) VALUES (?, ?, ?, ?, ?)",
                (username, email, password_hash, 'admin', now)
            )
            conn.commit()
            
            print(f"Usuario administrador '{username}' creado exitosamente")
            
        # Mostrar todos los usuarios para verificar
        print("\nUsuarios en la base de datos:")
        cursor.execute("SELECT id, username, email, role FROM user")
        users = cursor.fetchall()
        
        for user in users:
            print(f"  - ID: {user[0]}, Usuario: {user[1]}, Email: {user[2]}, Rol: {user[3]}")
            
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error al crear usuario administrador: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Si se proporcionan argumentos, usarlos como credenciales
        if len(sys.argv) >= 4:
            success = create_admin_user(
                username=sys.argv[1], 
                email=sys.argv[2], 
                password=sys.argv[3]
            )
        else:
            print("Uso: python create_admin_sqlite.py <username> <email> <password>")
            sys.exit(1)
    else:
        # Usar valores predeterminados
        success = create_admin_user()
    
    sys.exit(0 if success else 1)
