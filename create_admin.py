"""
Script para crear un usuario administrador en la base de datos

Este script crea un usuario con rol de administrador si no existe.
Se puede ejecutar para asegurar que siempre haya un usuario admin disponible.
"""
import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
from datetime import datetime

def create_admin_user(username="admin", email="admin@barberbrothers.com", password="adminBB2025", overwrite=False):
    """
    Crear un usuario administrador en la base de datos
    
    Args:
        username: Nombre de usuario (default: admin)
        email: Correo electrónico (default: admin@barberbrothers.com)
        password: Contraseña (default: adminBB2025)
        overwrite: Si es True, actualizará el usuario si existe, de lo contrario solo creará uno si no existe
    
    Returns:
        bool: True si fue exitoso, False en caso contrario
    """
    try:
        print(f"Iniciando creación de usuario administrador: {username}")
        
        # Verificamos primero que la base de datos SQLite exista
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'app.db')
        if not os.path.exists(db_path):
            print(f"ERROR: No se encontró la base de datos en {db_path}")
            print("Ejecuta primero 'python setup_local_db.py' para configurar la base de datos")
            return False
            
        print(f"Base de datos encontrada: {db_path} ({os.path.getsize(db_path)} bytes)")
        
        # Configurar explícitamente DATABASE_URL para SQLite
        os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'
        
        # Usar la app existente con todos los modelos
        from app import create_app, db
        from app.models.admin import User
        
        app = create_app('development')
        
        with app.app_context():
            # Verificar si el usuario ya existe
            existing_user = User.query.filter_by(username=username).first()
            
            if existing_user:
                if not overwrite:
                    print(f"El usuario '{username}' ya existe con rol: {existing_user.role}")
                    if existing_user.role == 'admin':
                        print("Ya es administrador. No se realizaron cambios.")
                        return True
                    else:
                        print(f"Actualizando rol de usuario de '{existing_user.role}' a 'admin'")
                        existing_user.role = 'admin'
                        db.session.commit()
                        print(f"Usuario {username} actualizado con rol de administrador")
                        return True
                else:
                    print(f"Actualizando usuario existente: {username}")
                    existing_user.email = email
                    existing_user.set_password(password)
                    existing_user.role = 'admin'
                    db.session.commit()
                    print(f"Usuario administrador '{username}' actualizado correctamente")
                    return True
            else:
                # Crear nuevo usuario admin
                new_admin = User(
                    username=username,
                    email=email,
                    role='admin',
                    creado=datetime.utcnow()
                )
                new_admin.set_password(password)
                
                db.session.add(new_admin)
                db.session.commit()
                
                print(f"Usuario administrador '{username}' creado exitosamente")
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
                password=sys.argv[3],
                overwrite=True if len(sys.argv) > 4 and sys.argv[4].lower() == 'true' else False
            )
        else:
            print("Uso: python create_admin.py <username> <email> <password> [overwrite]")
            sys.exit(1)
    else:
        # Usar valores predeterminados
        success = create_admin_user()
    
    sys.exit(0 if success else 1)
