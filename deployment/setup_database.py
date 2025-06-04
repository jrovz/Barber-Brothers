#!/usr/bin/env python3
"""
Script para configurar y verificar la base de datos PostgreSQL en producción
Ejecutar en el servidor VPS después de la instalación inicial
"""

import os
import sys
import subprocess
import psycopg2
from psycopg2 import sql
import time
from datetime import datetime

# Colores para output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_status(message):
    print(f"{Colors.GREEN}[INFO]{Colors.END} {message}")

def print_warning(message):
    print(f"{Colors.YELLOW}[WARNING]{Colors.END} {message}")

def print_error(message):
    print(f"{Colors.RED}[ERROR]{Colors.END} {message}")

def print_header(message):
    print(f"\n{Colors.BLUE}{'='*50}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{message}{Colors.END}")
    print(f"{Colors.BLUE}{'='*50}{Colors.END}\n")

# Configuración de la base de datos
DB_CONFIG = {
    'host': 'localhost',
    'port': '5432',
    'database': 'barber_brothers_db',
    'user': 'barber_user',
    'password': 'barber_password_2024'
}

def check_postgresql_service():
    """Verificar que PostgreSQL esté ejecutándose"""
    print_header("VERIFICANDO SERVICIO POSTGRESQL")
    
    try:
        result = subprocess.run(['systemctl', 'is-active', 'postgresql'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print_status("✅ PostgreSQL está activo")
            return True
        else:
            print_error("❌ PostgreSQL no está activo")
            print_status("Intentando iniciar PostgreSQL...")
            subprocess.run(['sudo', 'systemctl', 'start', 'postgresql'], check=True)
            time.sleep(2)
            return check_postgresql_service()
    except Exception as e:
        print_error(f"Error verificando PostgreSQL: {e}")
        return False

def create_database_and_user():
    """Crear base de datos y usuario si no existen"""
    print_header("CONFIGURANDO BASE DE DATOS Y USUARIO")
    
    try:
        # Conectar como usuario postgres
        conn = psycopg2.connect(
            host='localhost',
            database='postgres',
            user='postgres',
            port=5432
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Verificar si el usuario existe
        cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (DB_CONFIG['user'],))
        if not cursor.fetchone():
            print_status(f"Creando usuario: {DB_CONFIG['user']}")
            cursor.execute(sql.SQL("CREATE USER {} WITH PASSWORD %s").format(
                sql.Identifier(DB_CONFIG['user'])
            ), (DB_CONFIG['password'],))
            print_status("✅ Usuario creado")
        else:
            print_status("✅ Usuario ya existe")
        
        # Verificar si la base de datos existe
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_CONFIG['database'],))
        if not cursor.fetchone():
            print_status(f"Creando base de datos: {DB_CONFIG['database']}")
            cursor.execute(sql.SQL("CREATE DATABASE {} OWNER {}").format(
                sql.Identifier(DB_CONFIG['database']),
                sql.Identifier(DB_CONFIG['user'])
            ))
            print_status("✅ Base de datos creada")
        else:
            print_status("✅ Base de datos ya existe")
        
        # Otorgar permisos
        cursor.execute(sql.SQL("GRANT ALL PRIVILEGES ON DATABASE {} TO {}").format(
            sql.Identifier(DB_CONFIG['database']),
            sql.Identifier(DB_CONFIG['user'])
        ))
        print_status("✅ Permisos otorgados")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print_error(f"Error configurando base de datos: {e}")
        return False

def test_database_connection():
    """Probar conexión a la base de datos"""
    print_header("PROBANDO CONEXIÓN A LA BASE DE DATOS")
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Probar consulta simple
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print_status(f"✅ Conexión exitosa")
        print_status(f"Versión PostgreSQL: {version}")
        
        # Verificar permisos
        cursor.execute("SELECT current_database(), current_user;")
        db_info = cursor.fetchone()
        print_status(f"Base de datos actual: {db_info[0]}")
        print_status(f"Usuario actual: {db_info[1]}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print_error(f"Error conectando a la base de datos: {e}")
        return False

def setup_flask_environment():
    """Configurar variables de entorno para Flask"""
    print_header("CONFIGURANDO ENTORNO FLASK")
    
    # Variables de entorno necesarias
    env_vars = {
        'FLASK_APP': 'wsgi.py',
        'FLASK_ENV': 'production',
        'DATABASE_URL': f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value
        print_status(f"✅ {key} configurado")
    
    return True

def run_flask_migrations():
    """Ejecutar migraciones de Flask"""
    print_header("EJECUTANDO MIGRACIONES DE FLASK")
    
    try:
        # Cambiar al directorio del proyecto
        project_dir = '/opt/barber-brothers'
        if not os.path.exists(project_dir):
            project_dir = os.getcwd()
        
        os.chdir(project_dir)
        print_status(f"Directorio de trabajo: {os.getcwd()}")
        
        # Activar entorno virtual si existe
        venv_path = os.path.join(project_dir, 'venv', 'bin', 'activate')
        if os.path.exists(venv_path):
            print_status("Usando entorno virtual")
        
        # Inicializar migraciones si es necesario
        if not os.path.exists('migrations'):
            print_status("Inicializando migraciones...")
            result = subprocess.run(['flask', 'db', 'init'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                print_error(f"Error inicializando migraciones: {result.stderr}")
                return False
            print_status("✅ Migraciones inicializadas")
        
        # Ejecutar migraciones
        print_status("Ejecutando migraciones...")
        result = subprocess.run(['flask', 'db', 'upgrade'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print_status("✅ Migraciones ejecutadas exitosamente")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print_error(f"Error ejecutando migraciones: {result.stderr}")
            return False
            
    except Exception as e:
        print_error(f"Error en migraciones: {e}")
        return False

def verify_database_tables():
    """Verificar que las tablas se hayan creado correctamente"""
    print_header("VERIFICANDO TABLAS DE LA BASE DE DATOS")
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Obtener lista de tablas
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        
        if tables:
            print_status(f"✅ Se encontraron {len(tables)} tablas:")
            for table in tables:
                print_status(f"  - {table[0]}")
        else:
            print_warning("⚠️  No se encontraron tablas")
        
        # Verificar tablas específicas esperadas
        expected_tables = ['usuario', 'barbero', 'cliente', 'servicio', 'producto', 'categoria', 'cita']
        
        table_names = [table[0] for table in tables]
        missing_tables = [table for table in expected_tables if table not in table_names]
        
        if missing_tables:
            print_warning(f"⚠️  Tablas faltantes: {', '.join(missing_tables)}")
        else:
            print_status("✅ Todas las tablas principales están presentes")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print_error(f"Error verificando tablas: {e}")
        return False

def create_admin_user():
    """Crear usuario administrador si no existe"""
    print_header("CREANDO USUARIO ADMINISTRADOR")
    
    try:
        # Importar modelos de Flask
        sys.path.append('/opt/barber-brothers')
        from app import create_app
        from app.models.admin import Usuario
        from werkzeug.security import generate_password_hash
        
        app = create_app()
        
        with app.app_context():
            # Verificar si ya existe un admin
            admin = Usuario.query.filter_by(email='admin@barberbros.com').first()
            
            if not admin:
                print_status("Creando usuario administrador...")
                admin = Usuario(
                    nombre='Administrador',
                    email='admin@barberbros.com',
                    password_hash=generate_password_hash('admin123'),
                    es_admin=True,
                    activo=True
                )
                
                from app import db
                db.session.add(admin)
                db.session.commit()
                
                print_status("✅ Usuario administrador creado")
                print_status("Email: admin@barberbros.com")
                print_status("Password: admin123")
                print_warning("⚠️  Cambia la contraseña después del primer login")
            else:
                print_status("✅ Usuario administrador ya existe")
        
        return True
        
    except Exception as e:
        print_error(f"Error creando usuario admin: {e}")
        return False

def run_database_tests():
    """Ejecutar pruebas básicas de la base de datos"""
    print_header("EJECUTANDO PRUEBAS DE LA BASE DE DATOS")
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Test 1: Insertar y leer datos de prueba
        print_status("Test 1: Operaciones básicas...")
        
        # Verificar si existe la tabla de categorías
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'categoria'
            );
        """)
        
        if cursor.fetchone()[0]:
            # Insertar categoría de prueba
            cursor.execute("""
                INSERT INTO categoria (nombre, descripcion) 
                VALUES (%s, %s) 
                ON CONFLICT (nombre) DO NOTHING
                RETURNING id;
            """, ('Test Category', 'Categoría de prueba'))
            
            conn.commit()
            print_status("✅ Test de inserción exitoso")
            
            # Leer datos
            cursor.execute("SELECT COUNT(*) FROM categoria;")
            count = cursor.fetchone()[0]
            print_status(f"✅ Test de lectura exitoso - {count} categorías encontradas")
        
        # Test 2: Verificar índices
        print_status("Test 2: Verificando índices...")
        cursor.execute("""
            SELECT indexname, tablename 
            FROM pg_indexes 
            WHERE schemaname = 'public'
            ORDER BY tablename, indexname;
        """)
        
        indexes = cursor.fetchall()
        print_status(f"✅ {len(indexes)} índices encontrados")
        
        cursor.close()
        conn.close()
        
        print_status("✅ Todas las pruebas pasaron exitosamente")
        return True
        
    except Exception as e:
        print_error(f"Error en pruebas: {e}")
        return False

def main():
    """Función principal"""
    print_header("CONFIGURACIÓN DE BASE DE DATOS BARBER BROTHERS")
    print_status(f"Iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    steps = [
        ("Verificar servicio PostgreSQL", check_postgresql_service),
        ("Crear base de datos y usuario", create_database_and_user),
        ("Probar conexión", test_database_connection),
        ("Configurar entorno Flask", setup_flask_environment),
        ("Ejecutar migraciones", run_flask_migrations),
        ("Verificar tablas", verify_database_tables),
        ("Crear usuario admin", create_admin_user),
        ("Ejecutar pruebas", run_database_tests)
    ]
    
    results = []
    
    for step_name, step_function in steps:
        print_status(f"\n🔄 Ejecutando: {step_name}")
        try:
            success = step_function()
            results.append((step_name, success))
            if success:
                print_status(f"✅ {step_name} completado")
            else:
                print_error(f"❌ {step_name} falló")
                break
        except Exception as e:
            print_error(f"❌ Error en {step_name}: {e}")
            results.append((step_name, False))
            break
    
    # Resumen final
    print_header("RESUMEN DE CONFIGURACIÓN")
    
    success_count = sum(1 for _, success in results if success)
    total_count = len(results)
    
    for step_name, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {step_name}")
    
    print(f"\nResultado: {success_count}/{total_count} pasos completados")
    
    if success_count == total_count:
        print_status("\n🎉 ¡Base de datos configurada exitosamente!")
        print_status("La aplicación está lista para usar")
        print_status("Accede con: admin@barberbros.com / admin123")
    else:
        print_error("\n❌ Configuración incompleta")
        print_error("Revisa los errores anteriores")
    
    return success_count == total_count

if __name__ == "__main__":
    main()
