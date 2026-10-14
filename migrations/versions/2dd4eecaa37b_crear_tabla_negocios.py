"""crear_tabla_negocios

Revision ID: 2dd4eecaa37b
Revises: 2d2fa96c69c7
Create Date: 2026-10-14 00:00:00.000000

"""
from datetime import datetime

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2dd4eecaa37b'
down_revision = '2d2fa96c69c7'
branch_labels = None
depends_on = None


HISTORIA_BARBER_BROTHERS = (
    "En el año 2017, dos hermanos apasionados por el arte de la barbería decidimos unirnos para crear un "
    "espacio donde los hombres pudieran sentirse orgullosos de su apariencia y relajados en un ambiente "
    "acogedor. Así nació La Barber Brothers, un lugar donde la tradición y la innovación se unen para ofrecer "
    "experiencias únicas.\n\n"
    "Desde nuestros inicios, nos hemos esforzado por brindar servicios de alta calidad, desde cortes de pelo "
    "precisos hasta afeitados suaves y relajantes. Nuestros barberos han sido entrenados para entender las "
    "necesidades de cada cliente y ofrecer soluciones personalizadas.\n\n"
    "A lo largo de los años, hemos visto a hombres de todas las edades y estilos pasar por nuestras puertas, "
    "cada uno con su propia historia y necesidades. Hemos sido testigos de momentos importantes, como bodas y "
    "graduaciones, y hemos ayudado a nuestros clientes a sentirse seguros y confiados en su apariencia.\n\n"
    "La Barber Brothers no es solo un lugar para cortarse el pelo o afeitarse; es un espacio donde los hombres "
    "pueden relajarse, socializar y sentirse parte de una comunidad. Hemos creado un ambiente acogedor y "
    "masculino, donde se puede disfrutar de una buena conversación y un servicio de alta calidad.\n\n"
    "Hoy en día, La Barber Brothers es un lugar emblemático en la comunidad, conocido por su atención al "
    "detalle y su compromiso con la excelencia. Estamos orgullosos de haber podido crecer y evolucionar junto "
    "con nuestros clientes, y estamos emocionados de ver lo que el futuro nos depara.\n\n"
    "Gracias a todos nuestros clientes por haber sido parte de esta historia. Estamos comprometidos con seguir "
    "ofreciendo servicios de alta calidad y hacer que cada visita a La Barber Brothers sea una experiencia "
    "inolvidable.\n\n"
    "¡Visítanos y descubre por qué somos la mejor barbería de la ciudad!"
)

HORARIO_BARBER_BROTHERS = [
    {
        "dias": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        "abre": "08:00",
        "cierra": "18:00",
    },
    {
        "dias": ["Saturday"],
        "abre": "08:00",
        "cierra": "16:00",
    },
]


def upgrade():
    op.create_table(
        'negocios',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('slug', sa.String(length=50), nullable=False),
        sa.Column('nombre', sa.String(length=150), nullable=False),
        sa.Column('nombre_corto', sa.String(length=80), nullable=True),
        sa.Column('eslogan', sa.String(length=200), nullable=True),
        sa.Column('anio_fundacion', sa.Integer(), nullable=True),
        sa.Column('telefono', sa.String(length=20), nullable=True),
        sa.Column('whatsapp', sa.String(length=20), nullable=True),
        sa.Column('telefono_tienda', sa.String(length=20), nullable=True),
        sa.Column('email_contacto', sa.String(length=120), nullable=True),
        sa.Column('instagram_url', sa.String(length=255), nullable=True),
        sa.Column('tiktok_url', sa.String(length=255), nullable=True),
        sa.Column('facebook_url', sa.String(length=255), nullable=True),
        sa.Column('direccion', sa.String(length=200), nullable=True),
        sa.Column('ciudad', sa.String(length=100), nullable=True),
        sa.Column('departamento', sa.String(length=100), nullable=True),
        sa.Column('pais', sa.String(length=100), nullable=True),
        sa.Column('latitud', sa.Float(), nullable=True),
        sa.Column('longitud', sa.Float(), nullable=True),
        sa.Column('razon_social', sa.String(length=200), nullable=True),
        sa.Column('nit', sa.String(length=30), nullable=True),
        sa.Column('direccion_legal', sa.String(length=200), nullable=True),
        sa.Column('email_datos_personales', sa.String(length=120), nullable=True),
        sa.Column('dominio', sa.String(length=150), nullable=True),
        sa.Column('subdominio', sa.String(length=80), nullable=True),
        sa.Column('zona_horaria', sa.String(length=50), nullable=True),
        sa.Column('seo_titulo', sa.String(length=255), nullable=True),
        sa.Column('seo_descripcion', sa.Text(), nullable=True),
        sa.Column('seo_palabras_clave', sa.Text(), nullable=True),
        sa.Column('historia', sa.Text(), nullable=True),
        sa.Column('horario_atencion', sa.JSON(), nullable=True),
        sa.Column('remitente_nombre', sa.String(length=150), nullable=True),
        sa.Column('logo_url', sa.String(length=255), nullable=True),
        sa.Column('favicon_url', sa.String(length=255), nullable=True),
        sa.Column('color_primario', sa.String(length=7), nullable=True),
        sa.Column('color_secundario', sa.String(length=7), nullable=True),
        sa.Column('color_acento', sa.String(length=7), nullable=True),
        sa.Column('tienda_activa', sa.Boolean(), nullable=True),
        sa.Column('plan', sa.String(length=20), nullable=True),
        sa.Column('activo', sa.Boolean(), nullable=True),
        sa.Column('creado', sa.DateTime(), nullable=True),
        sa.Column('actualizado', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug'),
        sa.UniqueConstraint('subdominio'),
    )
    with op.batch_alter_table('negocios', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_negocios_slug'), ['slug'], unique=True)

    negocios = sa.table(
        'negocios',
        sa.column('slug', sa.String),
        sa.column('nombre', sa.String),
        sa.column('nombre_corto', sa.String),
        sa.column('anio_fundacion', sa.Integer),
        sa.column('telefono', sa.String),
        sa.column('whatsapp', sa.String),
        sa.column('email_contacto', sa.String),
        sa.column('instagram_url', sa.String),
        sa.column('tiktok_url', sa.String),
        sa.column('facebook_url', sa.String),
        sa.column('direccion', sa.String),
        sa.column('ciudad', sa.String),
        sa.column('departamento', sa.String),
        sa.column('pais', sa.String),
        sa.column('latitud', sa.Float),
        sa.column('longitud', sa.Float),
        sa.column('dominio', sa.String),
        sa.column('zona_horaria', sa.String),
        sa.column('seo_titulo', sa.String),
        sa.column('seo_descripcion', sa.Text),
        sa.column('seo_palabras_clave', sa.Text),
        sa.column('historia', sa.Text),
        sa.column('horario_atencion', sa.JSON),
        sa.column('remitente_nombre', sa.String),
        sa.column('color_primario', sa.String),
        sa.column('color_secundario', sa.String),
        sa.column('color_acento', sa.String),
        sa.column('tienda_activa', sa.Boolean),
        sa.column('plan', sa.String),
        sa.column('activo', sa.Boolean),
        sa.column('creado', sa.DateTime),
        sa.column('actualizado', sa.DateTime),
    )

    ahora = datetime.utcnow()
    op.bulk_insert(negocios, [{
        'slug': 'barberbrothers',
        # Nombre/teléfono/ciudad: el código tenía datos contradictorios (ver docs/PLAN_FASE_1_MARCA.md,
        # paso 0). "La Barber Brothers" y Ibagué/Tolima se eligieron por tener más evidencia a favor
        # (nombre del lugar en Google Maps, dominio labarberbrothers.com, coordenadas reales del mapa
        # incrustado en contacto.html). Ajustar desde el panel de admin (paso 5) si no es correcto.
        'nombre': 'La Barber Brothers',
        'nombre_corto': 'Barber Brothers',
        'anio_fundacion': 2017,
        'telefono': '3143782855',
        'whatsapp': '573143782855',
        'email_contacto': 'labarberbrothers@gmail.com',
        'instagram_url': 'https://www.instagram.com/la_barberbrothers/',
        'tiktok_url': 'https://www.tiktok.com/@labarberbrothers',
        'facebook_url': 'https://www.facebook.com/barberbrothers/',
        'direccion': 'Manzana A casa N°5',
        'ciudad': 'Ibagué',
        'departamento': 'Tolima',
        'pais': 'Colombia',
        'latitud': 4.4465177,
        'longitud': -75.1810363,
        'dominio': 'labarberbrothers.com',
        'zona_horaria': 'America/Bogota',
        'seo_titulo': 'Barber Brothers - Barbería Profesional en Ibagué | Reserva tu Cita Online',
        'seo_descripcion': (
            'Barber Brothers - Barbería profesional en Ibagué con más de 7 años de experiencia. '
            'Cortes modernos, afeitado clásico, arreglo de barba. Reserva tu cita online. '
            '¡Ubicados en Manzana A casa N°5!'
        ),
        'seo_palabras_clave': (
            'barbería Ibagué, Barber Brothers, corte cabello masculino, afeitado profesional, '
            'barbero Ibagué, citas online barbería, barber shop Tolima, arreglo barba, '
            'servicios barbería, corte infantil'
        ),
        'historia': HISTORIA_BARBER_BROTHERS,
        'horario_atencion': HORARIO_BARBER_BROTHERS,
        'remitente_nombre': 'Barber Brothers',
        'color_primario': '#0a0908',
        'color_secundario': '#302c25',
        'color_acento': '#b39656',
        'tienda_activa': True,
        'plan': 'basico',
        'activo': True,
        'creado': ahora,
        'actualizado': ahora,
    }])


def downgrade():
    with op.batch_alter_table('negocios', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_negocios_slug'))
    op.drop_table('negocios')
