"""
Script para configurar la cuenta de administrador en GCP PostgreSQL

Este script es una versión modificada del fix_admin_auth.py, enfocada en
configurar correctamente la cuenta de administrador en la base de datos PostgreSQL en GCP.
"""
import os
import sys
import argparse
import logging
from sqlalchemy import create_engine, text
from werkzeug.security import generate_password_hash
import traceback

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("setup_admin_gcp")

def get_pg_connection_url():
    """
    Construye la URL de conexión para PostgreSQL en GCP
    """
    # Obtener variables de entorno para la conexión
    db_user = os.environ.get("DB_USER", "barberia_user")
    db_pass = os.environ.get("DB_PASS", "")
    db_name = os.environ.get("DB_NAME", "barberia_db")
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "barber-brothers-460514")
    
    # Formato recomendado para conexión con Cloud SQL Proxy
    region = os.environ.get("CLOUD_SQL_REGION", "us-central1")
    instance = os.environ.get("CLOUD_SQL_INSTANCE", "barberia-db")
    instance_connection_name = f"{project_id}:{region}:{instance}"
    
    # Comprobar si las variables obligatorias están definidas
    if not db_pass:
        logger.error("DB_PASS no está definido. Establece esta variable de entorno.")
        return None
    
    # Crear URL de conexión para PostgreSQL con Cloud SQL Proxy
    connection_url = f"postgresql://{db_user}:{db_pass}@localhost:5432/{db_name}"
    logger.info(f"URL de conexión: {connection_url} para instancia {instance_connection_name}")
    
    return connection_url, instance_connection_name

def connect_to_gcp_postgres():
    """
    Establece conexión a PostgreSQL en GCP
    """
    try:
        connection_info = get_pg_connection_url()
        if not connection_info:
            return None
        
        connection_url, instance_name = connection_info
        
        # Verificar si está instalado cloud-sql-python-connector
        try:
            from google.cloud.sql.connector import Connector
            logger.info("Usando google.cloud.sql.connector para la conexión")
            
            # Crear conexión usando el conector
            connector = Connector()
            
            def getconn():
                conn = connector.connect(
                    instance_name,
                    "pg8000",
                    user=os.environ.get("DB_USER", "barberia_user"),
                    password=os.environ.get("DB_PASS", ""),
                    db=os.environ.get("DB_NAME", "barberia_db")
                )
                return conn
            
            engine = create_engine(
                "postgresql+pg8000://",
                creator=getconn
            )
            
            # Verificar conexión
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                if result.scalar() == 1:
                    logger.info("Conexión a PostgreSQL establecida exitosamente")
                    return engine
                else:
                    logger.error("Error en la consulta de prueba de conexión")
                    return None
                
        except ImportError:
            logger.warning("google.cloud.sql.connector no está instalado, intentando conexión directa")
            # Fallback a conexión directa si el conector no está disponible
            engine = create_engine(connection_url)
            
            # Verificar conexión
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                if result.scalar() == 1:
                    logger.info("Conexión directa a PostgreSQL establecida exitosamente")
                    return engine
                else:
                    logger.error("Error en la consulta de prueba de conexión directa")
                    return None
    except Exception as e:
        logger.error(f"Error al conectar a PostgreSQL: {e}")
        traceback.print_exc()
        return None

def setup_admin_user(engine, username="admin", email="admin@example.com", password="admin123", force_reset=False):
    """
    Configura o actualiza el usuario administrador en la base de datos
    """
    try:
        # Generar hash de la contraseña
        password_hash = generate_password_hash(password)
        
        with engine.connect() as conn:
            # Verificar si existe la tabla user
            result = conn.execute(text(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'user')"
            ))
            
            if not result.scalar():
                logger.error("La tabla 'user' no existe en la base de datos")
                logger.info("¿Has ejecutado las migraciones de la base de datos?")
                return False
            
            # Verificar si el usuario existe
            result = conn.execute(
                text('SELECT id, username, email, role FROM "user" WHERE username = :username'),
                {"username": username}
            )
            user = result.fetchone()
            
            if user:
                logger.info(f"Usuario encontrado: {user[1]}, Email: {user[2]}, Rol: {user[3]}")
                
                # Si el usuario existe pero no es admin, actualizar rol
                if user[3] != 'admin':
                    logger.info(f"Actualizando rol de '{user[3]}' a 'admin'")
                    conn.execute(
                        text('UPDATE "user" SET role = :role WHERE username = :username'),
                        {"role": "admin", "username": username}
                    )
                    conn.commit()
                
                # Si se solicita resetear la contraseña o forzar el reset
                if force_reset:
                    logger.info("Actualizando contraseña del usuario existente")
                    conn.execute(
                        text('UPDATE "user" SET password_hash = :password_hash WHERE username = :username'),
                        {"password_hash": password_hash, "username": username}
                    )
                    conn.commit()
                    logger.info(f"✅ Contraseña actualizada para el usuario '{username}'")
                else:
                    logger.info(f"Usuario '{username}' existe y no se ha modificado la contraseña")
                
                return True
            else:
                logger.info(f"Usuario '{username}' no encontrado, creando nuevo usuario administrador")
                
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
                
                logger.info(f"✅ Usuario administrador creado exitosamente:")
                logger.info(f"   Username: {username}")
                logger.info(f"   Email: {email}")
                logger.info(f"   Contraseña: {password}")
                return True
    except Exception as e:
        logger.error(f"Error al configurar usuario administrador: {e}")
        traceback.print_exc()
        return False

def verify_admin_user(engine, username="admin"):
    """
    Verifica si existe un usuario administrador con permisos correctos
    """
    try:
        with engine.connect() as conn:
            # Verificar si existe la tabla user
            result = conn.execute(text(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'user')"
            ))
            
            if not result.scalar():
                logger.error("La tabla 'user' no existe en la base de datos")
                return False
            
            # Consultar usuario
            result = conn.execute(
                text('SELECT id, username, email, role, password_hash FROM "user" WHERE username = :username'),
                {"username": username}
            )
            user = result.fetchone()
            
            if user:
                logger.info(f"Usuario encontrado: ID={user[0]}, Username={user[1]}, Email={user[2]}, Rol={user[3]}")
                has_password = user[4] is not None and user[4] != ''
                
                if user[3] == 'admin' and has_password:
                    logger.info(f"✅ El usuario '{username}' tiene rol de administrador y contraseña configurada")
                    return True
                elif user[3] != 'admin':
                    logger.warning(f"⚠️ El usuario '{username}' existe pero tiene rol '{user[3]}' (no es admin)")
                    return False
                elif not has_password:
                    logger.warning(f"⚠️ El usuario '{username}' es admin pero no tiene contraseña configurada")
                    return False
            else:
                logger.warning(f"❌ No se encontró el usuario '{username}'")
                return False
    except Exception as e:
        logger.error(f"Error al verificar usuario: {e}")
        traceback.print_exc()
        return False

def main():
    parser = argparse.ArgumentParser(description='Configurar usuario administrador en GCP PostgreSQL')
    parser.add_argument('--username', default='admin', help='Nombre de usuario (default: admin)')
    parser.add_argument('--email', default='admin@example.com', help='Email del usuario (default: admin@example.com)')
    parser.add_argument('--password', default='admin123', help='Contraseña (default: admin123)')
    parser.add_argument('--force-reset', action='store_true', help='Forzar actualización de la contraseña si el usuario ya existe')
    parser.add_argument('--verify-only', action='store_true', help='Solo verificar si el usuario existe con permisos correctos')
    
    args = parser.parse_args()
    
    # Mostrar un encabezado
    print("\n" + "="*80)
    print(" CONFIGURACIÓN DE USUARIO ADMINISTRADOR EN POSTGRESQL (GCP) ".center(80, "="))
    print("="*80 + "\n")
    
    # Conectar a la base de datos
    logger.info("Conectando a PostgreSQL en GCP...")
    engine = connect_to_gcp_postgres()
    
    if not engine:
        logger.error("No se pudo establecer conexión a la base de datos PostgreSQL")
        return 1
    
    if args.verify_only:
        logger.info(f"Verificando usuario administrador '{args.username}'...")
        if verify_admin_user(engine, args.username):
            print("\n" + "="*80)
            print(" ✅ VERIFICACIÓN EXITOSA ".center(80, "="))
            print("="*80)
            print(f"\nEl usuario '{args.username}' existe como administrador y tiene contraseña configurada.\n")
            return 0
        else:
            print("\n" + "="*80)
            print(" ❌ VERIFICACIÓN FALLIDA ".center(80, "="))
            print("="*80)
            print(f"\nEl usuario '{args.username}' no existe o no tiene los permisos correctos.\n")
            print("Ejecuta este script sin la opción --verify-only para corregir el problema.")
            return 1
    else:
        logger.info(f"Configurando usuario administrador '{args.username}'...")
        if setup_admin_user(engine, args.username, args.email, args.password, args.force_reset):
            # Verificar que todo quedó bien configurado
            if verify_admin_user(engine, args.username):
                print("\n" + "="*80)
                print(" ✅ CONFIGURACIÓN EXITOSA ".center(80, "="))
                print("="*80)
                print(f"\nEl usuario administrador '{args.username}' ha sido configurado correctamente.")
                print(f"La contraseña se ha establecido como: {args.password}")
                print("\nYa puedes iniciar sesión en el panel de administración con estas credenciales.\n")
                return 0
            else:
                print("\n" + "="*80)
                print(" ⚠️ VERIFICACIÓN POSTERIOR FALLIDA ".center(80, "="))
                print("="*80)
                print("\nEl usuario se configuró pero la verificación posterior falló.")
                print("Revisa los logs para más detalles.\n")
                return 1
        else:
            print("\n" + "="*80)
            print(" ❌ CONFIGURACIÓN FALLIDA ".center(80, "="))
            print("="*80)
            print("\nNo se pudo configurar el usuario administrador.")
            print("Revisa los logs para más detalles.\n")
            return 1

if __name__ == "__main__":
    sys.exit(main())
