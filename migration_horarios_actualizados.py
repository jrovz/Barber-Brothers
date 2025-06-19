#!/usr/bin/env python3
"""
Script de migración para actualizar horarios de barberos existentes
al nuevo horario estándar: Lunes a Sábado 8:00-12:00 y 13:00-20:00

Ejecutar con: python migration_horarios_actualizados.py
"""

import sys
import os

# Añadir el directorio raíz al path para importar la app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import time
from app import create_app, db
from app.models.barbero import Barbero, DisponibilidadBarbero

def migrar_horarios():
    """
    Migra los horarios existentes al nuevo estándar
    """
    app = create_app()
    
    with app.app_context():
        try:
            # Obtener todos los barberos
            barberos = Barbero.query.all()
            
            if not barberos:
                print("No hay barberos en la base de datos.")
                return
            
            print(f"Encontrados {len(barberos)} barberos para migrar horarios...")
            
            for barbero in barberos:
                print(f"\nMigrando horarios para: {barbero.nombre}")
                
                # Eliminar horarios antiguos
                horarios_antiguos = DisponibilidadBarbero.query.filter_by(barbero_id=barbero.id).all()
                
                if horarios_antiguos:
                    print(f"  - Eliminando {len(horarios_antiguos)} horarios antiguos")
                    for horario in horarios_antiguos:
                        db.session.delete(horario)
                    db.session.flush()
                
                # Crear nuevos horarios (Lunes a Sábado)
                print("  - Creando nuevos horarios:")
                dias_nombres = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado']
                
                for dia in range(0, 6):  # 0=Lunes, 5=Sábado
                    # Turno mañana
                    disp_manana = DisponibilidadBarbero(
                        barbero_id=barbero.id,
                        dia_semana=dia,
                        hora_inicio=time(8, 0),  # 8:00 AM
                        hora_fin=time(12, 0),    # 12:00 PM
                        activo=True
                    )
                    
                    # Turno tarde
                    disp_tarde = DisponibilidadBarbero(
                        barbero_id=barbero.id,
                        dia_semana=dia,
                        hora_inicio=time(13, 0),  # 1:00 PM
                        hora_fin=time(20, 0),     # 8:00 PM
                        activo=True
                    )
                    
                    db.session.add(disp_manana)
                    db.session.add(disp_tarde)
                    
                    print(f"    * {dias_nombres[dia]}: 08:00-12:00 y 13:00-20:00")
                
                # Confirmar cambios para este barbero
                db.session.commit()
                print(f"  ✅ Horarios actualizados exitosamente para {barbero.nombre}")
            
            print(f"\n🎉 Migración completada exitosamente para {len(barberos)} barberos!")
            print("Nuevo horario estándar aplicado: Lunes a Sábado 8:00-12:00 y 13:00-20:00")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error durante la migración: {str(e)}")
            raise

def confirmar_migracion():
    """
    Solicita confirmación antes de ejecutar la migración
    """
    print("🔄 MIGRACIÓN DE HORARIOS DE BARBEROS")
    print("=" * 50)
    print("Este script:")
    print("• Eliminará TODOS los horarios existentes de TODOS los barberos")
    print("• Aplicará el nuevo horario estándar: Lunes a Sábado 8:00-12:00 y 13:00-20:00")
    print("• Esta acción NO se puede deshacer")
    print()
    
    respuesta = input("¿Deseas continuar? (escriba 'SI' para confirmar): ").strip()
    
    if respuesta.upper() == 'SI':
        print("\n✅ Confirmado. Iniciando migración...")
        return True
    else:
        print("\n❌ Migración cancelada.")
        return False

if __name__ == "__main__":
    if confirmar_migracion():
        migrar_horarios()
    else:
        print("No se realizaron cambios.") 