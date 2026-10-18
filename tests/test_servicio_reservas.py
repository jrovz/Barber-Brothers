"""El servicio de reservas se puede usar sin HTTP ni cookies (así lo usará el chat)."""
import pytest

from app import db
from app.models.cliente import Cita, Cliente
from app.services import reservas
from app.services.reservas import crear_cita
from tests.conftest import fecha_futura


def _datos(barbero, servicio, **cambios):
    datos = {
        'barbero_id': barbero.id,
        'servicio_id': servicio.id,
        'fecha': fecha_futura(),
        'hora': '10:00',
        'nombre': 'Cliente Servicio',
        'email': 'servicio@test.com',
        'telefono': '3001112222',
    }
    datos.update(cambios)
    return datos


@pytest.fixture
def correos(monkeypatch):
    enviados = []
    monkeypatch.setattr(reservas, 'send_appointment_confirmation_email',
                        lambda **kw: enviados.append(kw))
    return enviados


def test_crea_cita_pendiente_y_devuelve_token(app, barbero, servicio, correos):
    r = crear_cita(_datos(barbero, servicio))
    assert r.ok and r.error is None
    assert r.cita.estado == 'pendiente_confirmacion'
    assert r.cita.duracion == 30
    assert Cita.verify_confirmation_token(r.token) is not None
    assert len(correos) == 1
    assert correos[0]['cita'] is r.cita and correos[0]['token'] == r.token
    assert correos[0]['cliente_email'] == 'servicio@test.com'


def test_enviar_correo_false_no_envia(app, barbero, servicio, correos):
    r = crear_cita(_datos(barbero, servicio), enviar_correo=False)
    assert r.ok
    assert correos == []


def test_el_servicio_no_depende_de_http():
    """Ni petición, ni respuesta, ni cookies: eso es cosa de cada canal (web, chat)."""
    for nombre in ('request', 'jsonify', 'make_response', 'session', 'g', 'BusinessCookieManager'):
        assert not hasattr(reservas, nombre), f'reservas importa {nombre}'


@pytest.mark.parametrize('cambios, codigo, http', [
    ({'telefono': ''}, 'campo_faltante', 400),
    ({'hora': 'diez'}, 'formato_invalido', 400),
    ({'barbero_id': 'abc'}, 'formato_invalido', 400),
    ({'fecha': '2020-01-01'}, 'fecha_pasada', 400),
    ({'barbero_id': 9999}, 'barbero_no_disponible', 400),
    ({'servicio_id': 9999}, 'servicio_no_disponible', 400),
    ({'fecha_nacimiento': '2999-01-01'}, 'nacimiento_futuro', 400),
    ({'fecha_nacimiento': '20-05-1995'}, 'nacimiento_invalido', 400),
])
def test_errores_de_validacion(app, barbero, servicio, correos, cambios, codigo, http):
    r = crear_cita(_datos(barbero, servicio, **cambios))
    assert not r.ok and r.cita is None and r.token is None
    assert r.error.codigo == codigo
    assert r.error.http == http
    assert Cita.query.count() == 0
    assert correos == []


def test_error_deja_la_sesion_limpia_para_liberar_el_bloqueo(app, barbero, servicio):
    """Tras un error no debe quedar nada pendiente en la sesión (ni cliente a medias)."""
    crear_cita(_datos(barbero, servicio, fecha_nacimiento='2999-01-01'))
    assert not db.session.new and not db.session.dirty
    assert Cliente.query.count() == 0


def test_conflicto_devuelve_409_con_detalles(app, barbero, servicio, correos):
    assert crear_cita(_datos(barbero, servicio, email='a@test.com')).ok
    r = crear_cita(_datos(barbero, servicio, email='b@test.com'))
    assert r.error.codigo == 'conflicto_horario'
    assert r.error.http == 409
    cuerpo = r.error.cuerpo()
    assert cuerpo['error'].startswith('Este horario se solapa')
    assert cuerpo['conflict_details']['barbero_id'] == barbero.id
    assert cuerpo['conflict_details']['duracion_servicio'] == 30
    assert len(correos) == 1  # solo la primera reserva mandó correo


def test_cuerpo_de_error_sin_extra(app, barbero, servicio):
    r = crear_cita(_datos(barbero, servicio, fecha='2020-01-01'))
    assert r.error.cuerpo() == {'error': 'No se puede agendar una cita en una fecha u hora pasada.'}


def test_barbero_que_no_ofrece_el_servicio(app, barbero, servicio):
    from app.models.barbero_servicio import BarberoServicio
    db.session.add(BarberoServicio(barbero_id=barbero.id, servicio_id=servicio.id, activo=False))
    db.session.commit()
    r = crear_cita(_datos(barbero, servicio))
    assert r.error.codigo == 'barbero_sin_servicio'
    assert Cita.query.count() == 0
    assert Cliente.query.count() == 0


def test_notas_se_guardan(app, barbero, servicio, correos):
    r = crear_cita(_datos(barbero, servicio, notas='Corte bajo'))
    assert r.cita.notas == 'Corte bajo'
