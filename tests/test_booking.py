from app.models.cliente import Cita


def _payload(barbero, servicio, fecha='2026-09-01', hora='10:00', email='cliente@test.com'):
    return {
        'barbero_id': barbero.id,
        'servicio_id': servicio.id,
        'fecha': fecha,
        'hora': hora,
        'nombre': 'Cliente de Prueba',
        'email': email,
        'telefono': '3000000000',
    }


def test_agendar_cita_crea_cita_pendiente(client, barbero, servicio):
    resp = client.post('/api/agendar-cita', json=_payload(barbero, servicio))
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True

    cita = Cita.query.get(data['cita_id'])
    assert cita is not None
    assert cita.estado == 'pendiente_confirmacion'
    assert cita.barbero_id == barbero.id
    assert cita.servicio_id == servicio.id


def test_agendar_cita_horario_duplicado_devuelve_409(client, barbero, servicio):
    primero = client.post('/api/agendar-cita', json=_payload(barbero, servicio, email='primero@test.com'))
    assert primero.status_code == 200

    segundo = client.post('/api/agendar-cita', json=_payload(barbero, servicio, email='segundo@test.com'))
    assert segundo.status_code == 409


def test_agendar_cita_campo_faltante_devuelve_400(client, barbero, servicio):
    payload = _payload(barbero, servicio)
    del payload['telefono']
    resp = client.post('/api/agendar-cita', json=payload)
    assert resp.status_code == 400


def test_confirmar_cita_con_token_valido(app, client, barbero, servicio):
    resp = client.post('/api/agendar-cita', json=_payload(barbero, servicio))
    cita_id = resp.get_json()['cita_id']

    with app.app_context():
        cita = Cita.query.get(cita_id)
        token = cita.generate_confirmation_token()

    confirm_resp = client.get(f'/confirmar-cita/{token}')
    assert confirm_resp.status_code == 200

    with app.app_context():
        cita = Cita.query.get(cita_id)
        assert cita.estado == 'confirmada'
        assert cita.confirmed_at is not None


def test_confirmar_cita_con_token_invalido_no_falla(client):
    resp = client.get('/confirmar-cita/token-invalido-o-vencido')
    assert resp.status_code == 200
