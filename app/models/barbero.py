# filepath: app/models/barbero.py
from app import db
from datetime import datetime, timedelta
from sqlalchemy.orm import validates

class Barbero(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    especialidad = db.Column(db.String(100))
    descripcion = db.Column(db.Text)
    imagen_url = db.Column(db.String(255))
    activo = db.Column(db.Boolean, default=True)
    creado = db.Column(db.DateTime, default=datetime.utcnow)
    # Relación con Citas (un barbero puede tener muchas citas)
    citas = db.relationship('Cita', backref='barbero', lazy='dynamic')
    
    # Relación con disponibilidad
    disponibilidad = db.relationship('DisponibilidadBarbero', backref='barbero', lazy='dynamic',
                                    cascade='all, delete-orphan')
    
    def esta_disponible(self, fecha_propuesta):
        """
        Verifica si el barbero está disponible en una fecha específica
        
        Args:
            fecha_propuesta (datetime): Fecha y hora para verificar disponibilidad
            
        Returns:
            bool: True si está disponible, False en caso contrario
        """
        # Obtener solo la fecha (sin hora)
        solo_fecha = fecha_propuesta.date()
        # Obtener solo la hora
        solo_hora = fecha_propuesta.time()
        
        # Obtener disponibilidades para ese día
        dia_semana = solo_fecha.weekday()
        
        # Verificar si es un día laborable (lunes a sábado)
        if dia_semana > 5:  # domingo
            return False
            
        # Comprobar en cada bloque de disponibilidad
        for disp in self.disponibilidad.filter_by(dia_semana=dia_semana, activo=True).all():
            if disp.hora_inicio <= solo_hora < disp.hora_fin:
                # Verificar si ya tiene una cita en ese horario
                from app.models.cliente import Cita
                cita_existente = Cita.query.filter_by(
                    barbero_id=self.id,
                    fecha=fecha_propuesta,
                    estado='confirmada'
                ).first()
                return cita_existente is None
                
        return False

    def get_disponibilidad_por_dia(self, dia_semana):
        """Obtener todos los bloques de disponibilidad para un día específico"""
        return self.disponibilidad.filter_by(dia_semana=dia_semana, activo=True).all()
    
    def obtener_horarios_disponibles(self, fecha, duracion=30):
        """
        Obtiene todos los horarios disponibles para una fecha específica
        
        Args:
            fecha (date): Fecha para la que se quieren obtener los horarios
            duracion (int): Duración de cada slot en minutos
            
        Returns:
            list: Lista de diccionarios con la información de cada slot de tiempo disponible
        """
        # Obtener el día de la semana (0-6)
        dia_semana = fecha.weekday()
        
        # No hay atención los domingos
        if dia_semana > 5:  # Domingo
            return []
            
        # Obtener todos los bloques de disponibilidad para este día
        disponibilidades = self.get_disponibilidad_por_dia(dia_semana)
        
        if not disponibilidades:
            return []
            
        # Generar todos los slots de tiempo para esas disponibilidades
        todos_los_slots = []
        for disp in disponibilidades:
            slots = disp.generar_slots_disponibles(fecha, duracion)
            todos_los_slots.extend(slots)
            
        # Ordenar los slots por hora
        todos_los_slots.sort(key=lambda x: x['hora'])
        
        return todos_los_slots

    def __repr__(self):
        return f'<Barbero {self.nombre}>'
    

class DisponibilidadBarbero(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    barbero_id = db.Column(db.Integer, db.ForeignKey('barbero.id'), nullable=False)
    dia_semana = db.Column(db.Integer, nullable=False)  # 0: Lunes, 1: Martes, ..., 5: Sábado
    hora_inicio = db.Column(db.Time, nullable=False)
    hora_fin = db.Column(db.Time, nullable=False)
    activo = db.Column(db.Boolean, default=True)
    
    @validates('dia_semana')
    def validate_dia_semana(self, key, dia):
        if dia < 0 or dia > 6:
            raise ValueError(f"Día de semana debe estar entre 0 (Lunes) y 6 (Domingo). Valor recibido: {dia}")
        return dia
    
    @validates('hora_fin')
    def validate_hora_fin(self, key, hora_fin):
        if hasattr(self, 'hora_inicio') and self.hora_inicio and hora_fin <= self.hora_inicio:
            raise ValueError("La hora de fin debe ser posterior a la hora de inicio")
        return hora_fin
    
    def generar_slots_disponibles(self, fecha, duracion=30):
        """
        Genera slots de tiempo disponibles para una fecha específica
        
        Args:
            fecha (date): Fecha para la que se quieren generar los slots
            duracion (int): Duración de cada slot en minutos
            
        Returns:
            list: Lista de diccionarios con la información de cada slot
        """
        # Verificar que sea el día de la semana correcto
        if fecha.weekday() != self.dia_semana:
            return []
            
        from app.models.cliente import Cita
        
        slots = []
        # Convertir la hora de inicio y fin a datetime para poder hacer operaciones
        current_time = datetime.combine(fecha, self.hora_inicio)
        end_time = datetime.combine(fecha, self.hora_fin)
        
        # Generar slots hasta la hora de fin
        while current_time + timedelta(minutes=duracion) <= end_time:
            # Verificar si ya existe una cita para este horario
            hora_slot = current_time.time()
            fecha_hora = datetime.combine(fecha, hora_slot)
            
            # Buscar citas que se solapen con este horario
            cita_existente = Cita.query.filter_by(
                barbero_id=self.barbero_id,
                fecha=fecha_hora,
                estado='confirmada'
            ).first()
            
            slots.append({
                'hora': hora_slot.strftime('%H:%M'),
                'disponible': cita_existente is None
            })
            
            # Avanzar a la siguiente hora
            current_time += timedelta(minutes=duracion)
            
        return slots
    
    def __repr__(self):
        dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        return f'<Disponibilidad: {dias[self.dia_semana]} {self.hora_inicio}-{self.hora_fin}>'

def crear_disponibilidad_predeterminada(barbero_id):
    """
    Crea una disponibilidad predeterminada para un barbero
    - Lunes a viernes: 9:00-13:00 y 15:00-20:00
    - Sábados: 9:00-14:00
    
    Args:
        barbero_id (int): ID del barbero
        
    Returns:
        bool: True si se creó correctamente, False en caso contrario
    """
    from datetime import time
    
    try:
        # Verificar si ya tiene disponibilidad
        disp_existente = DisponibilidadBarbero.query.filter_by(barbero_id=barbero_id).first()
        if disp_existente:
            print(f"El barbero {barbero_id} ya tiene disponibilidad configurada")
            return False
        
        # Horario para días de semana (L-V)
        for dia in range(0, 5):  # 0=Lunes, 4=Viernes
            disp_manana = DisponibilidadBarbero(
                barbero_id=barbero_id,
                dia_semana=dia,
                hora_inicio=time(9, 0),  # 9:00 AM
                hora_fin=time(13, 0),    # 1:00 PM
                activo=True
            )
            disp_tarde = DisponibilidadBarbero(
                barbero_id=barbero_id,
                dia_semana=dia,
                hora_inicio=time(15, 0),  # 3:00 PM
                hora_fin=time(20, 0),     # 8:00 PM
                activo=True
            )
            db.session.add(disp_manana)
            db.session.add(disp_tarde)
        
        # Horario para sábado (medio día)
        disp_sabado = DisponibilidadBarbero(
            barbero_id=barbero_id,
            dia_semana=5,  # 5=Sábado
            hora_inicio=time(9, 0),  # 9:00 AM
            hora_fin=time(14, 0),    # 2:00 PM
            activo=True
        )
        db.session.add(disp_sabado)
        
        db.session.commit()
        return True
        
    except Exception as e:
        db.session.rollback()
        print(f"Error al crear disponibilidad: {e}")
        return False