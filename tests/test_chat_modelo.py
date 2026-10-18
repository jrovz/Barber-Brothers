import pytest
from alembic.config import Config as AlembicConfig
from alembic.script import ScriptDirectory
from sqlalchemy.exc import IntegrityError

from app import db
from app.models.chat import ChatMensaje
from app.utils.chat_config import chat_activo


def test_chat_mensaje_se_guarda_y_se_ordena(app):
    db.session.add_all([
        ChatMensaje(session_id='sesion-1', rol='user', contenido='Hola'),
        ChatMensaje(session_id='sesion-1', rol='assistant', contenido='¡Hola! ¿En qué te ayudo?'),
        ChatMensaje(session_id='sesion-2', rol='user', contenido='Otra conversación'),
    ])
    db.session.commit()

    propios = ChatMensaje.query.filter_by(session_id='sesion-1').order_by(ChatMensaje.id).all()
    assert [m.rol for m in propios] == ['user', 'assistant']
    assert propios[0].creado is not None


def test_chat_mensaje_rechaza_rol_invalido(app):
    db.session.add(ChatMensaje(session_id='sesion-1', rol='system', contenido='x'))
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_chat_apagado_por_defecto(app):
    assert app.config['CHAT_ENABLED'] is False
    assert chat_activo(app) is False


@pytest.mark.parametrize('enabled, clave, esperado', [
    (True, 'sk-test', True),
    (True, '', False),       # activado pero sin clave: sigue apagado
    (False, 'sk-test', False),  # clave pero sin activar: sigue apagado
    (False, '', False),
])
def test_chat_activo_requiere_activacion_y_clave(app, enabled, clave, esperado):
    app.config['CHAT_ENABLED'] = enabled
    app.config['ANTHROPIC_API_KEY'] = clave
    assert chat_activo(app) is esperado


def test_valores_por_defecto_de_configuracion(app):
    assert app.config['CHAT_MODEL'] == 'claude-haiku-5-5'
    assert app.config['CHAT_MAX_CARACTERES'] == 500
    assert app.config['CHAT_MAX_TURNOS'] == 30
    assert app.config['CHAT_HISTORIAL'] == 12
    assert app.config['CHAT_RATE_LIMIT'] == '20 per hour'
    assert app.config['CHAT_MAX_TOKENS_RESPUESTA'] == 400
    assert app.config['CHAT_MAX_RESERVAS_SESION'] == 2


def test_migraciones_tienen_una_sola_cabeza():
    """Dos cabezas hacen fallar `flask db upgrade`; esto avisa en el CI antes del deploy."""
    cfg = AlembicConfig('migrations/alembic.ini')
    cfg.set_main_option('script_location', 'migrations')
    heads = ScriptDirectory.from_config(cfg).get_heads()
    assert len(heads) == 1, f'Hay varias cabezas de migración: {heads}'
