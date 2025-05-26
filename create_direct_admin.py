"""
Script para crear un usuario administrador directamente en SQLite
"""
import os
import sys
import sqlite3
from werkzeug.security import generate_password_hash
from datetime import datetime

def create_admin():
    """Crea un usuario administrador en SQLite"""
    username = "admin"
    email = "admin@barberbrothers.com"
    password = "AdminBB2023"
    
    # Ruta a la base de datos SQLite
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'app.db')
    
    if not os.path.exists(db_path):
        print(f"ERROR: No se encontró la base de datos en {db_path}")
        return False
    
    print(f"Base de datos encontrada: {db_path}")
    
    try:
        # Conectar a la base de datos SQLite
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Crear tabla user si no existe
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(64) UNIQUE NOT NULL,
            email VARCHAR(120) UNIQUE NOT NULL,
            password_hash VARCHAR(128),
            role VARCHAR(64),
            creado DATETIME,
            actualizado DATETIME
        )
        """)
        conn.commit()
        
        # Crear usuario admin
        password_hash = generate_password_hash(password)
        now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        
        # Verificar si el usuario ya existe
        cursor.execute("SELECT id, role FROM user WHERE username = ?", (username,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            user_id, role = existing_user
            print(f"El usuario '{username}' ya existe con rol '{role}'")
            
            if role != 'admin':
                cursor.execute("UPDATE user SET role = 'admin' WHERE id = ?", (user_id,))
                conn.commit()
                print(f"Usuario {username} actualizado a administrador")
            else:
                print("Ya es administrador. No se realizaron cambios.")
        else:
            cursor.execute(
                "INSERT INTO user (username, email, password_hash, role, creado) VALUES (?, ?, ?, ?, ?)",
                (username, email, password_hash, 'admin', now)
            )
            conn.commit()
            print(f"Usuario administrador '{username}' creado exitosamente")
        
        # Mostrar información del usuario creado
        cursor.execute("SELECT id, username, email, role FROM user WHERE username = ?", (username,))
        user = cursor.fetchone()
        
        if user:
            print("\nInformación del usuario administrador:")
            print(f"  ID: {user[0]}")
            print(f"  Usuario: {user[1]}")
            print(f"  Email: {user[2]}")
            print(f"  Rol: {user[3]}")
            print(f"  Contraseña: {password}")
            print("\nGuarda esta información en un lugar seguro.")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error al crear usuario administrador: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    create_admin()
