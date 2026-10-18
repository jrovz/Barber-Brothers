import pytest

from app import confiar_en_proxy, limiter


@pytest.fixture
def ruta_limitada(app):
    """Ruta de prueba con límite de 2 por minuto, registrada solo para este test."""
    @app.route('/_prueba_limite')
    @limiter.limit('2 per minute')
    def _prueba_limite():
        return 'ok'

    yield '/_prueba_limite'
    limiter.reset()


def test_no_hay_limites_globales(app, client):
    """El limitador se instala sin afectar a ninguna ruta existente."""
    for _ in range(30):
        assert client.get('/robots.txt').status_code == 200


def test_ruta_limitada_responde_429_al_pasarse(client, ruta_limitada):
    assert client.get(ruta_limitada).status_code == 200
    assert client.get(ruta_limitada).status_code == 200
    assert client.get(ruta_limitada).status_code == 429


def test_el_limite_es_por_ip(client, ruta_limitada):
    uno = {'REMOTE_ADDR': '10.0.0.1'}
    otro = {'REMOTE_ADDR': '10.0.0.2'}
    client.get(ruta_limitada, environ_base=uno)
    client.get(ruta_limitada, environ_base=uno)
    assert client.get(ruta_limitada, environ_base=uno).status_code == 429
    assert client.get(ruta_limitada, environ_base=otro).status_code == 200


def test_la_configuracion_por_defecto_usa_memoria(app):
    assert app.config['RATELIMIT_STORAGE_URI'] == 'memory://'


def test_confiar_en_proxy_toma_la_ip_de_x_forwarded_for(app, ruta_limitada):
    confiar_en_proxy(app)
    client = app.test_client()
    # Dos visitantes distintos detrás del mismo proxy (127.0.0.1) no deben compartir contador.
    a = {'REMOTE_ADDR': '127.0.0.1', 'HTTP_X_FORWARDED_FOR': '203.0.113.7'}
    b = {'REMOTE_ADDR': '127.0.0.1', 'HTTP_X_FORWARDED_FOR': '203.0.113.8'}
    client.get(ruta_limitada, environ_base=a)
    client.get(ruta_limitada, environ_base=a)
    assert client.get(ruta_limitada, environ_base=a).status_code == 429
    assert client.get(ruta_limitada, environ_base=b).status_code == 200


def test_sin_proxy_x_forwarded_for_se_ignora(app, ruta_limitada):
    """En desarrollo y tests la cabecera no se toma en cuenta: cualquiera podría falsearla."""
    client = app.test_client()
    for i in range(3):
        resp = client.get(ruta_limitada, environ_base={'REMOTE_ADDR': '127.0.0.1',
                                                       'HTTP_X_FORWARDED_FOR': f'198.51.100.{i}'})
    assert resp.status_code == 429
