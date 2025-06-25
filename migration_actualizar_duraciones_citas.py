#!/usr/bin/env python3
"""
Script de migración para actualizar las duraciones de las citas existentes
basándose en la duración del servicio asociado.

Ejecutar desde el directorio raíz del proyecto:
python migration_actualizar_duraciones_citas.py
"""

import os
import sys

# Añadir el directorio actual al path para importar los módulos de la app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.cliente import Cita
from app.models.servicio import Servicio

def actualizar_duraciones_citas():
    """
    Actualiza las duraciones de todas las citas existentes basándose
    en la duración estimada del servicio asociado.
    """
    app = create_app()
    
    with app.app_context():
        print("Iniciando actualización de duraciones de citas...")
        
        # Obtener todas las citas que no tienen duración definida o tienen duración por defecto
        citas_sin_duracion = Cita.query.filter(
            (Cita.duracion == None) | (Cita.duracion == 30)
        ).all()
        
        total_citas = len(citas_sin_duracion)
        print(f"Se encontraron {total_citas} citas para actualizar.")
        
        actualizadas = 0
        errores = 0
        
        for i, cita in enumerate(citas_sin_duracion, 1):
            try:
                if cita.servicio_rel:
                    nueva_duracion = cita.servicio_rel.get_duracion_minutos()
                    cita.duracion = nueva_duracion
                    
                    print(f"[{i}/{total_citas}] Cita ID {cita.id}: {nueva_duracion} min (Servicio: {cita.servicio_rel.nombre})")
                else:
                    print(f"[{i}/{total_citas}] Cita ID {cita.id}: SIN SERVICIO ASOCIADO - manteniendo 30 min")
                    cita.duracion = 30
                
                actualizadas += 1
                    
            except Exception as e:
                print(f"[{i}/{total_citas}] ERROR en Cita ID {cita.id}: {str(e)}")
                errores += 1
        
        try:
            db.session.commit()
            print(f"\n✅ Migración completada:")
            print(f"   - Citas actualizadas: {actualizadas}")
            print(f"   - Errores: {errores}")
            print(f"   - Total procesadas: {total_citas}")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error al guardar cambios: {str(e)}")
            return False
            
        return True

def mostrar_resumen_duraciones():
    """
    Muestra un resumen de las duraciones de servicios y citas
    """
    app = create_app()
    
    with app.app_context():
        print("\n=== RESUMEN DE DURACIONES ===")
        
        # Servicios y sus duraciones
        servicios = Servicio.query.filter_by(activo=True).all()
        print(f"\nServicios activos ({len(servicios)}):")
        for servicio in servicios:
            duracion = servicio.get_duracion_minutos()
            print(f"  - {servicio.nombre}: {duracion} min ({servicio.duracion_estimada})")
        
        # Distribución de duraciones en citas
        from sqlalchemy import func
        distribucion_citas = db.session.query(
            Cita.duracion, 
            func.count(Cita.id).label('cantidad')
        ).group_by(Cita.duracion).order_by(Cita.duracion).all()
        
        print(f"\nDistribución de duraciones en citas:")
        for duracion, cantidad in distribucion_citas:
            print(f"  - {duracion} min: {cantidad} citas")

if __name__ == "__main__":
    print("MIGRACIÓN DE DURACIONES DE CITAS")
    print("=" * 40)
    
    # Mostrar resumen antes de la migración
    print("ANTES DE LA MIGRACIÓN:")
    mostrar_resumen_duraciones()
    
    # Confirmar ejecución
    respuesta = input("\n¿Continuar con la migración? (s/N): ").lower().strip()
    
    if respuesta in ['s', 'si', 'sí', 'y', 'yes']:
        exito = actualizar_duraciones_citas()
        
        if exito:
            print("\nDESPUÉS DE LA MIGRACIÓN:")
            mostrar_resumen_duraciones()
        else:
            print("\n❌ La migración falló. Revisar los errores anteriores.")
    else:
        print("Migración cancelada.") 