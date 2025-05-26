#!/usr/bin/env python
"""
Script para verificar y arreglar problemas de autenticación de administrador en GCP

Este script se conecta a la base de datos PostgreSQL en Cloud SQL,
verifica si existe el usuario administrador y corrige cualquier problema encontrado.
"""
import os
import sys
import argparse
import traceback
from sqlalchemy import create_engine, text
from werkzeug.security import generate_password_hash
import time

def init_cloud_sql_connection():
    """
    Inicializa la conexión a Cloud SQL PostgreSQL
    """
    try:
        # Intentar importar el conector de Cloud SQL
        from google.cloud.sql.connector import Connector
        
        # Obtener los parámetros de conexión
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
        
        # Verificar la conexión
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            if result.scalar() == 1:
                print("✅ Conexión a PostgreSQL establecida correctamente")
            else:
                print("❌ Error en la conexión a PostgreSQL")
                return None
        
        return engine
    except ImportError:
        print("❌ Error: El conector de Cloud SQL no está instalado")
        print("Ejecute: pip install cloud-sql-python-connector")
        return None
    except Exception as e:
        print(f"❌ Error al conectar a PostgreSQL: {e}")
        traceback.print_exc()
        return None

def verify_user_table(engine):
    """
    Verifica si la tabla 'user' existe y tiene la estructura correcta
    """
    try:
        with engine.connect() as conn:
            # Verificar si la tabla existe
            result = conn.execute(text(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'user')"
            ))
            if not result.scalar():
                print("❌ La tabla 'user' no existe en la base de datos")
                return False
            
            # Verificar columnas
            result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'user'"))
            columns = [r[0] for r in result.fetchall()]
            
            required_columns = ['id', 'username', 'email', 'password_hash', 'role']
            for col in required_columns:
                if col.lower() not in [c.lower() for c in columns]:
                    print(f"❌ La columna '{col}' no existe en la tabla 'user'")
                    return False
            
            print("✅ La tabla 'user' existe y tiene la estructura correcta")
            return True
    except Exception as e:
        print(f"❌ Error al verificar la tabla 'user': {e}")
        traceback.print_exc()
        return False

def check_admin_user(engine, username="admin"):
    """
    Verifica si existe un usuario administrador
    """
    try:
        with engine.connect() as conn:
            # Consultar usuario administrador
            result = conn.execute(
                text('SELECT id, username, email, role, password_hash FROM "user" WHERE username = :username'),
                {"username": username}
            )
            user = result.fetchone()
            
            if user:
                print("\nUsuario encontrado:")
                print(f"  ID: {user[0]}")
                print(f"  Username: {user[1]}")
                print(f"  Email: {user[2]}")
                print(f"  Role: {user[3]}")
                print(f"  Password Hash existe: {'Sí' if user[4] else 'No'}")
                
                # Verificar si es administrador
                if user[3] == 'admin':
                    if user[4]:  # Si tiene password_hash
                        print("✅ El usuario administrador existe y tiene un hash de contraseña")
                        return "ok"
                    else:
                        print("⚠️ El usuario es admin pero no tiene contraseña configurada")
                        return "no_password"
                else:
                    print(f"⚠️ El usuario existe pero con rol '{user[3]}' (no es admin)")
                    return "wrong_role"
            else:
                print(f"❌ No se encontró ningún usuario con username '{username}'")
                
                # Listar todos los usuarios para referencia
                result = conn.execute(text('SELECT id, username, email, role FROM "user"'))
                users = result.fetchall()
                
                if users:
                    print("\nUsuarios en la base de datos:")
                    for u in users:
                        print(f"  - ID: {u[0]}, Usuario: {u[1]}, Email: {u[2]}, Rol: {u[3]}")
                else:
                    print("No hay usuarios en la base de datos.")
                
                return "not_found"
    except Exception as e:
        print(f"❌ Error al verificar usuario administrador: {e}")
        traceback.print_exc()
        return "error"

def reset_admin_password(engine, username="admin", password="admin123"):
    """
    Restablece la contraseña del usuario administrador
    """
    try:
        # Generar hash de la nueva contraseña
        password_hash = generate_password_hash(password)
        
        with engine.connect() as conn:
            # Verificar si el usuario existe
            result = conn.execute(
                text('SELECT id FROM "user" WHERE username = :username'),
                {"username": username}
            )
            user = result.fetchone()
            
            if user:
                # Actualizar contraseña
                conn.execute(
                    text('UPDATE "user" SET password_hash = :password_hash WHERE username = :username'),
                    {"password_hash": password_hash, "username": username}
                )
                conn.commit()
                
                print(f"✅ Contraseña restablecida para el usuario '{username}'")
                print(f"   Nueva contraseña: {password}")
                return True
            else:
                print(f"❌ No se encontró el usuario '{username}'")
                return False
    except Exception as e:
        print(f"❌ Error al restablecer la contraseña: {e}")
        traceback.print_exc()
        return False

def update_user_role(engine, username="admin", role="admin"):
    """
    Actualiza el rol de un usuario existente a administrador
    """
    try:
        with engine.connect() as conn:
            # Verificar si el usuario existe
            result = conn.execute(
                text('SELECT id FROM "user" WHERE username = :username'),
                {"username": username}
            )
            user = result.fetchone()
            
            if user:
                # Actualizar rol
                conn.execute(
                    text('UPDATE "user" SET role = :role WHERE username = :username'),
                    {"role": role, "username": username}
                )
                conn.commit()
                
                print(f"✅ Rol actualizado para el usuario '{username}' a '{role}'")
                return True
            else:
                print(f"❌ No se encontró el usuario '{username}'")
                return False
    except Exception as e:
        print(f"❌ Error al actualizar el rol del usuario: {e}")
        traceback.print_exc()
        return False

def create_admin_user(engine, username="admin", email="admin@example.com", password="admin123"):
    """
    Crea un nuevo usuario administrador
    """
    try:
        # Generar hash de la contraseña
        password_hash = generate_password_hash(password)
        
        with engine.connect() as conn:
            # Verificar si el usuario ya existe
            result = conn.execute(
                text('SELECT id FROM "user" WHERE username = :username OR email = :email'),
                {"username": username, "email": email}
            )
            existing_user = result.fetchone()
            
            if existing_user:
                print(f"⚠️ Ya existe un usuario con el username '{username}' o email '{email}'")
                return False
            
            # Crear nuevo usuario administrador
            conn.execute(
                text('INSERT INTO "user" (username, email, password_hash, role) VALUES (:username, :email, :password_hash, :role)'),
                {
                    "username": username,
                    "email": email,
                    "password_hash": password_hash,
                    "role": "admin"
                }
            )
            conn.commit()
            
            print(f"✅ Usuario administrador creado exitosamente:")
            print(f"   Username: {username}")
            print(f"   Email: {email}")
            print(f"   Contraseña: {password}")
            return True
    except Exception as e:
        print(f"❌ Error al crear usuario administrador: {e}")
        traceback.print_exc()
        return False

def fix_admin_auth(engine, username="admin", email="admin@example.com", password="admin123"):
    """
    Verifica y corrige problemas de autenticación de administrador
    """
    if not verify_user_table(engine):
        print("❌ La tabla de usuarios no existe o no tiene la estructura correcta")
        return False
    
    # Verificar usuario administrador
    admin_status = check_admin_user(engine, username)
    
    if admin_status == "ok":
        # El usuario existe y es admin con contraseña
        print("✅ El usuario administrador está configurado correctamente")
        return True
    elif admin_status == "no_password":
        # El usuario existe pero no tiene contraseña
        print("⚠️ Restableciendo contraseña para el usuario administrador...")
        return reset_admin_password(engine, username, password)
    elif admin_status == "wrong_role":
        # El usuario existe pero no es admin
        print("⚠️ Actualizando rol del usuario a administrador...")
        if update_user_role(engine, username, "admin"):
            return reset_admin_password(engine, username, password)
        return False
    elif admin_status == "not_found":
        # El usuario no existe
        print("⚠️ Creando nuevo usuario administrador...")
        return create_admin_user(engine, username, email, password)
    else:
        # Error
        print("❌ No se pudo verificar el usuario administrador")
        return False

def main():
    # Configurar argumentos de línea de comandos
    parser = argparse.ArgumentParser(description='Verificar y corregir problemas de autenticación de administrador en GCP')
    parser.add_argument('--username', default='admin', help='Nombre de usuario (default: admin)')
    parser.add_argument('--email', default='admin@example.com', help='Email del usuario (default: admin@example.com)')
    parser.add_argument('--password', default='admin123', help='Contraseña (default: admin123)')
    parser.add_argument('--verify-only', action='store_true', help='Solo verificar, no hacer cambios')
    
    args = parser.parse_args()
    
    # Inicializar conexión a Cloud SQL
    print("Conectando a Cloud SQL PostgreSQL...")
    engine = init_cloud_sql_connection()
    
    if not engine:
        print("❌ No se pudo establecer conexión a la base de datos")
        return 1
    
    if args.verify_only:
        print("Verificando usuario administrador...")
        admin_status = check_admin_user(engine, args.username)
        return 0 if admin_status == "ok" else 1
    else:
        print("Verificando y corrigiendo problemas de autenticación...")
        success = fix_admin_auth(engine, args.username, args.email, args.password)
        
        if success:
            print("\n✅ La configuración del usuario administrador se ha completado exitosamente")
            print(f"   Username: {args.username}")
            print(f"   Contraseña: {args.password}")
            return 0
        else:
            print("\n❌ No se pudieron corregir todos los problemas de autenticación")
            return 1

if __name__ == "__main__":
    sys.exit(main())
