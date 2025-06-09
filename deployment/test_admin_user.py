#!/usr/bin/env python3
"""
Script para verificar y probar el usuario administrador
"""

import os
import sys

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
    
    print("🔍 Verificando usuario administrador...")
    
    app = create_app()
    
    with app.app_context():
        # Buscar el usuario admin
        admin = User.query.filter_by(email='thebarberbrothers1@gmail.com').first()
        
        if admin:
            print("✅ Usuario encontrado:")
            print(f"   ID: {admin.id}")
            print(f"   Username: {admin.username}")
            print(f"   Email: {admin.email}")
            print(f"   Role: {admin.role}")
            print(f"   Fecha creación: {admin.creado}")
            
            # Verificar que el método is_admin() funciona
            print(f"\n🔍 Verificaciones:")
            print(f"   ¿Tiene método is_admin()?: {hasattr(admin, 'is_admin')}")
            if hasattr(admin, 'is_admin'):
                print(f"   ¿Es admin?: {admin.is_admin()}")
            
            # Probar autenticación
            print(f"\n🔐 Probando contraseña...")
            password_test = admin.check_password('barberbrothers1*')
            print(f"   ¿Contraseña correcta?: {password_test}")
            
            if not password_test:
                print("❌ La contraseña no coincide. ¿Quieres resetearla?")
                reset = input("Escribe 'si' para resetear la contraseña: ")
                if reset.lower() == 'si':
                    admin.set_password('barberbrothers1*')
                    db.session.commit()
                    print("✅ Contraseña reseteada")
                    
                    # Probar de nuevo
                    password_test = admin.check_password('barberbrothers1*')
                    print(f"   ¿Contraseña correcta ahora?: {password_test}")
            
        else:
            print("❌ Usuario administrador no encontrado")
            print("Ejecuta: python deployment/create_admin.py")
        
        # Mostrar todos los usuarios
        print(f"\n📊 Todos los usuarios en la base de datos:")
        all_users = User.query.all()
        for user in all_users:
            print(f"   - {user.username} ({user.email}) - Rol: {user.role}")

except ImportError as e:
    print(f"❌ Error importando módulos: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

print("\n🌐 Para probar el login:")
print("   URL: http://144.217.86.8/admin/login")
print("   Username: barber.brothers3")
print("   Password: barberbrothers1*")
