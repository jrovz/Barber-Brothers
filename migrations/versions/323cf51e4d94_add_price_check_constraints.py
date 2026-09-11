"""Add price check constraints

Revision ID: 323cf51e4d94
Revises: a78c6e6f92f8
Create Date: 2026-09-11 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '323cf51e4d94'
down_revision = 'a78c6e6f92f8'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('servicio', schema=None) as batch_op:
        batch_op.create_check_constraint(
            'ck_servicio_precio_no_negativo', 'precio >= 0'
        )

    with op.batch_alter_table('barbero_servicio', schema=None) as batch_op:
        batch_op.create_check_constraint(
            'ck_barbero_servicio_precio_no_negativo',
            'precio_personalizado IS NULL OR precio_personalizado >= 0'
        )


def downgrade():
    with op.batch_alter_table('barbero_servicio', schema=None) as batch_op:
        batch_op.drop_constraint('ck_barbero_servicio_precio_no_negativo', type_='check')

    with op.batch_alter_table('servicio', schema=None) as batch_op:
        batch_op.drop_constraint('ck_servicio_precio_no_negativo', type_='check')
