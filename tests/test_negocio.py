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
