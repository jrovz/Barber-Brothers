from app import db
from datetime import datetime
import re
from urllib.parse import quote

_COLOR_HEX = re.compile(r'^#[0-9a-fA-F]{6}$')


class Negocio(db.Model):
    __tablename__ = 'negocios'

    id = db.Column(db.Integer, primary_key=True)

    # Identidad
    slug = db.Column(db.String(50), unique=True, nullable=False, index=True)
    nombre = db.Column(db.String(150), nullable=False)
    nombre_corto = db.Column(db.String(80))
    eslogan = db.Column(db.String(200))
    anio_fundacion = db.Column(db.Integer)

    # Contacto
    telefono = db.Column(db.String(20))
    whatsapp = db.Column(db.String(20))
    telefono_tienda = db.Column(db.String(20))
    email_contacto = db.Column(db.String(120))

    # Redes
    instagram_url = db.Column(db.String(255))
    tiktok_url = db.Column(db.String(255))
    facebook_url = db.Column(db.String(255))

    # Ubicación
    direccion = db.Column(db.String(200))
    ciudad = db.Column(db.String(100))
    departamento = db.Column(db.String(100))
    pais = db.Column(db.String(100), default='Colombia')
    latitud = db.Column(db.Float)
    longitud = db.Column(db.Float)

    # Legal
    razon_social = db.Column(db.String(200))
    nit = db.Column(db.String(30))
    direccion_legal = db.Column(db.String(200))
    email_datos_personales = db.Column(db.String(120))

    # Web
    dominio = db.Column(db.String(150))
    subdominio = db.Column(db.String(80), unique=True)
    zona_horaria = db.Column(db.String(50), default='America/Bogota')
    # Nombre del archivo de verificación de Google Search Console, p. ej. 'google123abc.html'
    google_verificacion = db.Column(db.String(100))

    # SEO
    seo_titulo = db.Column(db.String(255))
    seo_descripcion = db.Column(db.Text)
    seo_palabras_clave = db.Column(db.Text)

    # Contenido
    historia = db.Column(db.Text)
    horario_atencion = db.Column(db.JSON)

    # Correo
    remitente_nombre = db.Column(db.String(150))

    # Visual
    logo_url = db.Column(db.String(255))
    favicon_url = db.Column(db.String(255))
    color_primario = db.Column(db.String(7))
    color_secundario = db.Column(db.String(7))
    color_acento = db.Column(db.String(7))

    # Producto
    tienda_activa = db.Column(db.Boolean, default=True)
    plan = db.Column(db.String(20), default='basico')
    activo = db.Column(db.Boolean, default=True)

    # Auditoría
    creado = db.Column(db.DateTime, default=datetime.utcnow)
    actualizado = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Negocio {self.slug}>'

    def whatsapp_link(self, texto=None):
        base = f'https://wa.me/{self.whatsapp}'
        if texto:
            return f'{base}?text={quote(texto)}'
        return base

    def url_logo(self, url_root=''):
        """Logo del negocio; si es una ruta relativa y se da url_root, devuelve la URL absoluta."""
        if not self.logo_url:
            return None
        if self.logo_url.startswith('/') and url_root:
            return url_root.rstrip('/') + self.logo_url
        return self.logo_url

    def tema_css(self):
        """Declaraciones CSS (sin selector) con los colores válidos del negocio.

        Solo se emiten colores #RRGGBB: el resultado se imprime sin escapar en la plantilla.
        """
        variables = [
            ('--color-bg-main', self.color_primario),
            ('--color-border', self.color_secundario),
            ('--color-accent', self.color_acento),
        ]
        declaraciones = [f'{nombre}: {valor};' for nombre, valor in variables
                         if valor and _COLOR_HEX.match(valor)]
        if self.color_acento and _COLOR_HEX.match(self.color_acento):
            declaraciones.append(
                f'--color-accent-hover: color-mix(in srgb, {self.color_acento} 80%, white);')
        return ' '.join(declaraciones)

    def datos_publicos(self):
        """Lo que puede ver el navegador. Nunca NIT ni correos internos."""
        return {
            'nombre': self.nombre,
            'nombre_corto': self.nombre_corto,
            'telefono': self.telefono,
            'whatsapp': self.whatsapp,
            'color_primario': self.color_primario if self.color_primario and _COLOR_HEX.match(self.color_primario) else None,
            'color_secundario': self.color_secundario if self.color_secundario and _COLOR_HEX.match(self.color_secundario) else None,
            'color_acento': self.color_acento if self.color_acento and _COLOR_HEX.match(self.color_acento) else None,
        }
