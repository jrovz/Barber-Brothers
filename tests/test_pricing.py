from app import db
from app.models.barbero_servicio import BarberoServicio
from app.models.cliente import Cita
from app.utils.pricing import obtener_precio_servicio, obtener_servicios_barbero
from tests.conftest import login_as


def _desactivar_servicio(barbero, servicio):
    config = BarberoServicio(barbero_id=barbero.id, servicio_id=servicio.id, activo=False)
    db.session.add(config)
    db.session.commit()
    return config


def test_servicio_desactivado_no_ofrece_precio(app, barbero, servicio):
    _desactivar_servicio(barbero, servicio)

    info = obtener_precio_servicio(barbero.id, servicio.id)

    assert info['servicio_activo_para_barbero'] is False


def test_servicio_activo_sin_config_usa_precio_base(app, barbero, servicio):
    info = obtener_precio_servicio(barbero.id, servicio.id)

    assert info['servicio_activo_para_barbero'] is True
    assert info['precio'] == servicio.precio
    assert info['es_personalizado'] is False


def test_servicio_desactivado_no_aparece_como_activo_en_listado(app, barbero, servicio):
    _desactivar_servicio(barbero, servicio)

    resultado = obtener_servicios_barbero(barbero.id)
    item = next(i for i in resultado if i['servicio'].id == servicio.id)

    assert item['activo'] is False


def test_agendar_cita_rechaza_servicio_desactivado(client, barbero, servicio):
    _desactivar_servicio(barbero, servicio)

    resp = client.post('/api/agendar-cita', json={
        'barbero_id': barbero.id,
        'servicio_id': servicio.id,
        'fecha': '2026-09-14',
        'hora': '10:00',
        'nombre': 'Cliente Test',
        'email': 'cliente@test.com',
        'telefono': '3000000000',
    })

    assert resp.status_code == 400
    assert Cita.query.count() == 0


def test_admin_no_guarda_precio_personalizado_negativo(client, admin_user, barbero, servicio):
    login_as(client, admin_user)

    resp = client.post(
        f'/admin/barberos/{barbero.id}/servicios',
        data={
            f'servicio_{servicio.id}_activo': 'on',
            f'servicio_{servicio.id}_precio': '-500',
        },
        follow_redirects=True,
    )

    assert resp.status_code == 200
    config = BarberoServicio.query.filter_by(barbero_id=barbero.id, servicio_id=servicio.id).first()
    assert config is None or config.precio_personalizado is None
