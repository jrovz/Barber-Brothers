from app import db
from app.models.negocio import Negocio
from app.admin.routes.negocio import horario_desde_dias, horario_por_dia
from tests.conftest import login_as


def _datos(**extra):
    datos = {
        'telefono': '3001112233',
        'whatsapp': '573001112233',
        'email_contacto': 'hola@ejemplo.com',
        'ciudad': 'Medellín',
    }
    datos.update(extra)
    return datos


def test_admin_ve_el_formulario(client, admin_user):
    login_as(client, admin_user)
    resp = client.get('/admin/negocio')
    assert resp.status_code == 200
    assert 'name="whatsapp"' in resp.get_data(as_text=True)


def test_admin_cambia_telefono_y_se_ve_en_el_sitio(client, admin_user):
    login_as(client, admin_user)
    resp = client.post('/admin/negocio', data=_datos(), follow_redirects=True)
    assert resp.status_code == 200

    home = client.get('/').get_data(as_text=True)
    assert 'Tel: +57 3001112233' in home
    assert 'https://wa.me/573001112233' in home
    assert '3001112233' in client.get('/contacto').get_data(as_text=True)


def test_whatsapp_invalido_no_se_guarda(client, admin_user, negocio):
    login_as(client, admin_user)
    client.post('/admin/negocio', data=_datos(whatsapp='3001112233'))
    db.session.refresh(negocio)
    assert negocio.whatsapp == '573000000000'
    assert negocio.telefono == '3000000000'


def test_url_de_red_invalida_no_se_guarda(client, admin_user, negocio):
    login_as(client, admin_user)
    client.post('/admin/negocio', data=_datos(instagram_url='no-es-una-url'))
    db.session.refresh(negocio)
    assert negocio.instagram_url is None


def test_no_se_pueden_editar_campos_reservados(client, admin_user, negocio):
    login_as(client, admin_user)
    client.post('/admin/negocio', data=_datos(slug='otro', dominio='otro.com', plan='premium', activo=''))
    db.session.refresh(negocio)
    assert negocio.slug == 'barberbrothers'
    assert negocio.dominio is None
    assert negocio.plan == 'basico'
    assert negocio.activo is True


def test_horario_se_guarda_agrupado_y_valida_formato(client, admin_user, negocio):
    login_as(client, admin_user)
    datos = _datos()
    for dia in ('Monday', 'Tuesday', 'Wednesday'):
        datos[f'h_{dia}_abre'] = '08:00'
        datos[f'h_{dia}_cierra'] = '18:00'
    datos['h_Saturday_abre'] = '09:00'
    datos['h_Saturday_cierra'] = '14:00'
    client.post('/admin/negocio', data=datos)
    db.session.refresh(negocio)
    assert negocio.horario_atencion == [
        {'dias': ['Monday', 'Tuesday', 'Wednesday'], 'abre': '08:00', 'cierra': '18:00'},
        {'dias': ['Saturday'], 'abre': '09:00', 'cierra': '14:00'},
    ]

    malo = _datos(telefono='3009998877')
    malo['h_Monday_abre'] = '18:00'
    malo['h_Monday_cierra'] = '08:00'
    client.post('/admin/negocio', data=malo)
    db.session.refresh(negocio)
    assert negocio.telefono == '3001112233'


def test_horario_ida_y_vuelta():
    horario = [{'dias': ['Monday', 'Tuesday'], 'abre': '08:00', 'cierra': '12:00'},
               {'dias': ['Friday'], 'abre': '08:00', 'cierra': '12:00'}]
    assert horario_desde_dias(horario_por_dia(horario)) == horario


def test_barbero_y_cliente_reciben_403(client, cliente_user):
    login_as(client, cliente_user)
    assert client.get('/admin/negocio').status_code == 403
    assert client.post('/admin/negocio', data=_datos()).status_code == 403
