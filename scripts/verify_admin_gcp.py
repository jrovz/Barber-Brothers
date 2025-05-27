"""
Script para verificar usuario administrador en PostgreSQL en GCP

Este script se conecta a la base de datos PostgreSQL en Cloud SQL
y verifica si existe el usuario administrador.
Utiliza el módulo centralizado de configuración para acceder a las credenciales.
"""
import os
import sys
import traceback
from sqlalchemy import create_engine, text
from google.cloud.sql.connector import Connector
# Importar módulo de configuración centralizada
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.utils.config_manager import get_project_id, get_gcp_region, get_instance_name, get_secret, get_db_credentials, get_instance_connection_name

def init_connection_engine():
    """
    Inicializa la conexión a Cloud SQL PostgreSQL
    """
    try:
        # Obtener configuración desde el módulo centralizado
        instance_connection_name = get_instance_connection_name()
        print(f"Intentando conexión a: {instance_connection_name}")
        
        # Obtener credenciales de BD desde config_manager
        db_credentials = get_db_credentials()
        db_user = db_credentials["user"]
        db_pass = db_credentials["password"]
        db_name = db_credentials["database"]
        
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
        print(f"Error al conectar a PostgreSQL: {e}")
        traceback.print_exc()
        return None

def verify_admin_user(username="admin"):
    """
    Verifica si existe un usuario administrador con el nombre especificado
    """
    try:
        engine = init_connection_engine()
        
        if not engine:
            print("No se pudo establecer conexión a la base de datos.")
            return False
        
        with engine.connect() as conn:
            # Verificar si existe la tabla de usuarios
            result = conn.execute(text(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'user')"
            ))
            if not result.scalar():
                print("ERROR: La tabla 'user' no existe en la base de datos")
                return False
            
            # Consultar usuario administrador, incluyendo password_hash para verificar que es válido
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
                        print("✅ El usuario tiene permisos de administrador y tiene un hash de contraseña válido")
                        return True
                    else:
                        print("⚠️ El usuario es admin pero no tiene contraseña configurada")
                        return False
                else:
                    print(f"⚠️ El usuario existe pero con rol '{user[3]}' (no es admin)")
                    return False
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
                
                return False
    except Exception as e:
        print(f"Error al verificar usuario administrador: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--all-admins":
            verify_admin_by_role()
        else:
            username = sys.argv[1]
            verify_admin_user(username)
    else:
        print("Verificando usuario admin por defecto...")
        verify_admin_user("admin")
        print("\nVerificando todos los usuarios con rol admin...")
        verify_admin_by_role()

def verify_admin_by_role():
    """
    Verifica si existen usuarios con rol de administrador en la base de datos
    """
    try:
        engine = init_connection_engine()
        
        if not engine:
            print("No se pudo establecer conexión a la base de datos.")
            return False
            
        # Consulta para verificar usuarios administradores
        with engine.connect() as conn:
            query = text("""
                SELECT id, username, email, password_hash, role, creado
                FROM "user"
                WHERE role = 'admin'
            """)
            
            result = conn.execute(query)
            admin_users = result.fetchall()
            
            if not admin_users:
                print("No se encontraron usuarios administradores en la base de datos.")
                return False
                
            print(f"Se encontraron {len(admin_users)} usuarios administradores:")
            for user in admin_users:
                has_password = user[3] is not None and len(user[3]) > 0
                print(f"ID: {user[0]}, Usuario: {user[1]}, Email: {user[2]}, Contraseña configurada: {has_password}, Rol: {user[4]}, Creado: {user[5]}")
                
            return True
    except Exception as e:
        print(f"Error al verificar usuarios administradores: {e}")
        traceback.print_exc()
        return False
