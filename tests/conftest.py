import pytest
from datetime import date, timedelta

from app import create_app, db as _db
from app.models.admin import User
from app.models.barbero import Barbero
from app.models.negocio import Negocio
from app.models.servicio import Servicio
from app.utils.negocio_actual import limpiar_cache_negocio


@pytest.fixture
def app():
    application = create_app('testing')
    with application.app_context():
        _db.create_all()
        limpiar_cache_negocio()
        _db.session.add(Negocio(
            slug='barberbrothers',
            nombre='Barbería de Prueba',
            nombre_corto='Barbería de Prueba',
            telefono='3000000000',
            whatsapp='573000000000',
            color_primario='#000000',
            color_secundario='#333333',
            color_acento='#999999',
        ))
        _db.session.commit()
        yield application
        _db.session.remove()
        _db.drop_all()
        limpiar_cache_negocio()


@pytest.fixture
def negocio(app):
    return Negocio.query.filter_by(slug='barberbrothers').first()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def admin_user(app):
    user = User(username='admin_test', email='admin_test@example.com', role='admin')
    user.set_password('adminpass123')
    _db.session.add(user)
    _db.session.commit()
    return user


@pytest.fixture
def cliente_user(app):
    user = User(username='cliente_test', email='cliente_test@example.com', role='cliente')
    user.set_password('clientepass123')
    _db.session.add(user)
    _db.session.commit()
    return user


@pytest.fixture
def barbero(app):
    b = Barbero(nombre='Barbero de Prueba', especialidad='Corte', activo=True)
    _db.session.add(b)
    _db.session.commit()
    return b


@pytest.fixture
def servicio(app):
    s = Servicio(nombre='Corte de Prueba', precio=20000, duracion_estimada='30 min', activo=True)
    _db.session.add(s)
    _db.session.commit()
    return s


def login_as(client, user):
    """Fuerza una sesión autenticada para `user` dentro del contexto de una request real."""
    with client.session_transaction() as sess:
        sess['_user_id'] = user.get_id()
        sess['_fresh'] = True


def fecha_futura(dias=30):
    """Fecha en formato YYYY-MM-DD siempre en el futuro, para no depender del día en que corren las pruebas."""
    return (date.today() + timedelta(days=dias)).isoformat()
