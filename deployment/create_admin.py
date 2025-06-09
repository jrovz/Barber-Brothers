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
    from app.models.admin import User
    from werkzeug.security import generate_password_hash
    
    print("🔄 Creando usuario administrador...")
    
    app = create_app()
    
    with app.app_context():
        # Verificar si ya existe un admin
        existing_admin = User.query.filter_by(email='thebarberbrothers1@gmail.com').first()
        
        if existing_admin:
            print("✅ Usuario administrador ya existe")
            print(f"Email: {existing_admin.email}")
            print(f"Username: {existing_admin.username}")
            print(f"Role: {existing_admin.role}")
        else:
            # Crear nuevo usuario admin
            admin_user = User(
                username='barber.brothers3',
                email='thebarberbrothers1@gmail.com',
                role='admin'
            )
            admin_user.set_password('barberbrothers1*')
            
            db.session.add(admin_user)
            db.session.commit()
            
            print("✅ Usuario administrador creado exitosamente")
            print("📧 Email: thebarberbrothers1@gmail.com")
            print("👤 Username: barber.brothers3")
            print("🔐 Password: barberbrothers1*")
            print("⚠️  IMPORTANTE: Cambia la contraseña después del primer login")
        
        # Mostrar estadísticas de usuarios
        total_users = User.query.count()
        admin_users = User.query.filter_by(role='admin').count()
        barbero_users = User.query.filter_by(role='barbero').count()
        cliente_users = User.query.filter_by(role='cliente').count()
        
        print(f"\n📊 Estadísticas de usuarios:")
        print(f"   Total de usuarios: {total_users}")
        print(f"   Administradores: {admin_users}")
        print(f"   Barberos: {barbero_users}")
        print(f"   Clientes: {cliente_users}")

except ImportError as e:
    print(f"❌ Error importando módulos: {e}")
    print("Verifica que el entorno virtual esté activado y las dependencias instaladas")
except Exception as e:
    print(f"❌ Error creando usuario administrador: {e}")
    sys.exit(1)
