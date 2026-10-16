"""actualizar direccion y coordenadas de Barber Brothers

Revision ID: a1c4e7b90d12
Revises: 2dd4eecaa37b
Create Date: 2026-10-16 10:00:00.000000

La migración que crea `negocios` sembró la dirección y las coordenadas antiguas.
Las plantillas ya usaban los datos unificados (commit 6af2b45); esto los pasa a la base.
"""
from alembic import op
import sqlalchemy as sa


revision = 'a1c4e7b90d12'
down_revision = '2dd4eecaa37b'
branch_labels = None
depends_on = None


def upgrade():
    negocios = sa.table(
        'negocios',
        sa.column('slug', sa.String),
        sa.column('direccion', sa.String),
        sa.column('latitud', sa.Float),
        sa.column('longitud', sa.Float),
        sa.column('seo_descripcion', sa.Text),
    )
    op.execute(
        negocios.update()
        .where(negocios.c.slug == 'barberbrothers')
        .values(
            direccion='Cra. 20 #94D-34, Arcambuko',
            latitud=4.4389,
            longitud=-75.2322,
            seo_descripcion=(
                'Barber Brothers - Barbería profesional en Ibagué con más de 7 años de experiencia. '
                'Cortes modernos, afeitado clásico, arreglo de barba. Reserva tu cita online.'
            ),
        )
    )


def downgrade():
    negocios = sa.table(
        'negocios',
        sa.column('slug', sa.String),
        sa.column('direccion', sa.String),
        sa.column('latitud', sa.Float),
        sa.column('longitud', sa.Float),
    )
    op.execute(
        negocios.update()
        .where(negocios.c.slug == 'barberbrothers')
        .values(direccion='Manzana A casa N°5', latitud=4.4465177, longitud=-75.1810363)
    )
