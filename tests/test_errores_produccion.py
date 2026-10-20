"""Errores 500 de producción: /about, sesión rota tras un fallo de la base y 503 con reintento.

Contexto: 313 fallos de conexión a PostgreSQL en 16 meses (15 reservas que no se pudieron enviar),
/about daba 500 en 78 de 78 peticiones y la sesión quedaba inutilizable tras una consulta fallida.
"""
import logging
from datetime import date, timedelta

import pytest
from sqlalchemy.exc import InterfaceError, OperationalError

from app import db
from app.models.barbero import BloqueoHorario, crear_disponibilidad_predeterminada
from app.models.cliente import Cita, Cliente
from tests.conftest import fecha_futura

SSL_EOF = 'SSL SYSCALL error: EOF detected'


def _bd_caida(sql='SELECT secreto FROM cliente WHERE email = %(e)s'):
    """Un error como el de producción; el SQL y los parámetros llevan datos personales a propósito."""
    return OperationalError(sql, {'e': 'cliente.privado@ejemplo.com'}, Exception(SSL_EOF))


def _payload(barbero, servicio, **extra):
    datos = {'barbero_id': barbero.id, 'servicio_id': servicio.id, 'fecha': fecha_futura(), 'hora': '10:00',
             'nombre': 'Cliente', 'email': 'c@ejemplo.com', 'telefono': '3000000000'}
    datos.update(extra)
    return datos


# --------------------------------------------------------------------------- /about

def test_about_redirige_a_la_seccion_de_la_home(client):
    resp = client.get('/about')
    assert resp.status_code == 301
    assert resp.headers['Location'].endswith('/#about-section')


def test_la_home_tiene_la_seccion_a_la_que_apunta_la_redireccion(client):
    assert 'id="about-section"' in client.get('/').get_data(as_text=True)


# ------------------------------------------------------- 503: rutas HTML y rutas JSON

@pytest.fixture
def rutas_de_prueba(app):
    @app.route('/_bd_caida')
    def _bd_caida_html():
        raise _bd_caida()

    @app.route('/api/_bd_caida')
    def _bd_caida_api():
        raise InterfaceError('SELECT 1', {}, Exception('connection already closed'))


def test_pagina_html_con_bd_caida_da_503_amable(client, rutas_de_prueba):
    resp = client.get('/_bd_caida')
    assert resp.status_code == 503
    assert resp.headers['Retry-After'] == '2'
    cuerpo = resp.get_data(as_text=True)
    assert 'Reintentar' in cuerpo and 'inténtalo de nuevo' in cuerpo


def test_ruta_api_con_bd_caida_da_503_json_con_reintentar(client, rutas_de_prueba):
    resp = client.get('/api/_bd_caida')
    assert resp.status_code == 503
    assert resp.headers['Retry-After'] == '2'
    assert resp.get_json()['reintentar'] is True


def test_el_log_no_contiene_sql_ni_datos_personales(client, rutas_de_prueba, caplog):
    with caplog.at_level(logging.DEBUG):
        client.get('/_bd_caida')
    assert 'Base de datos no disponible' in caplog.text and SSL_EOF in caplog.text
    assert 'cliente.privado@ejemplo.com' not in caplog.text
    assert 'SELECT secreto' not in caplog.text


def test_otros_errores_siguen_siendo_500(app, client):
    @app.route('/_otro_error')
    def _otro():
        raise RuntimeError('fallo cualquiera')
    app.config['PROPAGATE_EXCEPTIONS'] = False
    assert client.get('/_otro_error').status_code == 500


# --------------------------------------------- 503 en el envío de la reserva (POST)

def test_fallo_de_bd_ANTES_de_guardar_pide_reintentar_y_no_guarda_nada(client, barbero, servicio, monkeypatch):
    def romper(*a, **k):
        raise _bd_caida()
    monkeypatch.setattr('app.utils.pricing.obtener_precio_servicio', romper)   # ocurre antes del commit

    resp = client.post('/api/agendar-cita', json=_payload(barbero, servicio))
    assert resp.status_code == 503
    assert resp.get_json()['reintentar'] is True
    assert Cita.query.count() == 0


def test_fallo_de_bd_AL_guardar_no_pide_reintentar_y_avisa_de_revisar_el_correo(client, barbero, servicio, monkeypatch):
    def romper_commit():
        raise _bd_caida()
    monkeypatch.setattr(db.session, 'commit', romper_commit)

    resp = client.post('/api/agendar-cita', json=_payload(barbero, servicio))
    assert resp.status_code == 503
    cuerpo = resp.get_json()
    assert cuerpo['reintentar'] is False          # la cita pudo quedar registrada: no repetir solo
    assert 'correo' in cuerpo['error']


def test_el_reintento_tras_un_fallo_previo_funciona(client, barbero, servicio, monkeypatch):
    llamadas = {'n': 0}
    original = __import__('app.utils.pricing', fromlist=['x']).obtener_precio_servicio

    def falla_una_vez(*a, **k):
        llamadas['n'] += 1
        if llamadas['n'] == 1:
            raise _bd_caida()
        return original(*a, **k)
    monkeypatch.setattr('app.utils.pricing.obtener_precio_servicio', falla_una_vez)
    monkeypatch.setattr('app.models.email.send_email', lambda **kw: None)

    assert client.post('/api/agendar-cita', json=_payload(barbero, servicio)).status_code == 503
    segundo = client.post('/api/agendar-cita', json=_payload(barbero, servicio))
    assert segundo.status_code == 200 and Cita.query.count() == 1      # sin duplicados


# ------------------------------------------------ 503 en las consultas (GET)

def test_disponibilidad_con_bd_caida_da_503_con_reintentar(client, barbero, servicio, monkeypatch):
    def romper(self, *a, **k):
        raise _bd_caida()
    monkeypatch.setattr('app.models.barbero.Barbero.obtener_horarios_disponibles', romper)
    dia = date.today() + timedelta(days=30)
    resp = client.get(f'/api/disponibilidad/{barbero.id}/{dia.isoformat()}?servicio_id={servicio.id}')
    assert resp.status_code == 503 and resp.get_json()['reintentar'] is True


def test_servicios_del_barbero_con_bd_caida_da_503(client, barbero, monkeypatch):
    def romper(*a, **k):
        raise _bd_caida()
    monkeypatch.setattr('app.utils.pricing.obtener_servicios_barbero', romper)
    resp = client.get(f'/api/barbero/{barbero.id}/servicios')
    assert resp.status_code == 503 and resp.get_json()['reintentar'] is True


# ----------------------------------------------------- P2: sesión rota tras un fallo

def test_si_falla_la_consulta_de_bloqueos_se_hace_rollback(app, barbero, monkeypatch):
    """En PostgreSQL, tras un error la transacción queda abortada y todo lo siguiente fallaba
    con InFailedSqlTransaction / PendingRollbackError."""
    crear_disponibilidad_predeterminada(barbero.id)

    class ConsultaRota:
        def filter(self, *a, **k):
            raise _bd_caida()
    monkeypatch.setattr(BloqueoHorario, 'query', ConsultaRota(), raising=False)
    llamadas = []
    original = db.session.rollback
    monkeypatch.setattr(db.session, 'rollback', lambda: (llamadas.append(1), original())[1])

    dia = date.today() + timedelta(days=30)
    while dia.weekday() == 6:
        dia += timedelta(days=1)
    horarios = barbero.obtener_horarios_disponibles(dia, 30)

    assert llamadas, 'no se hizo rollback tras el fallo'
    assert horarios                          # y la disponibilidad se devuelve igualmente
