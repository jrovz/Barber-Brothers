from app import create_app, db
from app.models.barbero import Barbero, DisponibilidadBarbero, crear_disponibilidad_predeterminada

# Crear una aplicación con contexto
app = create_app()

def verificar_disponibilidad_barberos():
    """Verifica que todos los barberos activos tengan disponibilidad configurada"""
    with app.app_context():
        print("=== Verificando disponibilidad de barberos ===")
        barberos_activos = Barbero.query.filter_by(activo=True).all()
        print(f"Encontrados {len(barberos_activos)} barberos activos")
        
        for barbero in barberos_activos:
            # Contar disponibilidades
            total_disp = DisponibilidadBarbero.query.filter_by(barbero_id=barbero.id, activo=True).count()
            
            print(f"Barbero ID {barbero.id}: {barbero.nombre} - {total_disp} bloques de disponibilidad")
            
            if total_disp == 0:
                print(f"⚠️ El barbero {barbero.nombre} (ID: {barbero.id}) no tiene disponibilidad configurada.")
                print("   Creando disponibilidad predeterminada...")
                
                resultado = crear_disponibilidad_predeterminada(barbero.id)
                
                if resultado:
                    print(f"✅ Se creó disponibilidad predeterminada para {barbero.nombre}")
                else:
                    print(f"❌ No se pudo crear disponibilidad predeterminada para {barbero.nombre}")
                    
            # Verificar disponibilidad por día de semana
            dias_con_disponibilidad = db.session.query(DisponibilidadBarbero.dia_semana)\
                                    .filter_by(barbero_id=barbero.id, activo=True)\
                                    .distinct().all()
            
            dias = [d[0] for d in dias_con_disponibilidad]
            dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
            
            print(f"   Días con disponibilidad: {', '.join(dias_semana[d] for d in dias)}")
            
            # Verificar días faltantes
            dias_faltantes = [d for d in range(6) if d not in dias]  # 0-5 (lun-sáb)
            
            if dias_faltantes:
                print(f"⚠️ No hay disponibilidad para: {', '.join(dias_semana[d] for d in dias_faltantes)}")
        
        print("=== Verificación completada ===")

if __name__ == "__main__":
    verificar_disponibilidad_barberos()
