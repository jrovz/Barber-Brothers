#!/usr/bin/env python3
"""
Script para crear usuario administrador en Barber Brothers
Ejecutar después de las migraciones
"""

import os
import sys
from datetime import datetime

# Configurar el entorno
os.environ['FLASK_APP'] = 'wsgi.py'
os.environ['FLASK_ENV'] = 'production'

# Agregar el directorio del proyecto al path
project_dir = '/opt/barber-brothers'
if os.path.exists(project_dir):
    sys.path.insert(0, project_dir)
    os.chdir(project_dir)

try:
    from app import create_app, db
    from app.models.admin import Usuario
    from werkzeug.security import generate_password_hash
    
    print("🔄 Creando usuario administrador...")
    
    app = create_app()
    
    with app.app_context():
        # Verificar si ya existe un admin
        existing_admin = Usuario.query.filter_by(email='admin@barberbros.com').first()
        
        if existing_admin:
            print("✅ Usuario administrador ya existe")
            print(f"Email: {existing_admin.email}")
            print(f"Nombre: {existing_admin.nombre}")
            print(f"Estado: {'Activo' if existing_admin.activo else 'Inactivo'}")
        else:
            # Crear nuevo usuario admin
            admin_user = Usuario(
                nombre='Administrador Principal',
                email='admin@barberbros.com',
                password_hash=generate_password_hash('admin123'),
                es_admin=True,
                activo=True,
                fecha_creacion=datetime.utcnow()
            )
            
            db.session.add(admin_user)
            db.session.commit()
            
            print("✅ Usuario administrador creado exitosamente")
            print("📧 Email: admin@barberbros.com")
            print("🔐 Password: admin123")
            print("⚠️  IMPORTANTE: Cambia la contraseña después del primer login")
        
        # Mostrar estadísticas de usuarios
        total_users = Usuario.query.count()
        admin_users = Usuario.query.filter_by(es_admin=True).count()
        active_users = Usuario.query.filter_by(activo=True).count()
        
        print(f"\n📊 Estadísticas de usuarios:")
        print(f"   Total de usuarios: {total_users}")
        print(f"   Administradores: {admin_users}")
        print(f"   Usuarios activos: {active_users}")

except ImportError as e:
    print(f"❌ Error importando módulos: {e}")
    print("Verifica que el entorno virtual esté activado y las dependencias instaladas")
except Exception as e:
    print(f"❌ Error creando usuario administrador: {e}")
    sys.exit(1)
