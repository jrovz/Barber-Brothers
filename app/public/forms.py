from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, validators

class CheckoutForm(FlaskForm):
    nombre = StringField('Nombre completo', [
        validators.DataRequired(message="El nombre es obligatorio"),
        validators.Length(min=2, max=100, message="El nombre debe tener entre 2 y 100 caracteres")
    ])
    
    email = StringField('Correo electrónico', [
        validators.DataRequired(message="El email es obligatorio"),
        validators.Email(message="Ingresa un email válido"),
        validators.Length(max=120, message="El email es demasiado largo")
    ])
    
    telefono = StringField('Teléfono', [
        validators.DataRequired(message="El teléfono es obligatorio"),
        validators.Length(min=7, max=20, message="El teléfono debe tener entre 7 y 20 caracteres")
    ])
    
    notas = TextAreaField('Notas adicionales (opcional)', [
        validators.Length(max=500, message="Las notas no pueden exceder 500 caracteres")
    ]) 