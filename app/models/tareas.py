# filepath: app/models/tareas.py
"""
Módulo para tareas programadas y mantenimiento del sistema.
"""
from app import db
from datetime import datetime, date, timedelta
from app.models.barbero import BloqueoHorario

def limpiar_bloqueos_pasados():
    """
    Elimina los bloqueos de horario que ya han pasado.
    Esta función debe ejecutarse periódicamente, idealmente una vez al día.
    
    Returns:
        int: Número de bloqueos eliminados
    """
    try:
        # Verificar si la tabla existe
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        if 'bloqueo_horario' not in inspector.get_table_names():
            print("La tabla bloqueo_horario no existe en la base de datos")
            return 0
            
        # Obtener la fecha de ayer
        fecha_limite = date.today() - timedelta(days=1)
        
        # Buscar bloqueos anteriores a la fecha límite
        bloqueos_pasados = BloqueoHorario.query.filter(
            BloqueoHorario.fecha <= fecha_limite
        ).all()
        
        # Eliminar los bloqueos
        count = 0
        for bloqueo in bloqueos_pasados:
            db.session.delete(bloqueo)
            count += 1
        
        db.session.commit()
        return count
    
    except Exception as e:
        db.session.rollback()
        print(f"Error al limpiar bloqueos pasados: {str(e)}")
        return 0
