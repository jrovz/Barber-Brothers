from flask import render_template_string


def test_negocio_disponible_en_el_contexto_de_las_plantillas(app, negocio):
    """g.negocio se inyecta a todas las plantillas vía el context_processor."""
    with app.test_request_context('/'):
        app.preprocess_request()
        rendered = render_template_string('{{ negocio.nombre }}')
    assert rendered == negocio.nombre


def test_home_responde_200_con_negocio(client):
    resp = client.get('/')
    assert resp.status_code == 200


def test_home_no_se_cae_si_no_existe_el_negocio(client, monkeypatch):
    """Si el slug no coincide con ninguna fila, se usan valores neutros y el sitio no se cae."""
    monkeypatch.setenv('NEGOCIO_SLUG', 'un-negocio-que-no-existe')
    resp = client.get('/')
    assert resp.status_code == 200


def _json_ld(html):
    import json
    import re
    m = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    assert m, 'no se encontró el JSON-LD'
    return json.loads(m.group(1))


def test_home_muestra_datos_del_negocio(client, negocio):
    from app import db
    from app.utils.negocio_actual import limpiar_cache_negocio
    negocio.telefono = '3111111111'
    negocio.whatsapp = '573111111111'
    negocio.ciudad = 'Cali'
    db.session.commit()
    limpiar_cache_negocio()

    html = client.get('/').get_data(as_text=True)
    assert 'https://wa.me/573111111111' in html
    assert 'Tel: +57 3111111111' in html
    assert 'Cali' in html
    assert 'Ibagué' not in html.split('Nuestra historia')[0]


def test_json_ld_omite_horario_y_coordenadas_si_no_existen(client):
    datos = _json_ld(client.get('/').get_data(as_text=True))
    assert datos['name'] == 'Barbería de Prueba'
    assert datos['telephone'] == '+573000000000'
    assert 'openingHoursSpecification' not in datos
    assert 'geo' not in datos
    assert 'sameAs' not in datos


def test_json_ld_incluye_horario_coordenadas_y_redes(client, negocio):
    from app import db
    from app.utils.negocio_actual import limpiar_cache_negocio
    negocio.latitud = 4.5
    negocio.longitud = -75.2
    negocio.instagram_url = 'https://instagram.com/prueba'
    negocio.horario_atencion = [{'dias': ['Monday', 'Tuesday'], 'abre': '08:00', 'cierra': '18:00'}]
    db.session.commit()
    limpiar_cache_negocio()

    datos = _json_ld(client.get('/').get_data(as_text=True))
    assert datos['geo']['latitude'] == 4.5
    assert datos['sameAs'] == ['https://instagram.com/prueba']
    assert datos['openingHoursSpecification'][0]['opens'] == '08:00'


def test_contacto_y_servicios_usan_datos_del_negocio(client):
    contacto = client.get('/contacto').get_data(as_text=True)
    assert '3000000000' in contacto
    assert 'instagram.com' not in contacto
    assert 'Barbería de Prueba' in client.get('/servicios').get_data(as_text=True)


def test_paginas_legales_sin_datos_legales_no_dejan_frases_rotas(client):
    for ruta in ('/terminos', '/privacidad', '/cookies'):
        resp = client.get(ruta)
        assert resp.status_code == 200, ruta
        html = resp.get_data(as_text=True)
        assert 'Barbería de Prueba' in html
        assert 'barberbrothers.com' not in html
        assert 'NIT' not in html
        assert 'None' not in html


def test_paginas_legales_usan_datos_legales_del_negocio(client, negocio):
    from app import db
    from app.utils.negocio_actual import limpiar_cache_negocio
    negocio.razon_social = 'Prueba S.A.S.'
    negocio.nit = '900.123.456-7'
    negocio.direccion_legal = 'Calle Falsa 123'
    negocio.email_contacto = 'contacto@prueba.com'
    negocio.email_datos_personales = 'datos@prueba.com'
    negocio.ciudad = 'Cali'
    db.session.commit()
    limpiar_cache_negocio()

    terminos = client.get('/terminos').get_data(as_text=True)
    assert 'Prueba S.A.S.' in terminos and '900.123.456-7' in terminos
    assert 'Calle Falsa 123' in terminos and 'contacto@prueba.com' in terminos
    assert 'tribunales de Cali' in terminos

    privacidad = client.get('/privacidad').get_data(as_text=True)
    assert 'datos@prueba.com' in privacidad
    assert 'responsable del tratamiento' in privacidad
    assert 'encargada del tratamiento' in privacidad

    assert 'contacto@prueba.com' in client.get('/cookies').get_data(as_text=True)


def test_contacto_muestra_el_horario_de_la_base(client, negocio):
    from app import db
    from app.utils.negocio_actual import limpiar_cache_negocio
    negocio.horario_atencion = [
        {'dias': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'], 'abre': '08:00', 'cierra': '18:00'},
        {'dias': ['Saturday'], 'abre': '08:00', 'cierra': '16:00'},
    ]
    db.session.commit()
    limpiar_cache_negocio()

    html = client.get('/contacto').get_data(as_text=True)
    assert 'Lunes a Viernes: 08:00 - 18:00' in html
    assert 'Sábados: 08:00 - 16:00' in html
    assert 'Domingos: Cerrado' in html


def test_contacto_sin_horario_no_muestra_dias_cerrados(client):
    html = client.get('/contacto').get_data(as_text=True)
    assert 'Cerrado' not in html


def test_correo_de_confirmacion_usa_el_nombre_del_negocio(app, client, barbero, servicio, negocio, monkeypatch):
    from app import db, mail
    from app.utils.negocio_actual import limpiar_cache_negocio
    from tests.conftest import fecha_futura

    class HiloSincrono:
        def __init__(self, target, args=()):
            self._target, self._args = target, args

        def start(self):
            self._target(*self._args)

    monkeypatch.setattr('app.models.email.Thread', HiloSincrono)
    negocio.remitente_nombre = 'Reservas de Prueba'
    db.session.commit()
    limpiar_cache_negocio()

    with mail.record_messages() as enviados:
        resp = client.post('/api/agendar-cita', json={
            'barbero_id': barbero.id, 'servicio_id': servicio.id, 'fecha': fecha_futura(),
            'hora': '10:00', 'nombre': 'Cliente', 'email': 'cliente@test.com', 'telefono': '3000000000',
        })
        assert resp.status_code == 200
        assert len(enviados) == 1
        correo = enviados[0]
        assert correo.subject == 'Confirma tu cita en Barbería de Prueba'
        assert 'Barbería de Prueba' in correo.html and 'Barbería de Prueba' in correo.body
        assert 'Barber Brothers' not in correo.html + correo.body
        assert correo.sender[0] == 'Reservas de Prueba' if isinstance(correo.sender, tuple) else 'Reservas de Prueba' in correo.sender


def test_login_de_barberos_muestra_el_nombre_del_negocio(client):
    assert 'Barbería de Prueba' in client.get('/barbero/login').get_data(as_text=True)


def test_panel_admin_muestra_el_nombre_del_negocio(client, admin_user):
    from tests.conftest import login_as
    login_as(client, admin_user)
    assert 'Barbería de Prueba Admin' in client.get('/admin/').get_data(as_text=True)


def test_robots_usa_el_host_de_la_peticion(client):
    resp = client.get('/robots.txt', base_url='http://otra-barberia.test')
    texto = resp.get_data(as_text=True)
    assert resp.status_code == 200
    assert 'Sitemap: http://otra-barberia.test/sitemap.xml' in texto
    assert 'labarberbrothers' not in texto


def test_sitemap_usa_el_host_de_la_peticion(client):
    resp = client.get('/sitemap.xml', base_url='http://otra-barberia.test')
    texto = resp.get_data(as_text=True)
    assert resp.status_code == 200
    assert '<loc>http://otra-barberia.test' in texto
    assert 'labarberbrothers' not in texto


def test_verificacion_de_google_sale_del_negocio(client, negocio):
    from app import db
    from app.utils.negocio_actual import limpiar_cache_negocio

    assert client.get('/google17b126f9a1dae6ef.html').status_code == 404

    negocio.google_verificacion = 'googleabc123.html'
    db.session.commit()
    limpiar_cache_negocio()

    ok = client.get('/googleabc123.html')
    assert ok.status_code == 200
    assert ok.get_data(as_text=True) == 'google-site-verification: googleabc123.html'
    assert client.get('/googleotro.html').status_code == 404


def test_colores_del_negocio_se_aplican_como_variables_css(client, negocio):
    from app import db
    from app.utils.negocio_actual import limpiar_cache_negocio
    negocio.color_primario = '#112233'
    negocio.color_secundario = '#445566'
    negocio.color_acento = '#778899'
    db.session.commit()
    limpiar_cache_negocio()

    html = client.get('/').get_data(as_text=True)
    assert '--color-bg-main: #112233;' in html
    assert '--color-border: #445566;' in html
    assert '--color-accent: #778899;' in html
    assert 'color-mix(in srgb, #778899 80%, white)' in html


def test_color_invalido_no_llega_al_css(client, negocio):
    from app import db
    from app.utils.negocio_actual import limpiar_cache_negocio
    negocio.color_primario = 'red;}</style><script>alert(1)</script>'
    db.session.commit()
    limpiar_cache_negocio()

    html = client.get('/').get_data(as_text=True)
    assert 'alert(1)' not in html
    assert '--color-bg-main: red' not in html


def test_logo_y_favicon_del_negocio(client, negocio):
    from app import db
    from app.utils.negocio_actual import limpiar_cache_negocio
    negocio.logo_url = '/static/uploads/negocio/logo-prueba.png'
    negocio.favicon_url = '/static/uploads/negocio/fav-prueba.png'
    db.session.commit()
    limpiar_cache_negocio()

    html = client.get('/').get_data(as_text=True)
    assert 'src="/static/uploads/negocio/logo-prueba.png"' in html
    assert 'content="http://localhost/static/uploads/negocio/logo-prueba.png"' in html
    assert 'rel="icon" href="/static/uploads/negocio/fav-prueba.png"' in html
    assert 'alt="Barbería Clásica"' not in html


def test_sin_logo_usa_el_de_la_plataforma(client):
    html = client.get('/').get_data(as_text=True)
    assert 'src="/static/logo.png' in html
    assert 'alt="Barbería de Prueba"' in html
