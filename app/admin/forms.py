# filepath: app/admin/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, FloatField, TextAreaField, URLField, SelectField, DecimalField
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional, URL
from flask_wtf.file import FileField, FileAllowed

class LoginForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired(), Length(min=4, max=64)])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    remember_me = BooleanField('Recuérdame')
    submit = SubmitField('Iniciar Sesión')

class ProductoForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired(), Length(max=100)])
    descripcion = TextAreaField('Descripción', validators=[Optional(), Length(max=500)])
    precio = DecimalField('Precio (COP)', validators=[DataRequired(), NumberRange(min=0)])
    categoria = StringField('Categoría', validators=[Optional(), Length(max=50)])
    
    # Mantener campo URL para compatibilidad hacia atrás
    imagen_url = StringField('URL de Imagen (opcional)', validators=[Optional()])
    
    # Agregar campo para subir imagen
    imagen_file = FileField('Subir Imagen', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Solo archivos de imagen!')
    ])
    
    submit = SubmitField('Guardar Producto')

class BarberoForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired(), Length(max=100)])
    especialidad = StringField('Especialidad', validators=[Optional(), Length(max=100)])
    descripcion = TextAreaField('Descripción', validators=[Optional(), Length(max=500)])
    activo = BooleanField('Servicio Activo', default=True)
    # Mantener campo URL para compatibilidad hacia atrás
    imagen_url = StringField('URL de Imagen (opcional)', validators=[Optional()])
    
    # Agregar campo para subir imagen
    imagen_file = FileField('Subir Imagen', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Solo archivos de imagen!')
    ])
    
    submit = SubmitField('Guardar Barbero')

class ServicioForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired(), Length(max=100)])
    descripcion = TextAreaField('Descripción', validators=[Optional(), Length(max=500)])
    precio = DecimalField('Precio (COP)', validators=[DataRequired(), NumberRange(min=0)])
    duracion_estimada = StringField('Duración Estimada', validators=[Optional(), Length(max=50)])
    activo = BooleanField('Servicio Activo', default=True)
    
    # Mantener campo URL para compatibilidad hacia atrás
    imagen_url = StringField('URL de Imagen (opcional)', validators=[Optional()])
    
    # Agregar campo para subir imagen
    imagen_file = FileField('Subir Imagen', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Solo archivos de imagen!')
    ])
    
    submit = SubmitField('Guardar Servicio')