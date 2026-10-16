import logging
import os
import time

logger = logging.getLogger(__name__)

_CACHE_SEGUNDOS = 60
_cache = {'slug': None, 'negocio': None, 'expira': 0.0}


class _NegocioNulo:
    """Valores neutros para que el sitio no se caiga si falta la fila del negocio.

    Fase 2 reemplazará obtener_negocio() para buscar por dominio en vez de slug;
    esta clase sigue siendo el resultado cuando esa búsqueda tampoco encuentra nada.
    """

    nombre = 'Nuestro negocio'
    nombre_corto = 'Nuestro negocio'
    eslogan = None
    anio_fundacion = None
    telefono = ''
    whatsapp = ''
    telefono_tienda = None
    email_contacto = ''
    instagram_url = None
    tiktok_url = None
    facebook_url = None
    direccion = ''
    ciudad = ''
    departamento = ''
    pais = 'Colombia'
    latitud = None
    longitud = None
    razon_social = None
    nit = None
    direccion_legal = None
    email_datos_personales = None
    dominio = ''
    subdominio = None
    zona_horaria = 'America/Bogota'
    seo_titulo = 'Nuestro negocio'
    seo_descripcion = ''
    seo_palabras_clave = ''
    historia = ''
    horario_atencion = []
    remitente_nombre = 'Nuestro negocio'
    logo_url = None
    favicon_url = None
    color_primario = '#000000'
    color_secundario = '#333333'
    color_acento = '#999999'
    tienda_activa = False
    plan = 'basico'
    activo = True

    def whatsapp_link(self, texto=None):
        return '#'

    def tema_css(self):
        return ''

    def url_logo(self, url_root=''):
        return None

    def datos_publicos(self):
        return {
            'nombre': self.nombre,
            'nombre_corto': self.nombre_corto,
            'telefono': self.telefono,
            'whatsapp': self.whatsapp,
            'color_primario': self.color_primario,
            'color_secundario': self.color_secundario,
            'color_acento': self.color_acento,
        }


def obtener_negocio():
    """Devuelve el negocio actual, cacheado en memoria por 60 segundos.

    Por ahora busca por el slug de la variable de entorno NEGOCIO_SLUG (fase 1).
    La fase 2 reemplaza la búsqueda por dominio, solo en esta función.
    """
    from app.models.negocio import Negocio

    slug = os.environ.get('NEGOCIO_SLUG', 'barberbrothers')
    ahora = time.monotonic()

    if _cache['slug'] == slug and _cache['negocio'] is not None and ahora < _cache['expira']:
        return _cache['negocio']

    negocio = Negocio.query.filter_by(slug=slug).first()

    if negocio is None:
        logger.error("No existe un negocio con slug '%s'; usando valores neutros.", slug)
        negocio = _NegocioNulo()

    _cache['slug'] = slug
    _cache['negocio'] = negocio
    _cache['expira'] = ahora + _CACHE_SEGUNDOS
    return negocio


def limpiar_cache_negocio():
    """Fuerza a que la próxima petición vuelva a consultar la base de datos.

    La caché es por proceso: en producción con varios workers de Gunicorn,
    esto solo limpia la caché del worker que la llama. Los demás workers
    reflejan el cambio en un máximo de 60 segundos.
    """
    _cache['slug'] = None
    _cache['negocio'] = None
    _cache['expira'] = 0.0
