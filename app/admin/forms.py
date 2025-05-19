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
    categoria_id = SelectField('Categoría', coerce=int, validators=[Optional()])
    cantidad = IntegerField('Cantidad en Inventario', validators=[DataRequired(), NumberRange(min=0)])  # Nuevo campo
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
    # Cambiado de SelectField a StringField
    cliente_nombre = StringField('Nombre del Cliente', validators=[
        DataRequired(message="El nombre del cliente es obligatorio."),
        Length(min=3, max=100, message="El nombre debe tener entre 3 y 100 caracteres.")
    ])
    # cliente_id = SelectField('Cliente', ...) // Eliminado o comentado
    cliente_email = StringField('Correo Electrónico del Cliente', validators=[
        DataRequired(message="El correo electrónico es obligatorio."),
        Email(message="Correo electrónico no válido."),
        Length(max=120)
    ])
    barbero_id = SelectField('Barbero Asignado', coerce=int, validators=[DataRequired(message="Debe seleccionar un barbero.")])
    servicio_id = SelectField('Servicio Solicitado', coerce=int, validators=[DataRequired(message="Debe seleccionar un servicio.")])
    estado = SelectField('Estado de la Cita', choices=[
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada'),
        ('completada', 'Completada')
    ], default='pendiente')
    submit = SubmitField('Guardar Cita')

    def __init__(self, *args, **kwargs):
        super(CitaForm, self).__init__(*args, **kwargs)
        from app.models import Barbero, Servicio # Cliente ya no se importa para choices aquí
        # Las choices de barbero y servicio se siguen poblando como antes
        self.barbero_id.choices = [(0, 'Selecciona un barbero')] + [(b.id, b.nombre) for b in Barbero.query.filter_by(activo=True).order_by(Barbero.nombre).all()]
        self.servicio_id.choices = [(0, 'Selecciona un servicio')] + [(s.id, s.nombre) for s in Servicio.query.filter_by(activo=True).order_by(Servicio.nombre).all()]
        # Añadir opción por defecto también para estado si se desea
        self.estado.choices = [('pendiente', 'Pendiente'), ('confirmada', 'Confirmada'), ('cancelada', 'Cancelada'), ('completada', 'Completada')]

class ClienteFilterForm(FlaskForm):
    segmento = SelectField('Segmento', choices=[
        ('', 'Todos los segmentos'),
        ('nuevo', 'Nuevos'),
        ('ocasional', 'Ocasionales'),
        ('recurrente', 'Recurrentes'),
        ('vip', 'VIP'),
        ('inactivo', 'Inactivos')
    ], validators=[Optional()])
    ordenar_por = SelectField('Ordenar por', choices=[
        ('nombre', 'Nombre'),
        ('visitas', 'Total de visitas'),
        ('ultima_visita', 'Última visita')
    ], validators=[Optional()])
    submit = SubmitField('Filtrar')