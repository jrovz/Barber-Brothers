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
