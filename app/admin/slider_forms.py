from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, BooleanField, IntegerField, validators
from wtforms.widgets import TextArea

class SliderForm(FlaskForm):
    titulo = StringField('Título', [
        validators.DataRequired(message="El título es obligatorio"),
        validators.Length(min=3, max=200, message="El título debe tener entre 3 y 200 caracteres")
    ])
    
    subtitulo = StringField('Subtítulo', [
        validators.Length(max=300, message="El subtítulo no puede exceder 300 caracteres")
    ])
    
    tipo = SelectField('Tipo de Slide', 
        choices=[
            ('imagen', 'Imagen'),
            ('instagram', 'Publicación de Instagram')
        ],
        validators=[validators.DataRequired(message="Debes seleccionar un tipo")]
    )
    
    # Para slides de imagen
    imagen = FileField('Imagen del Slide', 
        validators=[
            FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 
                       'Solo se permiten archivos de imagen (jpg, jpeg, png, gif, webp)')
        ]
    )
    
    # Para slides de Instagram
    instagram_embed_code = TextAreaField('Código Embed de Instagram',
        widget=TextArea(),
        render_kw={
            "rows": 8,
            "placeholder": "Pega aquí el código HTML completo del embed de Instagram..."
        }
    )
    
    # Control de visualización
    activo = BooleanField('Slide Activo', default=True)
    
    orden = IntegerField('Orden de Visualización', [
        validators.NumberRange(min=0, max=100, message="El orden debe estar entre 0 y 100")
    ], default=0)
    
    def validate(self, extra_validators=None):
        """Validación personalizada según el tipo de slide"""
        if not super().validate(extra_validators):
            return False
        
        if self.tipo.data == 'imagen':
            # Para slides de imagen, validar que tenga imagen (al crear) o sea una edición
            if not self.imagen.data and not hasattr(self, '_editing'):
                self.imagen.errors.append('Debes subir una imagen para este tipo de slide')
                return False
                
        elif self.tipo.data == 'instagram':
            # Para slides de Instagram, validar que tenga código embed
            if not self.instagram_embed_code.data:
                self.instagram_embed_code.errors.append('Debes proporcionar el código embed de Instagram')
                return False
            
            # Validar que el código contenga elementos típicos de Instagram
            embed_code = self.instagram_embed_code.data.lower()
            if 'instagram' not in embed_code or 'blockquote' not in embed_code:
                self.instagram_embed_code.errors.append('El código no parece ser un embed válido de Instagram')
                return False
        
        return True 