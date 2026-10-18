"""Tests de caracterización: fijan el comportamiento ACTUAL de la reserva web y de la
disponibilidad, para poder mover esa lógica a app/services/ sin cambiar lo que ve el cliente.

No describen el comportamiento ideal sino el real. Si alguno falla tras el refactor,
algo cambió y hay que revisarlo, no ajustar el test.
"""
from datetime import date, datetime, timedelta

import pytest

from app import db
from app.models.barbero import BloqueoHorario, crear_disponibilidad_predeterminada
from app.models.barbero_servicio import BarberoServicio
from app.models.cliente import Cita, Cliente
from tests.conftest import fecha_futura


def _payload(barbero, servicio, fecha=None, hora='10:00', email='cliente@test.com', **extra):
    datos = {
        'barbero_id': barbero.id,
        'servicio_id': servicio.id,
        'fecha': fecha or fecha_futura(),
        'hora': hora,
        'nombre': 'Cliente de Prueba',
        'email': email,
        'telefono': '3000000000',
    }
    datos.update(extra)
    return datos


def _dia_habil(dias_minimos=30):
    """Primer lunes a partir de hoy + dias_minimos (los domingos no hay atención)."""
    d = date.today() + timedelta(days=dias_minimos)
    while d.weekday() != 0:
        d += timedelta(days=1)
    return d


@pytest.fixture
def correos(monkeypatch):
    """Intercepta el envío real de correos y devuelve la lista de envíos."""
    enviados = []
    monkeypatch.setattr('app.models.email.send_email', lambda **kw: enviados.append(kw))
    return enviados


# ---------------------------------------------------------------- reserva

def test_conflicto_409_incluye_detalles(client, barbero, servicio, correos):
    client.post('/api/agendar-cita', json=_payload(barbero, servicio, email='a@test.com'))
    resp = client.post('/api/agendar-cita', json=_payload(barbero, servicio, email='b@test.com'))
    assert resp.status_code == 409
    body = resp.get_json()
    assert 'se solapa' in body['error']
    assert body['conflict_details']['barbero_id'] == barbero.id
    assert body['conflict_details']['duracion_servicio'] == 30
    assert body['conflict_details']['horario_solicitado'].endswith('10:00:00')


def test_cliente_existente_se_reutiliza_y_se_actualiza(client, barbero, servicio, correos):
    existente = Cliente(nombre='Nombre Viejo', email='repetido@test.com', telefono='111')
    db.session.add(existente)
    db.session.commit()

    resp = client.post('/api/agendar-cita', json=_payload(barbero, servicio, email='repetido@test.com'))
    assert resp.status_code == 200

    assert Cliente.query.filter_by(email='repetido@test.com').count() == 1
    cliente = Cliente.query.filter_by(email='repetido@test.com').first()
    assert cliente.nombre == 'Cliente de Prueba'
    assert cliente.telefono == '3000000000'
    assert Cita.query.get(resp.get_json()['cita_id']).cliente_id == cliente.id


def test_cita_guarda_duracion_y_precio_base(client, barbero, servicio, correos):
    resp = client.post('/api/agendar-cita', json=_payload(barbero, servicio))
    cita = Cita.query.get(resp.get_json()['cita_id'])
    assert cita.duracion == 30
    assert float(cita.precio_cobrado) == 20000
    assert cita.es_precio_personalizado is False


def test_cita_usa_precio_personalizado_del_barbero(client, barbero, servicio, correos):
    db.session.add(BarberoServicio(barbero_id=barbero.id, servicio_id=servicio.id,
                                   precio_personalizado=35000, activo=True))
    db.session.commit()
    resp = client.post('/api/agendar-cita', json=_payload(barbero, servicio))
    cita = Cita.query.get(resp.get_json()['cita_id'])
    assert float(cita.precio_cobrado) == 35000
    assert cita.es_precio_personalizado is True


def test_servicio_desactivado_para_el_barbero_devuelve_400(client, barbero, servicio, correos):
    db.session.add(BarberoServicio(barbero_id=barbero.id, servicio_id=servicio.id, activo=False))
    db.session.commit()
    resp = client.post('/api/agendar-cita', json=_payload(barbero, servicio))
    assert resp.status_code == 400
    assert resp.get_json()['error'] == 'Este barbero no ofrece este servicio actualmente.'
    assert Cita.query.count() == 0


def test_servicio_inactivo_devuelve_400_con_mensaje(client, barbero, servicio, correos):
    servicio.activo = False
    db.session.commit()
    resp = client.post('/api/agendar-cita', json=_payload(barbero, servicio))
    assert resp.status_code == 400
    assert resp.get_json()['error'] == 'El servicio seleccionado no está disponible.'


def test_barbero_inactivo_devuelve_mensaje(client, barbero, servicio, correos):
    barbero.activo = False
    db.session.commit()
    resp = client.post('/api/agendar-cita', json=_payload(barbero, servicio))
    assert resp.get_json()['error'] == 'El barbero seleccionado no está disponible.'


@pytest.mark.parametrize('campo', ['barbero_id', 'servicio_id', 'fecha', 'hora', 'nombre', 'email', 'telefono'])
def test_cada_campo_requerido_devuelve_400(client, barbero, servicio, correos, campo):
    payload = _payload(barbero, servicio)
    payload[campo] = ''
    resp = client.post('/api/agendar-cita', json=payload)
    assert resp.status_code == 400
    assert resp.get_json()['error'] == f'Falta el campo o está vacío: {campo}'


def test_formato_invalido_devuelve_400(client, barbero, servicio, correos):
    resp = client.post('/api/agendar-cita', json=_payload(barbero, servicio, hora='diez'))
    assert resp.status_code == 400
    assert resp.get_json()['error'].startswith('Formato de fecha u hora inválido')

    resp = client.post('/api/agendar-cita', json=_payload(barbero, servicio, barbero_id='abc'))
    assert resp.status_code == 400
    assert resp.get_json()['error'].startswith('Formato de fecha u hora inválido')


def test_fecha_pasada_devuelve_mensaje(client, barbero, servicio, correos):
    resp = client.post('/api/agendar-cita', json=_payload(barbero, servicio, fecha='2020-01-01'))
    assert resp.get_json()['error'] == 'No se puede agendar una cita en una fecha u hora pasada.'


def test_fecha_nacimiento_futura_no_deja_cliente_ni_cita(client, barbero, servicio, correos):
    resp = client.post('/api/agendar-cita',
                       json=_payload(barbero, servicio, email='x@test.com', fecha_nacimiento='2999-01-01'))
    assert resp.status_code == 400
    assert Cliente.query.filter_by(email='x@test.com').count() == 0
    assert Cita.query.count() == 0


def test_cita_expirada_no_bloquea_una_nueva_reserva(client, barbero, servicio, correos):
    """Hoy la reserva solo choca con 'confirmada' y 'pendiente_confirmacion'
    (la disponibilidad, en cambio, también cuenta 'expirada'). Se fija tal cual."""
    cliente = Cliente(nombre='Viejo', email='viejo@test.com', telefono='1')
    db.session.add(cliente)
    db.session.flush()
    db.session.add(Cita(cliente_id=cliente.id, barbero_id=barbero.id, servicio_id=servicio.id,
                        fecha=datetime.fromisoformat(f'{fecha_futura()}T10:00:00'),
                        estado='expirada', duracion=30))
    db.session.commit()

    resp = client.post('/api/agendar-cita', json=_payload(barbero, servicio, email='nuevo@test.com'))
    assert resp.status_code == 200


def test_envia_un_correo_con_la_cita_y_el_token(client, barbero, servicio, correos):
    resp = client.post('/api/agendar-cita', json=_payload(barbero, servicio))
    assert resp.status_code == 200
    assert len(correos) == 1
    assert correos[0]['recipients'] == ['cliente@test.com']
    assert '/confirmar-cita/' in correos[0]['text_body']


def test_error_de_validacion_no_envia_correo(client, barbero, servicio, correos):
    client.post('/api/agendar-cita', json=_payload(barbero, servicio, fecha='2020-01-01'))
    assert correos == []


def test_respuesta_exitosa_incluye_cookies_comerciales(client, barbero, servicio, correos):
    resp = client.post('/api/agendar-cita', json=_payload(barbero, servicio))
    assert resp.status_code == 200
    cookies = ' '.join(resp.headers.getlist('Set-Cookie'))
    assert 'favorite_barber_service' in cookies
    assert 'booking_session_tracker' in cookies


def test_respuesta_exitosa_tiene_la_forma_esperada(client, barbero, servicio, correos):
    body = client.post('/api/agendar-cita', json=_payload(barbero, servicio)).get_json()
    assert set(body) == {'success', 'mensaje', 'cita_id'}
    assert body['success'] is True
    assert 'correo' in body['mensaje']


# ----------------------------------------------------------- disponibilidad

def _horas(client, barbero, fecha, servicio_id=None):
    url = f'/api/disponibilidad/{barbero.id}/{fecha}'
    if servicio_id:
        url += f'?servicio_id={servicio_id}'
    return client.get(url)


def test_disponibilidad_forma_del_json(client, barbero, servicio):
    crear_disponibilidad_predeterminada(barbero.id)
    resp = _horas(client, barbero, _dia_habil().isoformat(), servicio.id)
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body) == {'barbero', 'fecha', 'horarios', 'mensaje', 'total_slots', 'duracion_servicio'}
    assert body['barbero'] == barbero.nombre
    assert body['duracion_servicio'] == 30
    assert body['total_slots'] == len(body['horarios'])
    assert body['horarios'][0] == '08:00'
    assert '12:00' not in body['horarios'][:1]  # el primer bloque cierra a las 12:00


def test_disponibilidad_sin_servicio_usa_30_minutos(client, barbero):
    crear_disponibilidad_predeterminada(barbero.id)
    body = _horas(client, barbero, _dia_habil().isoformat()).get_json()
    assert body['duracion_servicio'] == 30


def test_disponibilidad_slot_ocupado_no_aparece(client, barbero, servicio, correos):
    crear_disponibilidad_predeterminada(barbero.id)
    dia = _dia_habil().isoformat()
    assert client.post('/api/agendar-cita', json=_payload(barbero, servicio, fecha=dia, hora='10:00')).status_code == 200
    horas = _horas(client, barbero, dia, servicio.id).get_json()['horarios']
    assert '10:00' not in horas
    assert '10:15' not in horas   # se solapa con la cita de 30 min
    assert '09:30' in horas
    assert '10:30' in horas


def test_disponibilidad_bloqueo_horario_no_aparece(client, barbero, servicio):
    from datetime import time
    crear_disponibilidad_predeterminada(barbero.id)
    dia = _dia_habil()
    db.session.add(BloqueoHorario(barbero_id=barbero.id, fecha=dia,
                                  hora_inicio=time(9, 0), hora_fin=time(10, 0)))
    db.session.commit()
    horas = _horas(client, barbero, dia.isoformat(), servicio.id).get_json()['horarios']
    assert '09:00' not in horas and '09:45' not in horas
    assert '10:00' in horas


def test_disponibilidad_domingo_dice_sin_horario(client, barbero, servicio):
    crear_disponibilidad_predeterminada(barbero.id)
    d = _dia_habil()
    while d.weekday() != 6:
        d += timedelta(days=1)
    body = _horas(client, barbero, d.isoformat(), servicio.id).get_json()
    assert body['horarios'] == []
    assert body['mensaje'] == f'{barbero.nombre} no tiene horario configurado para este día.'


def test_disponibilidad_dia_sin_cupo_mensaje(client, barbero, servicio):
    """Servicio más largo que cualquier bloque: hay horario configurado pero ningún hueco."""
    servicio.duracion_estimada = '9 horas'
    db.session.commit()
    crear_disponibilidad_predeterminada(barbero.id)
    dia = _dia_habil().isoformat()
    body = _horas(client, barbero, dia, servicio.id).get_json()
    assert body['horarios'] == []
    assert body['mensaje'] == f'No hay horarios disponibles para {barbero.nombre} el {dia} con duración de 540 min.'


def test_disponibilidad_fecha_invalida_devuelve_400(client, barbero):
    resp = client.get(f'/api/disponibilidad/{barbero.id}/no-es-fecha')
    assert resp.status_code == 400
    assert resp.get_json()['error'] == 'Formato de fecha inválido. Use YYYY-MM-DD.'


def test_disponibilidad_barbero_inexistente_devuelve_500_por_ahora(client):
    """Defecto conocido: get_or_404 lanza un 404 que el `except Exception` de la ruta
    convierte en 500. Se fija tal cual para que el refactor no lo cambie sin querer;
    cuando se corrija, este test debe pasar a esperar 404."""
    assert client.get('/api/disponibilidad/9999/2030-01-07').status_code == 500
