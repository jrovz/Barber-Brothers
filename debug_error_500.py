#!/usr/bin/env python3
"""
Script de depuración para identificar problemas en el VPS con el sistema de galería de servicios
"""

import sys
import os
import traceback

# Añadir el directorio base al path
sys.path.insert(0, os.path.abspath('.'))

def test_imports():
    """Prueba todas las importaciones críticas"""
    print("=== PRUEBA DE IMPORTACIONES ===")
    
    try:
        from app import create_app
        print("✅ create_app importado correctamente")
    except Exception as e:
        print(f"❌ Error importando create_app: {e}")
        traceback.print_exc()
        return False
    
    try:
        from app.models.servicio import Servicio
        print("✅ Modelo Servicio importado correctamente")
    except Exception as e:
        print(f"❌ Error importando Servicio: {e}")
        traceback.print_exc()
        return False
    
    try:
        from app.models.servicio_imagen import ServicioImagen
        print("✅ Modelo ServicioImagen importado correctamente")
    except Exception as e:
        print(f"❌ Error importando ServicioImagen: {e}")
        traceback.print_exc()
        return False
    
    try:
        from app.admin.forms import ServicioForm
        print("✅ FormularioServicio importado correctamente")
    except Exception as e:
        print(f"❌ Error importando ServicioForm: {e}")
        traceback.print_exc()
        return False
    
    return True

def test_database_connection():
    """Prueba la conexión a la base de datos"""
    print("\n=== PRUEBA DE CONEXIÓN A BASE DE DATOS ===")
    
    try:
        app = create_app()
        with app.app_context():
            from app import db
            from sqlalchemy.sql import text
            
            # Probar conexión básica
            result = db.session.execute(text("SELECT 1"))
            print("✅ Conexión a base de datos exitosa")
            
            # Verificar tabla servicio_imagenes
            result = db.session.execute(text("SELECT COUNT(*) FROM servicio_imagenes"))
            count = result.scalar()
            print(f"✅ Tabla servicio_imagenes existe con {count} registros")
            
            # Verificar servicios
            result = db.session.execute(text("SELECT COUNT(*) FROM servicio"))
            count = result.scalar()
            print(f"✅ Tabla servicio existe con {count} registros")
            
            return True
            
    except Exception as e:
        print(f"❌ Error de conexión a base de datos: {e}")
        traceback.print_exc()
        return False

def test_servicio_relations():
    """Prueba las relaciones del modelo Servicio"""
    print("\n=== PRUEBA DE RELACIONES DE MODELO ===")
    
    try:
        app = create_app()
        with app.app_context():
            from app.models.servicio import Servicio
            from app.models.servicio_imagen import ServicioImagen
            
            # Obtener un servicio
            servicio = Servicio.query.first()
            if not servicio:
                print("❌ No hay servicios en la base de datos")
                return False
            
            print(f"✅ Servicio encontrado: {servicio.nombre} (ID: {servicio.id})")
            
            # Probar método get_imagenes_activas
            try:
                imagenes = servicio.get_imagenes_activas()
                print(f"✅ get_imagenes_activas() funciona - {len(imagenes)} imágenes encontradas")
            except Exception as e:
                print(f"❌ Error en get_imagenes_activas(): {e}")
                traceback.print_exc()
                return False
            
            # Probar método get_imagen_principal
            try:
                imagen_principal = servicio.get_imagen_principal()
                print(f"✅ get_imagen_principal() funciona - Imagen: {imagen_principal}")
            except Exception as e:
                print(f"❌ Error en get_imagen_principal(): {e}")
                traceback.print_exc()
                return False
            
            return True
            
    except Exception as e:
        print(f"❌ Error probando relaciones: {e}")
        traceback.print_exc()
        return False

def test_admin_routes():
    """Prueba las rutas de administración"""
    print("\n=== PRUEBA DE RUTAS DE ADMINISTRACIÓN ===")
    
    try:
        app = create_app()
        with app.app_context():
            # Simular una solicitud a la ruta de editar servicio
            from app.admin.forms import ServicioForm
            from app.models.servicio import Servicio
            
            servicio = Servicio.query.first()
            if not servicio:
                print("❌ No hay servicios para probar")
                return False
            
            # Crear formulario como si fuera GET
            try:
                form = ServicioForm(obj=servicio)
                print("✅ Formulario ServicioForm creado correctamente")
            except Exception as e:
                print(f"❌ Error creando formulario: {e}")
                traceback.print_exc()
                return False
            
            # Probar pre-llenado de campos
            try:
                if hasattr(form, 'nombre'):
                    form.nombre.data = servicio.nombre
                    print(f"✅ Campo nombre pre-llenado: {form.nombre.data}")
                else:
                    print("❌ Formulario no tiene campo 'nombre'")
                    return False
            except Exception as e:
                print(f"❌ Error pre-llenando campos: {e}")
                traceback.print_exc()
                return False
            
            return True
            
    except Exception as e:
        print(f"❌ Error probando rutas admin: {e}")
        traceback.print_exc()
        return False

def main():
    """Función principal de depuración"""
    print("INICIANDO DEPURACIÓN DEL SISTEMA DE GALERÍA DE SERVICIOS")
    print("=" * 60)
    
    # Pruebas secuenciales
    tests = [
        test_imports,
        test_database_connection,
        test_servicio_relations,
        test_admin_routes
    ]
    
    all_passed = True
    for i, test in enumerate(tests, 1):
        print(f"\n[{i}/{len(tests)}] Ejecutando {test.__name__}...")
        try:
            if not test():
                all_passed = False
                print(f"❌ {test.__name__} FALLÓ")
            else:
                print(f"✅ {test.__name__} PASÓ")
        except Exception as e:
            print(f"❌ {test.__name__} EXCEPCIÓN: {e}")
            traceback.print_exc()
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ TODAS LAS PRUEBAS PASARON - El sistema debería estar funcionando")
    else:
        print("❌ ALGUNAS PRUEBAS FALLARON - Revisar errores arriba")
    
    return all_passed

if __name__ == "__main__":
    main() 