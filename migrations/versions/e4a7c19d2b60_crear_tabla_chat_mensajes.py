"""crear tabla chat_mensajes para el historial del chatbot

Revision ID: e4a7c19d2b60
Revises: c3e9a6d47f15
Create Date: 2026-10-18 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e4a7c19d2b60'
down_revision = 'c3e9a6d47f15'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'chat_mensajes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(length=64), nullable=False),
        sa.Column('rol', sa.String(length=10), nullable=False),
        sa.Column('contenido', sa.Text(), nullable=False),
        sa.Column('creado', sa.DateTime(), nullable=False),
        sa.CheckConstraint("rol IN ('user', 'assistant')", name='ck_chat_mensaje_rol'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('chat_mensajes', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_chat_mensajes_session_id'), ['session_id'], unique=False)


def downgrade():
    with op.batch_alter_table('chat_mensajes', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_chat_mensajes_session_id'))

    op.drop_table('chat_mensajes')
