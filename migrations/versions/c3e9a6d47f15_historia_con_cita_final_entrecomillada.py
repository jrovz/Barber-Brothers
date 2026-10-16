"""historia: la frase final de Barber Brothers queda entrecomillada

Revision ID: c3e9a6d47f15
Revises: b7d2f5a31c88
Create Date: 2026-10-16 15:00:00.000000

La plantilla pasa a leer la historia desde `negocios.historia`. La frase final se mostraba
en cursiva y entre comillas; ahora un párrafo entrecomillado se dibuja así, así que se
entrecomilla en los datos para que la página se vea idéntica.
Solo se toca si el texto todavía termina como lo sembró la migración 2dd4eecaa37b.
"""
from alembic import op
import sqlalchemy as sa


revision = 'c3e9a6d47f15'
down_revision = 'b7d2f5a31c88'
branch_labels = None
depends_on = None

FRASE = '¡Visítanos y descubre por qué somos la mejor barbería de la ciudad!'


def _reemplazar(antes, despues):
    conexion = op.get_bind()
    fila = conexion.execute(
        sa.text("SELECT historia FROM negocios WHERE slug = 'barberbrothers'")
    ).first()
    if not fila or not fila[0] or not fila[0].endswith(antes):
        return
    nueva = fila[0][:-len(antes)] + despues
    conexion.execute(
        sa.text("UPDATE negocios SET historia = :h WHERE slug = 'barberbrothers'"),
        {'h': nueva},
    )


def upgrade():
    _reemplazar('\n\n' + FRASE, '\n\n"' + FRASE + '"')


def downgrade():
    _reemplazar('\n\n"' + FRASE + '"', '\n\n' + FRASE)
