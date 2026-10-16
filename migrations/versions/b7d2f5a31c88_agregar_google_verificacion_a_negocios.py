"""agregar google_verificacion a negocios

Revision ID: b7d2f5a31c88
Revises: a1c4e7b90d12
Create Date: 2026-10-16 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'b7d2f5a31c88'
down_revision = 'a1c4e7b90d12'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('negocios', schema=None) as batch_op:
        batch_op.add_column(sa.Column('google_verificacion', sa.String(length=100), nullable=True))

    negocios = sa.table(
        'negocios',
        sa.column('slug', sa.String),
        sa.column('google_verificacion', sa.String),
    )
    op.execute(
        negocios.update()
        .where(negocios.c.slug == 'barberbrothers')
        .values(google_verificacion='google17b126f9a1dae6ef.html')
    )


def downgrade():
    with op.batch_alter_table('negocios', schema=None) as batch_op:
        batch_op.drop_column('google_verificacion')
