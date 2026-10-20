"""Las cookies comerciales las controla el navegador: un valor raro no debe dar nunca un 500.

Antes, get_business_cookie devolvía el texto tal cual si la cookie no era JSON (o era JSON pero
no un diccionario) y todo el código posterior llamaba a .get(...): la página principal daba
'str' object has no attribute 'get' (197 veces entre agosto de 2025 y septiembre de 2026).
"""
import json

import pytest
from flask import make_response
from werkzeug.http import dump_cookie, parse_cookie

from app.utils.business_cookies import BusinessCookieManager as Cookies, ConversionOptimizer
from tests.conftest import fecha_futura

COOKIES = ['client_booking_data', 'favorite_barber_service', 'booking_session_tracker',
           'viewed_products', 'persistent_cart']

# Valores que un navegador (o un bot) puede mandar
_VALORES = [
    'texto', '123', 'null', 'true', '[1,2]', '"cadena"', '{}', '[]', '{', '{"a":',
    '{"usage_count":"x"}', '{"usage_count":null}', '{"steps_completed":"no-lista"}',
    '{"steps_completed":[{"a":1}]}', '{"intent_score":"alto"}', '{"total_bookings":"x"}',
    '{"barbero_stats":"x","servicio_stats":[1],"time_stats":5}', '{"nombre":123,"email":[],"telefono":{}}',
    '{"current_step":{"a":1}}', 'x' * 4000,
]
# ids cortos (uno de los valores mide 4 000 caracteres y ensuciaría el informe de pytest)
HOSTILES = [pytest.param(v, id=f'h{i}') for i, v in enumerate(_VALORES)]


def _cabecera(**cookies):
    return '; '.join(dump_cookie(n, v).split(';')[0] for n, v in cookies.items())


def _en_peticion(app, **cookies):
    return app.test_request_context('/', headers={'Cookie': _cabecera(**cookies)})


# ------------------------------------------------- cookies válidas (no deben cambiar)

CLIENTE = {'nombre': 'Ana', 'email': 'ana@ejemplo.com', 'telefono': '3001234567', 'usage_count': 3}
PREFS = {'favorite_barbero': 2, 'favorite_servicio': 5, 'favorite_time': 'morning', 'total_bookings': 4}
SESION = {'current_step': 'booking_completed', 'intent_score': 80, 'steps_completed': ['a', 'b']}


def test_sin_cookies_los_valores_por_defecto(app):
    with app.test_request_context('/'):
        assert Cookies.get_personalization_data() == {
            'client': {'nombre': '', 'email': '', 'telefono': '', 'is_returning': False},
            'preferences': {'barbero_favorito': None, 'servicio_favorito': None,
                            'horario_favorito': None, 'total_reservas': 0},
            'session': {'current_step': 'initial', 'intent_score': 0, 'steps_completed': []},
        }
        assert Cookies.calculate_conversion_probability() == pytest.approx(0.1)


def test_cookies_validas_dan_los_mismos_datos_de_siempre(app):
    with _en_peticion(app, client_booking_data=json.dumps(CLIENTE), favorite_barber_service=json.dumps(PREFS),
                      booking_session_tracker=json.dumps(SESION)):
        datos = Cookies.get_personalization_data()
        assert datos['client'] == {'nombre': 'Ana', 'email': 'ana@ejemplo.com', 'telefono': '3001234567',
                                   'is_returning': True}
        assert datos['preferences'] == {'barbero_favorito': 2, 'servicio_favorito': 5,
                                        'horario_favorito': 'morning', 'total_reservas': 4}
        assert datos['session'] == {'current_step': 'booking_completed', 'intent_score': 80,
                                    'steps_completed': ['a', 'b']}
        assert Cookies.calculate_conversion_probability() == 1.0


def test_el_seguimiento_de_pasos_conserva_el_progreso_valido(app):
    with _en_peticion(app, booking_session_tracker=json.dumps(SESION)):
        sesion = Cookies.track_booking_abandonment()
        assert sesion['steps_completed'] == ['a', 'b'] and sesion['current_step'] == 'booking_completed'


def _cookie_escrita(respuesta, nombre):
    cabecera = next(h for h in respuesta.headers.getlist('Set-Cookie') if h.startswith(nombre + '='))
    return json.loads(parse_cookie(cabecera.split(';')[0])[nombre])


def test_guardar_preferencias_acumula_como_siempre(app):
    previas = {'barbero_stats': {'2': 1}, 'servicio_stats': {'5': 1}, 'time_stats': {'morning': 1},
               'favorite_barbero': None, 'total_bookings': 1}
    with _en_peticion(app, favorite_barber_service=json.dumps(previas)):
        guardado = _cookie_escrita(Cookies.save_preferences_smart(make_response('ok'), 2, 5, '10:00'),
                                   'favorite_barber_service')
    assert guardado['favorite_barbero'] == 2 and guardado['favorite_servicio'] == 5
    assert guardado['favorite_time'] == 'morning'
    assert guardado['barbero_stats'] == {'2': 2} and guardado['servicio_stats'] == {'5': 2}
    assert guardado['time_stats'] == {'morning': 2}
    assert guardado['total_bookings'] == 2
    assert guardado['last_booking']['barbero_id'] == 2 and guardado['last_booking']['hora'] == '10:00'


def test_guardar_datos_del_cliente_cuenta_los_usos_como_siempre(app):
    with _en_peticion(app, client_booking_data=json.dumps(CLIENTE)):
        guardado = _cookie_escrita(Cookies.save_client_data_smart(
            make_response('ok'), {'nombre': ' Ana ', 'telefono': '300', 'email': 'ANA@Ejemplo.com'}),
            'client_booking_data')
    assert guardado['nombre'] == 'Ana' and guardado['email'] == 'ana@ejemplo.com'
    assert guardado['usage_count'] == 4


# --------------------------------------------------- cookies hostiles, a nivel de función

@pytest.mark.parametrize('nombre', COOKIES)
@pytest.mark.parametrize('valor', HOSTILES)
def test_las_funciones_toleran_cualquier_valor(app, nombre, valor):
    with _en_peticion(app, **{nombre: valor}):
        Cookies.get_personalization_data()
        Cookies.track_booking_abandonment()
        assert 0.0 <= Cookies.calculate_conversion_probability() <= 1.0
        ConversionOptimizer.get_smart_recommendations()
        ConversionOptimizer.should_show_exit_intent_popup()


@pytest.mark.parametrize('valor', HOSTILES)
def test_get_business_cookie_con_defecto_dict_siempre_devuelve_dict(app, valor):
    with _en_peticion(app, client_booking_data=valor):
        assert isinstance(Cookies.get_business_cookie('client_booking_data', {}), dict)
    with _en_peticion(app, viewed_products=valor):
        assert isinstance(Cookies.get_business_cookie('viewed_products', []), list) or valor in ('[1,2]', '[]')


def test_get_business_cookie_sin_defecto_no_cambia(app):
    """Las llamadas sin valor por defecto conservan su comportamiento (devuelven lo leído)."""
    with _en_peticion(app, client_booking_data='texto'):
        assert Cookies.get_business_cookie('client_booking_data') == 'texto'
    with _en_peticion(app, client_booking_data=json.dumps(CLIENTE)):
        assert Cookies.get_business_cookie('client_booking_data') == CLIENTE


# ------------------------------------------------ cookies hostiles, a nivel de página

RUTAS = ['/', '/servicios', '/productos', '/contacto', '/checkout']


@pytest.mark.parametrize('ruta', RUTAS)
@pytest.mark.parametrize('nombre', COOKIES)
@pytest.mark.parametrize('valor', HOSTILES)
def test_ninguna_pagina_publica_da_500(client, ruta, nombre, valor):
    client.set_cookie(nombre, valor)
    assert client.get(ruta).status_code < 500


@pytest.mark.parametrize('nombre', ['client_booking_data', 'favorite_barber_service', 'booking_session_tracker'])
@pytest.mark.parametrize('valor', HOSTILES)
def test_una_reserva_exitosa_no_se_estropea_por_una_cookie_rara(client, barbero, servicio, monkeypatch, nombre, valor):
    """Si la cookie rompía el final de la reserva, el cliente veía un error aunque la cita ya
    estuviera guardada."""
    monkeypatch.setattr('app.models.email.send_email', lambda **kw: None)
    client.set_cookie(nombre, valor)
    resp = client.post('/api/agendar-cita', json={
        'barbero_id': barbero.id, 'servicio_id': servicio.id, 'fecha': fecha_futura(), 'hora': '10:00',
        'nombre': 'Cliente', 'email': 'c@ejemplo.com', 'telefono': '3000000000'})
    assert resp.status_code == 200
    assert resp.get_json()['success'] is True
