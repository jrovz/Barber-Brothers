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


def _desactivar_tienda(negocio):
    from app import db
    from app.utils.negocio_actual import limpiar_cache_negocio
    negocio.tienda_activa = False
    db.session.commit()
    limpiar_cache_negocio()


def test_con_tienda_activa_se_muestran_productos_y_carrito(client):
    assert client.get('/productos').status_code == 200
    html = client.get('/').get_data(as_text=True)
    assert 'href="/productos"' in html
    assert 'id="cart-panel"' in html
    assert 'smart_cart.js' in html
    assert '/productos' in client.get('/sitemap.xml').get_data(as_text=True)


def test_con_tienda_desactivada_las_rutas_dan_404(client, negocio):
    _desactivar_tienda(negocio)
    assert client.get('/productos').status_code == 404
    assert client.get('/tienda').status_code == 404
    assert client.get('/checkout').status_code == 404
    assert client.get('/confirmacion-pedido/1').status_code == 404


def test_con_tienda_desactivada_no_se_ve_en_el_sitio(client, negocio):
    _desactivar_tienda(negocio)
    home = client.get('/').get_data(as_text=True)
    assert 'href="/productos"' not in home
    assert 'cart-button' not in home
    assert 'id="cart-panel"' not in home
    assert 'smart_cart.js' not in home
    assert '/productos' not in client.get('/sitemap.xml').get_data(as_text=True)
    assert client.get('/servicios').status_code == 200


def test_datos_publicos_del_negocio_llegan_al_javascript(client):
    import json
    import re
    html = client.get('/').get_data(as_text=True)
    m = re.search(r'window\.NEGOCIO = (\{.*?\});</script>', html, re.S)
    assert m, 'falta window.NEGOCIO'
    datos = json.loads(m.group(1))
    assert datos['nombre'] == 'Barbería de Prueba'
    assert datos['whatsapp'] == '573000000000'
    assert 'nit' not in datos and 'email_contacto' not in datos


def test_javascript_no_trae_telefonos_fijos():
    import pathlib
    import re
    for js in pathlib.Path('app/static/js').glob('*.js'):
        assert not re.search(r'wa\.me/57\d{10}', js.read_text(encoding='utf-8')), js.name


def test_historia_se_dibuja_por_parrafos_y_la_cita_en_cursiva(client, negocio):
    from app import db
    from app.utils.negocio_actual import limpiar_cache_negocio
    negocio.historia = 'Primer párrafo.\r\n\r\nSegundo párrafo.\r\n\r\n"Una frase final."'
    db.session.commit()
    limpiar_cache_negocio()

    html = client.get('/').get_data(as_text=True)
    assert '<h3>La historia de Barbería de Prueba' in html
    assert '<p>Primer párrafo.</p>' in html
    assert '<p>Segundo párrafo.</p>' in html
    assert '<p><em>"Una frase final."</em></p>' in html or '<p><em>&#34;Una frase final.&#34;</em></p>' in html


def test_sin_historia_no_se_muestra_el_bloque(client):
    assert 'La historia de' not in client.get('/').get_data(as_text=True)


def test_sin_variable_de_entorno_usa_el_primer_negocio_activo(client, monkeypatch):
    monkeypatch.delenv('NEGOCIO_SLUG', raising=False)
    assert 'Barbería de Prueba' in client.get('/').get_data(as_text=True)


def test_barbero_sin_foto_no_muestra_imagen_de_relleno(client, barbero):
    html = client.get('/').get_data(as_text=True)
    assert barbero.nombre in html
    assert 'unsplash.com' not in html


def _etiquetas_tarjeta(html):
    import re
    return re.findall(r'<div class="barbero-card"[^>]*>', html)


def test_un_solo_barbero_muestra_su_tarjeta_de_servicios_desde_el_inicio(client, barbero):
    html = client.get('/').get_data(as_text=True)
    tarjetas = _etiquetas_tarjeta(html)
    assert len(tarjetas) == 1
    assert 'hidden' not in tarjetas[0]
    assert 'id="barbero-placeholder"' not in html
    assert 'Cambiar barbero' not in html


def test_varios_barberos_ocultan_las_tarjetas_hasta_elegir_uno(client, barbero):
    from app import db
    from app.models.barbero import Barbero
    db.session.add(Barbero(nombre='Segundo Barbero', especialidad='Barba', activo=True))
    db.session.commit()

    html = client.get('/').get_data(as_text=True)
    tarjetas = _etiquetas_tarjeta(html)
    assert len(tarjetas) == 2
    assert all('hidden' in t for t in tarjetas)
    assert 'id="barbero-placeholder"' in html
    assert html.count('Cambiar barbero') == 2
    assert 'accordion-chevron' not in html
