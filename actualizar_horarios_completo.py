#!/usr/bin/env python3
"""
Script para establecer los horarios estándar de la barbería:
8:00-12:00 y 14:00-20:00 para todos los barberos
"""

import os
import sys
from datetime import time

# Añadir el directorio del proyecto al path de Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.barbero import DisponibilidadBarbero, Barbero

def actualizar_a_horarios_estandar():
    """Actualiza todos los horarios a los estándares de la barbería"""
    try:
        # Obtener todos los barberos activos
        barberos = Barbero.query.filter_by(activo=True).all()
        
        print(f"Actualizando horarios para {len(barberos)} barberos activos")
        
        for barbero in barberos:
            print(f"\n--- Actualizando barbero: {barbero.nombre} (ID: {barbero.id}) ---")
            
            # Eliminar todas las disponibilidades existentes
            DisponibilidadBarbero.query.filter_by(barbero_id=barbero.id).delete()
            
            # Crear nuevos horarios estándar (L-S)
            for dia in range(0, 6):  # 0=Lunes a 5=Sábado
                # Turno mañana: 8:00-12:00
                disp_manana = DisponibilidadBarbero(
                    barbero_id=barbero.id,
                    dia_semana=dia,
                    hora_inicio=time(8, 0),   # 8:00 AM
                    hora_fin=time(12, 0),     # 12:00 PM
                    activo=True
                )
                
                # Turno tarde: 14:00-20:00 
                disp_tarde = DisponibilidadBarbero(
                    barbero_id=barbero.id,
                    dia_semana=dia,
                    hora_inicio=time(14, 0),  # 2:00 PM
                    hora_fin=time(20, 0),     # 8:00 PM
                    activo=True
                )
                
                db.session.add(disp_manana)
                db.session.add(disp_tarde)
                
            print(f"✅ Configurados horarios estándar para {barbero.nombre}")
        
        # Guardar todos los cambios
        db.session.commit()
        print("\n🎉 ¡Todos los horarios actualizados exitosamente!")
        
        return True
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error al actualizar horarios: {e}")
        return False

def verificar_horarios():
    """Verifica los horarios actuales de todos los barberos"""
    print("\n=== HORARIOS ACTUALES ===")
    barberos = Barbero.query.filter_by(activo=True).all()
    
    for barbero in barberos:
        print(f"\n{barbero.nombre} (ID: {barbero.id}):")
        disponibilidades = DisponibilidadBarbero.query.filter_by(
            barbero_id=barbero.id
        ).order_by(DisponibilidadBarbero.dia_semana, DisponibilidadBarbero.hora_inicio).all()
        
        if not disponibilidades:
            print("  Sin horarios configurados")
            continue
            
        dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        for disp in disponibilidades:
            print(f"  {dias[disp.dia_semana]}: {disp.hora_inicio.strftime('%H:%M')}-{disp.hora_fin.strftime('%H:%M')}")

if __name__ == '__main__':
    app = create_app()
    
    with app.app_context():
        print("=== ACTUALIZACIÓN A HORARIOS ESTÁNDAR ===")
        print("Estableciendo horarios estándar para todos los barberos:")
        print("• Lunes a Sábado:")
        print("  - Mañana: 8:00 AM - 12:00 PM")
        print("  - Tarde: 2:00 PM - 8:00 PM")
        print("• Domingo: Cerrado")
        
        # Verificar horarios actuales
        verificar_horarios()
        
        # Preguntar confirmación
        respuesta = input("\n¿Proceder con la actualización? (s/n): ").lower()
        
        if respuesta in ['s', 'si', 'sí', 'y', 'yes']:
            # Ejecutar actualización
            exito = actualizar_a_horarios_estandar()
            
            # Verificar resultado
            print("\n=== DESPUÉS DE LA ACTUALIZACIÓN ===")
            verificar_horarios()
            
            if exito:
                print("\n🎉 ¡Actualización completada exitosamente!")
                print("\nTodos los barberos ahora tienen los horarios estándar:")
                print("📅 Lunes a Sábado:")
                print("  🌅 Mañana: 8:00 AM - 12:00 PM") 
                print("  🌇 Tarde: 2:00 PM - 8:00 PM")
                print("🚫 Domingo: Cerrado")
            else:
                print("\n❌ Hubo errores durante la actualización")
        else:
            print("❌ Actualización cancelada") 