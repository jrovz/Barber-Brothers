# filepath: app/admin/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, FloatField, TextAreaField, URLField, SelectField, DecimalField
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional, URL

class LoginForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired(), Length(min=4, max=64)])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    remember_me = BooleanField('Recuérdame')
    submit = SubmitField('Iniciar Sesión')

class ProductoForm(FlaskForm):
    nombre = StringField('Nombre del Producto', validators=[DataRequired(), Length(max=100)])
    descripcion = TextAreaField('Descripción', validators=[Optional()])
    precio = FloatField('Precio (€)', validators=[DataRequired(), NumberRange(min=0)])
    imagen_url = URLField('URL de la Imagen', validators=[DataRequired(), URL()])
    categoria = SelectField('Categoría', choices=[
        ('peinar', 'Productos para Peinar'),
        ('barba', 'Productos para Barba'),
        ('accesorios', 'Accesorios')
    ], validators=[DataRequired()])
    submit = SubmitField('Guardar Producto')

class BarberoForm(FlaskForm):
    nombre = StringField('Nombre del Barbero', validators=[DataRequired(), Length(max=100)])
    especialidad = StringField('Especialidad', validators=[Optional(), Length(max=100)])
    imagen_url = URLField('URL de la Imagen', validators=[Optional(), URL()])
    activo = BooleanField('Activo', default=True)
    submit = SubmitField('Guardar Barbero')

class ServicioForm(FlaskForm):
    nombre = StringField('Nombre del Servicio', validators=[DataRequired(), Length(min=3, max=100)])
    descripcion = TextAreaField('Descripción (Opcional)')
    precio = DecimalField('Precio (€)', validators=[DataRequired(), NumberRange(min=0)], places=2)
    duracion_estimada = StringField('Duración Estimada (Ej: 45 min)', validators=[Length(max=50)])
    activo = BooleanField('Mostrar en el sitio público', default=True)
    submit = SubmitField('Guardar Servicio')