from app.models.cliente import Cita
from tests.conftest import fecha_futura, login_as


def _form_data(barbero, servicio, hora, estado='pendiente_confirmacion',
                email='cliente@test.com', nombre='Cliente de Prueba', fecha=None):
    return {
        'cliente_nombre': nombre,
        'cliente_email': email,
        'cliente_telefono': '3000000000',
        'barbero_id': str(barbero.id),
        'servicio_id': str(servicio.id),
        'estado': estado,
        'fecha_cita': fecha or fecha_futura(),
        'hora_cita': hora,
        'notas_cita': '',
    }


def test_crear_cita_admin_guarda_la_duracion_real_del_servicio(client, admin_user, barbero, servicio):
    """Antes, toda cita creada desde el admin quedaba con duracion=30 (el default del
    modelo) sin importar el servicio elegido, lo que rompía el cálculo de disponibilidad
    para cualquier servicio con otra duración."""
    servicio.duracion_estimada = '45 min'
    from app import db
    db.session.commit()

    login_as(client, admin_user)
    resp = client.post('/admin/citas', data=_form_data(barbero, servicio, '10:00'))
    assert resp.status_code in (200, 302)

    cita = Cita.query.one()
    assert cita.duracion == 45


def test_crear_cita_admin_rechaza_solapamiento_por_duracion(client, admin_user, barbero, servicio):
    """Reproduce el caso reportado: una cita a las 10:00 (30 min) debe bloquear una
    segunda a las 10:15 para el mismo barbero, aunque la hora de inicio sea distinta."""
    login_as(client, admin_user)

    primero = client.post('/admin/citas', data=_form_data(barbero, servicio, '10:00', email='a@test.com'))
    assert primero.status_code in (200, 302)
    assert Cita.query.count() == 1

    segundo = client.post('/admin/citas', data=_form_data(barbero, servicio, '10:15', email='b@test.com'))
    assert segundo.status_code == 200  # se re-renderiza el formulario, no se redirige
    assert Cita.query.count() == 1  # la segunda cita NO se creó


def test_editar_cita_admin_rechaza_solapamiento_con_otra_cita(client, admin_user, barbero, servicio):
    login_as(client, admin_user)

    client.post('/admin/citas', data=_form_data(barbero, servicio, '10:00', email='a@test.com'))
    client.post('/admin/citas', data=_form_data(barbero, servicio, '11:00', email='b@test.com'))
    assert Cita.query.count() == 2

    cita_b = [c for c in Cita.query.all() if c.fecha.hour == 11][0]

    resp = client.post(
        f'/admin/citas/editar/{cita_b.id}',
        data=_form_data(barbero, servicio, '10:15', email='b@test.com'),
    )
    assert resp.status_code == 200  # re-renderiza, no redirige

    cita_b_recargada = Cita.query.get(cita_b.id)
    assert cita_b_recargada.fecha.hour == 11  # no se movió


def test_editar_cita_admin_permite_guardar_sin_cambiar_su_propio_horario(client, admin_user, barbero, servicio):
    """excluir_cita_id debe evitar que una cita se marque como solapada contra sí misma."""
    login_as(client, admin_user)

    client.post('/admin/citas', data=_form_data(barbero, servicio, '10:00', email='a@test.com'))
    cita = Cita.query.one()

    resp = client.post(
        f'/admin/citas/editar/{cita.id}',
        data=_form_data(barbero, servicio, '10:00', email='a@test.com', estado='confirmada'),
    )
    assert resp.status_code == 302  # esta vez sí redirige: no hay conflicto

    cita_recargada = Cita.query.get(cita.id)
    assert cita_recargada.estado == 'confirmada'
