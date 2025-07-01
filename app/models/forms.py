from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateTimeField, IntegerField, BooleanField
from wtforms.validators import DataRequired, Length, ValidationError

# Validador personalizado para campos que pueden tener valor 0
class DataRequiredAllowZero(DataRequired):
    """
    Validador personalizado que permite el valor 0, a diferencia de DataRequired
    que considera 0 como falsy y lo rechaza.
    """
    def __call__(self, form, field):
        if field.data is None or (isinstance(field.data, str) and field.data.strip() == '') or field.data == -1:
            raise ValidationError(self.message or 'Este campo es obligatorio.')
        return True

class DisponibilidadForm(FlaskForm):
    dia_semana = SelectField('Día de la Semana', choices=[
        (-1, 'Selecciona un día'),
        (0, 'Lunes'), (1, 'Martes'), (2, 'Miércoles'), 
        (3, 'Jueves'), (4, 'Viernes'), (5, 'Sábado')
    ], coerce=int, validators=[DataRequiredAllowZero(message="Debe seleccionar un día de la semana")])
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