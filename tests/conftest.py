import pytest

from app import create_app, db as _db
from app.models.admin import User
from app.models.barbero import Barbero
from app.models.servicio import Servicio


@pytest.fixture
def app():
    application = create_app('testing')
    with application.app_context():
        _db.create_all()
        yield application
        _db.session.remove()
        _db.drop_all()


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
        sess['_user_id'] = str(user.id)
        sess['_fresh'] = True
