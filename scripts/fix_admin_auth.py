"""
Script para reparar problemas comunes en autenticación de administrador

Este script intenta identificar y corregir problemas comunes relacionados con
la autenticación de administradores en la aplicación Flask.
"""
import os
import sys
import argparse
from sqlalchemy import create_engine, text
from werkzeug.security import generate_password_hash
import traceback

def get_db_connection_string():
    """Devuelve la cadena de conexión a la base de datos según el entorno"""
    # Verificar si estamos en GCP
    if os.environ.get("GAE_ENV") == "standard" or os.environ.get("K_SERVICE"):
        # Este script debe ejecutarse localmente pero con credenciales para acceder a GCP
        print("Configurando para base de datos PostgreSQL en GCP")
        try:
            from google.cloud.sql.connector import Connector

            project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "barber-brothers-460514")
            region = os.environ.get("CLOUD_SQL_REGION", "us-central1")
            instance_name = os.environ.get("CLOUD_SQL_INSTANCE", "barberia-db")
            
            instance_connection_name = f"{project_id}:{region}:{instance_name}"
            print(f"Intentando conexión a: {instance_connection_name}")
            
            db_user = os.environ.get("DB_USER", "barberia_user")
            db_pass = os.environ.get("DB_PASS", "")
            db_name = os.environ.get("DB_NAME", "barberia_db")
            
            connector = Connector()
            
            def getconn():
                conn = connector.connect(
                    instance_connection_name,
                    "pg8000",
                    user=db_user,
                    password=db_pass,
                    db=db_name
                )
                return conn
            
            engine = create_engine(
                "postgresql+pg8000://",
                creator=getconn,
            )
            
            print("Conexión a PostgreSQL establecida")
            return engine
        except Exception as e:
            print(f"Error al conectar a PostgreSQL en GCP: {e}")
            traceback.print_exc()
            return None
    else:
        # Entorno local - SQLite
        print("Configurando para base de datos SQLite local")
        basedir = os.path.abspath(os.path.dirname(__file__))
        db_path = os.path.join(os.path.dirname(basedir), 'instance', 'app.db')
        
        if not os.path.exists(db_path):
            print(f"Error: No se encontró la base de datos local en {db_path}")
            return None
            
        try:
            engine = create_engine(f'sqlite:///{db_path}')
            print(f"Conexión a SQLite establecida: {db_path}")
            return engine
        except Exception as e:
            print(f"Error al conectar a SQLite: {e}")
            return None

def check_admin_table():
    """Verifica si la tabla de usuarios existe y tiene la estructura correcta"""
    engine = get_db_connection_string()
    if not engine:
        return False
        
    try:
        with engine.connect() as conn:
            # Verificar si la tabla existe
            dialect = engine.dialect.name
            
            if dialect == 'sqlite':
                query = text("SELECT name FROM sqlite_master WHERE type='table' AND name='user'")
                result = conn.execute(query)
                if not result.scalar():
                    print("La tabla 'user' no existe en la base de datos SQLite")
                    return False
            else:  # PostgreSQL
                query = text("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'user')")
                result = conn.execute(query)
                if not result.scalar():
                    print("La tabla 'user' no existe en la base de datos PostgreSQL")
                    return False
            
            # Verificar columnas
            if dialect == 'sqlite':
                query = text("PRAGMA table_info(user)")
            else:  # PostgreSQL
                query = text("SELECT column_name FROM information_schema.columns WHERE table_name = 'user'")
                
            result = conn.execute(query)
            columns = [r[0] if dialect == 'sqlite' else r[0] for r in result.fetchall()]
            
            required_columns = ['id', 'username', 'email', 'password_hash', 'role']
            for col in required_columns:
                if col.lower() not in [c.lower() for c in columns]:
                    print(f"La columna '{col}' no existe en la tabla 'user'")
                    return False
            
            print("✅ La tabla 'user' existe y tiene la estructura correcta")
            return True
            
    except Exception as e:
        print(f"Error al verificar la tabla de usuarios: {e}")
        traceback.print_exc()
        return False

def reset_admin_password(username="admin", password="admin123"):
    """Restablece la contraseña del usuario administrador especificado"""
    engine = get_db_connection_string()
    if not engine:
        return False
        
    try:
        # Generar hash de la nueva contraseña
        password_hash = generate_password_hash(password)
        
        with engine.connect() as conn:
            # Verificar si el usuario existe
            query = text('SELECT id, username, email, role FROM "user" WHERE username = :username')
            result = conn.execute(query, {"username": username})
            user = result.fetchone()
            
            if user:
                print(f"Usuario encontrado: {user[1]}, Email: {user[2]}, Rol: {user[3]}")
                
                # Actualizar contraseña
                query = text('UPDATE "user" SET password_hash = :password_hash WHERE username = :username')
                conn.execute(query, {"password_hash": password_hash, "username": username})
                conn.commit()
                
                print(f"✅ Contraseña restablecida para el usuario '{username}'")
                print(f"   Nueva contraseña: {password}")
                return True
            else:
                print(f"❌ No se encontró el usuario '{username}'")
                return False
    except Exception as e:
        print(f"Error al restablecer la contraseña: {e}")
        traceback.print_exc()
        return False

def create_admin_user(username="admin", email="admin@example.com", password="admin123"):
    """Crea un nuevo usuario administrador si no existe"""
    engine = get_db_connection_string()
    if not engine:
        return False
        
    try:
        # Generar hash de la contraseña
        password_hash = generate_password_hash(password)
        
        with engine.connect() as conn:
            # Verificar si el usuario ya existe
            query = text('SELECT id FROM "user" WHERE username = :username OR email = :email')
            result = conn.execute(query, {"username": username, "email": email})
            existing_user = result.fetchone()
            
            if existing_user:
                print(f"Ya existe un usuario con el username '{username}' o email '{email}'")
                return False
                
            # Crear nuevo usuario administrador
            dialect = engine.dialect.name
            if dialect == 'sqlite':
                query = text("""
                    INSERT INTO user (username, email, password_hash, role) 
                    VALUES (:username, :email, :password_hash, 'admin')
                """)
            else:  # PostgreSQL
                query = text("""
                    INSERT INTO "user" (username, email, password_hash, role) 
                    VALUES (:username, :email, :password_hash, 'admin')
                """)
                
            conn.execute(query, {
                "username": username,
                "email": email,
                "password_hash": password_hash
            })
            conn.commit()
            
            print(f"✅ Usuario administrador creado exitosamente:")
            print(f"   Username: {username}")
            print(f"   Email: {email}")
            print(f"   Contraseña: {password}")
            return True
    except Exception as e:
        print(f"Error al crear usuario administrador: {e}")
        traceback.print_exc()
        return False

def main():
    parser = argparse.ArgumentParser(description='Reparar problemas de autenticación de administrador')
    parser.add_argument('--check', action='store_true', help='Verificar la estructura de la tabla de usuarios')
    parser.add_argument('--reset-password', action='store_true', help='Restablecer contraseña de administrador')
    parser.add_argument('--create-admin', action='store_true', help='Crear un nuevo usuario administrador')
    parser.add_argument('--username', default='admin', help='Nombre de usuario (default: admin)')
    parser.add_argument('--email', default='admin@example.com', help='Email del usuario (para crear)')
    parser.add_argument('--password', default='admin123', help='Contraseña (default: admin123)')
    
    args = parser.parse_args()
    
    if not (args.check or args.reset_password or args.create_admin):
        parser.print_help()
        return
    
    if args.check:
        check_admin_table()
    
    if args.reset_password:
        reset_admin_password(args.username, args.password)
    
    if args.create_admin:
        create_admin_user(args.username, args.email, args.password)
        
if __name__ == "__main__":
    main()
