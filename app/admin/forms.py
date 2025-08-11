# filepath: app/admin/forms.py
"""
Formularios del panel de administración de Barber Brothers.

Este módulo define los formularios (WTForms) utilizados en el área de
administración. Cada formulario se centra en una entidad o flujo específico y
aplica validaciones tanto genéricas como de negocio. Se utilizan además campos
de carga de archivos con restricciones de tipo para imágenes.

Resumen de formularios y validaciones
- DataRequiredAllowZero (validador personalizado):
  - Permite explícitamente el valor 0 en campos que por defecto WTForms
    consideraría falsy. También se utiliza el valor sentinela -1 para forzar la
    selección válida en listas desplegables.

- LoginForm y BarberoLoginForm:
  - Autenticación para administradores y barberos con `username`, `password` y
    opción "Recuérdame". Longitudes mínimas razonables en usuario, contraseña obligatoria.

- CategoriaForm:
  - Campo `nombre` con validación de unicidad mediante consulta a `Categoria`.
    Durante edición, permite el mismo nombre si corresponde al registro actual.

- ProductoForm:
  - Campos: `nombre`, `descripcion`, `precio`, `categoria_id`, `cantidad`.
  - Carga de imagen por URL o archivo (`imagen_url`, `imagen_file`).
  - En `__init__` rellena `categoria_id.choices` con categorías ordenadas e
    inserta opción inicial "--- Sin Categoría ---" con id 0 para representar
    ausencia de categoría (nullable en BD).

- BarberoForm:
  - Campos principales: `nombre`, `especialidad`, `descripcion`, `activo`,
    `imagen_file`/`imagen_url`.
  - Acceso web opcional: `tiene_acceso_web`, `username`, `password`,
    `confirmar_password`.
  - Validaciones:
    - `validate_username`: verifica unicidad en `Barbero.username`. Para edición
      se espera que el controlador asigne `form.barbero_id` para permitir el
      mismo usuario en el registro actual.
    - `validate_password` y `validate_confirmar_password`: obligan contraseña y
      consistencia si se habilita el acceso web.

- ServicioForm:
  - Campos: `nombre`, `descripcion`, `precio`, `duracion_estimada`, `activo`,
    `orden` (posición en Home).
  - Imagen principal por URL o archivo, y soporte de carga múltiple con
    `imagenes_files` para galería del servicio (tipos permitidos: jpg, jpeg,
    png, gif, webp).

- DisponibilidadForm:
  - Define `dia_semana` con choices [-1, 0..5] usando `DataRequiredAllowZero`
    para forzar selección válida. Campos `hora_inicio` y `hora_fin` en formato
    HH:MM y `activo`.

- CitaForm:
  - Datos del cliente: `cliente_nombre`, `cliente_email` (con validación `Email`).
  - Selección de `barbero_id` y `servicio_id` poblados en `__init__` con
    entidades activas y opción inicial de selección (id 0).
  - `estado` con choices fijos y valor por defecto `pendiente_confirmacion`.

- ClienteFilterForm:
  - Filtros para listados de clientes: `segmento` y `ordenar_por`, ambos
    opcionales, más `submit`.

Consideraciones generales
- Tipos de archivo permitidos se limitan a imágenes para campos de subida.
- Los placeholders y opciones sentinela (0, -1) están pensados para UX clara y
  validaciones coherentes en el servidor.
- Algunos validadores consultan modelos (por ejemplo, `Categoria`, `Barbero`) y
  dependen de la base de datos disponible en el contexto de la aplicación.
"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, FloatField, TextAreaField, URLField, SelectField, DecimalField, DateTimeField, IntegerField
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional, URL, ValidationError # Añadir ValidationError
from flask_wtf.file import FileField, FileAllowed, MultipleFileField
from app.models.categoria import Categoria # Importar el modelo Categoria

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

class LoginForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired(), Length(min=4, max=64)])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    remember_me = BooleanField('Recuérdame')
    submit = SubmitField('Iniciar Sesión')

class BarberoLoginForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    remember_me = BooleanField('Recuérdame')
    submit = SubmitField('Acceder')

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
    imagen_url = StringField('URL de Imagen (opcional)', validators=[Optional()], render_kw={"autocomplete": "off", "placeholder": "https://ejemplo.com/imagen.jpg"})
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
    
    # Campos de acceso web
    tiene_acceso_web = BooleanField('Permitir acceso web', default=False)
    username = StringField('Usuario (para acceso web)', validators=[Optional(), Length(min=3, max=80)])
    password = PasswordField('Contraseña (para acceso web)', validators=[Optional(), Length(min=6, max=100)])
    confirmar_password = PasswordField('Confirmar Contraseña', validators=[Optional()])
    
    submit = SubmitField('Guardar')
    imagen_url = StringField('URL de Imagen (opcional)', validators=[Optional(), URL(message="URL no válida")], render_kw={"autocomplete": "off", "placeholder": "https://ejemplo.com/imagen.jpg"})
    
    def validate_username(self, username):
        """Validar que el username sea único"""
        if self.tiene_acceso_web.data and username.data:
            from app.models.barbero import Barbero
            barbero = Barbero.query.filter_by(username=username.data).first()
            if barbero:
                # Si estamos editando y el username pertenece al barbero actual, permitirlo
                if hasattr(self, 'barbero_id') and barbero.id != self.barbero_id:
                    raise ValidationError('Este nombre de usuario ya está en uso.')
                elif not hasattr(self, 'barbero_id'):
                    raise ValidationError('Este nombre de usuario ya está en uso.')
    
    def validate_password(self, password):
        """Validar contraseña si se requiere acceso web"""
        if self.tiene_acceso_web.data and not password.data:
            raise ValidationError('La contraseña es obligatoria para el acceso web.')
    
    def validate_confirmar_password(self, confirmar_password):
        """Validar que las contraseñas coincidan"""
        if self.tiene_acceso_web.data and self.password.data and confirmar_password.data:
            if self.password.data != confirmar_password.data:
                raise ValidationError('Las contraseñas no coinciden.')
class ServicioForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired(), Length(max=100)])
    descripcion = TextAreaField('Descripción', validators=[Optional(), Length(max=500)])
    precio = DecimalField('Precio (COP)', validators=[DataRequired(), NumberRange(min=0)])
    duracion_estimada = StringField('Duración Estimada', validators=[Optional(), Length(max=50)])
    activo = BooleanField('Servicio Activo', default=True)
    
    orden = IntegerField('Posición en el Home', validators=[DataRequired(), NumberRange(min=0)], default=0)
    # Mantener campo URL para compatibilidad hacia atrás
    imagen_url = StringField('URL de Imagen (opcional)', validators=[Optional()], render_kw={"autocomplete": "off", "placeholder": "https://ejemplo.com/imagen.jpg"})
    
    # Campo para subir múltiples imágenes
    imagenes_files = MultipleFileField('Subir Imágenes', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Solo archivos de imagen!')
    ])
    
    # Mantener campo individual para compatibilidad
    imagen_file = FileField('Subir Imagen Individual', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Solo archivos de imagen!')
    ])
    
    submit = SubmitField('Guardar Servicio')

    
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
        ('pendiente_confirmacion', 'Pendiente Confirmación'),
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada'),
        ('completada', 'Completada'),
        ('expirada', 'Expirada')
    ], default='pendiente_confirmacion')
    submit = SubmitField('Guardar Cita')

    def __init__(self, *args, **kwargs):
        super(CitaForm, self).__init__(*args, **kwargs)
        from app.models import Barbero, Servicio # Cliente ya no se importa para choices aquí
        # Las choices de barbero y servicio se siguen poblando como antes
        self.barbero_id.choices = [(0, 'Selecciona un barbero')] + [(b.id, b.nombre) for b in Barbero.query.filter_by(activo=True).order_by(Barbero.nombre).all()]
        self.servicio_id.choices = [(0, 'Selecciona un servicio')] + [(s.id, s.nombre) for s in Servicio.query.filter_by(activo=True).order_by(Servicio.nombre).all()]
        # Añadir opción por defecto también para estado si se desea
        self.estado.choices = [('pendiente_confirmacion', 'Pendiente Confirmación'), ('confirmada', 'Confirmada'), ('cancelada', 'Cancelada'), ('completada', 'Completada'), ('expirada', 'Expirada')]

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