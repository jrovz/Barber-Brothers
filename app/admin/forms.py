# filepath: app/admin/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, FloatField, TextAreaField, URLField, SelectField, DecimalField, DateTimeField, IntegerField
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional, URL, ValidationError # Añadir ValidationError
from flask_wtf.file import FileField, FileAllowed
from app.models.categoria import Categoria # Importar el modelo Categoria

class LoginForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired(), Length(min=4, max=64)])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    remember_me = BooleanField('Recuérdame')
    submit = SubmitField('Iniciar Sesión')

class CategoriaForm(FlaskForm):
    nombre = StringField('Nombre de la Categoría', validators=[DataRequired(), Length(max=100)])
    submit = SubmitField('Guardar Categoría')

    def validate_nombre(self, nombre):
        # Verificar si la categoría ya existe (ignorando el caso actual si se está editando)
        categoria_existente = Categoria.query.filter(Categoria.nombre.ilike(nombre.data)).first()
        if categoria_existente:
            # Si estamos editando y el nombre es el mismo que el original, permitirlo
            if hasattr(self, 'obj') and self.obj and self.obj.id == categoria_existente.id:
                return
            raise ValidationError('Esta categoría ya existe.')

class ProductoForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired(), Length(max=100)])
    descripcion = TextAreaField('Descripción', validators=[Optional(), Length(max=500)])
    precio = DecimalField('Precio (COP)', validators=[DataRequired(), NumberRange(min=0)])
    
    # Cambiar StringField a SelectField para categoría
    categoria_id = SelectField('Categoría', coerce=int, validators=[Optional()]) # Usar Optional si una categoría no es estrictamente requerida
    
    imagen_url = StringField('URL de Imagen (opcional)', validators=[Optional()])
    imagen_file = FileField('Subir Imagen', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Solo archivos de imagen!')
    ])
    submit = SubmitField('Guardar Producto')

    def __init__(self, *args, **kwargs):
        super(ProductoForm, self).__init__(*args, **kwargs)
        # Poblar las opciones del SelectField de categorías
        self.categoria_id.choices = [(c.id, c.nombre) for c in Categoria.query.order_by(Categoria.nombre).all()]
        # Añadir una opción por defecto si se desea, por ejemplo, "Sin categoría"
        self.categoria_id.choices.insert(0, (0, '--- Sin Categoría ---')) # (0 o None, dependiendo de si categoria_id puede ser NULL)

class BarberoForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired(), Length(min=2, max=100)])
    especialidad = StringField('Especialidad', validators=[Length(max=100)])
    descripcion = TextAreaField('Descripción')
    imagen_file = FileField('Imagen', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Solo imágenes: jpg, png, jpeg')])
    activo = BooleanField('Activo', default=True)
    submit = SubmitField('Guardar')

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

    
class DisponibilidadForm(FlaskForm):
    dia_semana = SelectField('Día de la Semana', choices=[
        (0, 'Lunes'), (1, 'Martes'), (2, 'Miércoles'), 
        (3, 'Jueves'), (4, 'Viernes'), (5, 'Sábado')
    ], coerce=int, validators=[DataRequired()])
    hora_inicio = StringField('Hora de Inicio (HH:MM)', validators=[DataRequired()])
    hora_fin = StringField('Hora de Fin (HH:MM)', validators=[DataRequired()])
    activo = BooleanField('Activo', default=True)
    
class CitaForm(FlaskForm):
    # 1. Cambiar a SelectField para el ID del cliente
    cliente_id = SelectField('Cliente', coerce=int, validators=[
        DataRequired(message="Debe seleccionar un cliente.")
    ])

    # 2. Campo Barbero (sin cambios aquí, se estilizará con CSS)
    barbero_id = SelectField('Barbero Asignado', coerce=int, validators=[DataRequired(message="Debe seleccionar un barbero.")])

    # 3. Campo Fecha (sin cambios aquí, se usará JS para el picker)
    # Asegúrate que el formato coincida con el que usará el date picker
    fecha = DateTimeField('Fecha y Hora de la Cita', format='%Y-%m-%d %H:%M', validators=[DataRequired(message="La fecha y hora son obligatorias.")])

    servicio = SelectField('Servicio Solicitado', validators=[DataRequired(message="Debe seleccionar un servicio.")])
    estado = SelectField('Estado de la Cita', choices=[
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada'),
        ('completada', 'Completada')
    ], default='pendiente')
    submit = SubmitField('Guardar Cita')

    # Método para poblar choices dinámicamente (opcional pero recomendado)
    def __init__(self, *args, **kwargs):
        super(CitaForm, self).__init__(*args, **kwargs)
        # Poblar barberos y servicios aquí si no se hace en la ruta
        # from app.models import Barbero, Servicio, Cliente # Asegúrate de importar Cliente si lo usas aquí
        # self.cliente_id.choices = [(c.id, c.nombre) for c in Cliente.query.order_by(Cliente.nombre).all()] # Ejemplo
        # self.barbero_id.choices = [(b.id, b.nombre) for b in Barbero.query.filter_by(activo=True).order_by(Barbero.nombre).all()]
        # self.servicio.choices = [(s.nombre, s.nombre) for s in Servicio.query.order_by(Servicio.nombre).all()]