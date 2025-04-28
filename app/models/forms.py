from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateTimeField, IntegerField, BooleanField
from wtforms.validators import DataRequired, Length

class DisponibilidadForm(FlaskForm):
    dia_semana = SelectField('Día de la Semana', choices=[
        (0, 'Lunes'), (1, 'Martes'), (2, 'Miércoles'), 
        (3, 'Jueves'), (4, 'Viernes'), (5, 'Sábado')
    ], coerce=int, validators=[DataRequired()])
    hora_inicio = StringField('Hora de Inicio (HH:MM)', validators=[DataRequired()])
    hora_fin = StringField('Hora de Fin (HH:MM)', validators=[DataRequired()])
    activo = BooleanField('Activo', default=True)
    
class CitaForm(FlaskForm):
    cliente_id = SelectField('Cliente', coerce=int, validators=[DataRequired()])
    barbero_id = SelectField('Barbero', coerce=int, validators=[DataRequired()])
    fecha = DateTimeField('Fecha y Hora', format='%Y-%m-%d %H:%M', validators=[DataRequired()])
    servicio = SelectField('Servicio', validators=[DataRequired()])
    estado = SelectField('Estado', choices=[
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada'),
        ('completada', 'Completada')
    ])