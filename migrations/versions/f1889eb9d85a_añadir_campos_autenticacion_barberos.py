"""añadir_campos_autenticacion_barberos

Revision ID: f1889eb9d85a
Revises: 6365f72a12fc
Create Date: 2025-06-19 10:57:18.047457

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f1889eb9d85a'
down_revision = '6365f72a12fc'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('barbero', schema=None) as batch_op:
        batch_op.add_column(sa.Column('username', sa.String(length=80), nullable=True))
        batch_op.add_column(sa.Column('password_hash', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('tiene_acceso_web', sa.Boolean(), nullable=True))
        batch_op.create_unique_constraint(None, ['username'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('barbero', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='unique')
        batch_op.drop_column('tiene_acceso_web')
        batch_op.drop_column('password_hash')
        batch_op.drop_column('username')

    # ### end Alembic commands ###
