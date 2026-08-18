from tests.conftest import login_as


def test_admin_login_valid_credentials(client, admin_user):
    resp = client.post('/admin/login', data={
        'username': admin_user.username,
        'password': 'adminpass123',
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert 'login' not in resp.request.path


def test_admin_login_invalid_password(client, admin_user):
    resp = client.post('/admin/login', data={
        'username': admin_user.username,
        'password': 'wrong-password',
    }, follow_redirects=True)
    assert resp.request.path == '/admin/login'


def test_admin_login_rejects_non_admin_role(client, cliente_user):
    """La vista de login de admin no debe autenticar a un usuario con rol 'cliente'."""
    resp = client.post('/admin/login', data={
        'username': cliente_user.username,
        'password': 'clientepass123',
    }, follow_redirects=True)
    assert resp.request.path != '/admin/'
    with client.session_transaction() as sess:
        assert '_user_id' not in sess


def test_admin_dashboard_requires_login(client):
    resp = client.get('/admin/', follow_redirects=False)
    assert resp.status_code in (302, 401, 403)


def test_admin_dashboard_accessible_to_admin(client, admin_user):
    login_as(client, admin_user)
    resp = client.get('/admin/')
    assert resp.status_code == 200


def test_all_admin_routes_reject_non_admin(app, client, cliente_user):
    """Todas las rutas /admin/* (menos login/logout) deben devolver 403 a un
    usuario autenticado que no sea administrador, sin importar el método."""
    login_as(client, cliente_user)

    rules = [r for r in app.url_map.iter_rules() if r.endpoint.startswith('admin.')
             and r.endpoint not in ('admin.login', 'admin.logout')]

    failures = []
    for rule in rules:
        values = {arg: 1 for arg in rule.arguments}
        try:
            with app.test_request_context():
                url = app.url_map.bind('localhost').build(rule.endpoint, values=values)
        except Exception as e:
            failures.append(f"{rule.endpoint}: no se pudo construir la URL ({e})")
            continue

        methods = rule.methods - {'OPTIONS', 'HEAD'}
        method = 'POST' if 'POST' in methods and 'GET' not in methods else 'GET'
        resp = client.open(url, method=method)
        if resp.status_code != 403:
            failures.append(f"{rule.endpoint} [{method} {url}] -> {resp.status_code} (esperado 403)")

    assert not failures, "Rutas admin accesibles sin ser administrador:\n" + "\n".join(failures)


def test_admin_routes_not_blocked_for_admin(app, client, admin_user):
    """El decorador admin_required no debe bloquear a un administrador legítimo
    (spot-check sobre las rutas GET más importantes)."""
    login_as(client, admin_user)
    for path in ('/admin/', '/admin/productos', '/admin/categorias', '/admin/barberos',
                 '/admin/servicios', '/admin/citas', '/admin/clientes', '/admin/sliders'):
        resp = client.get(path)
        assert resp.status_code != 403, f"{path} devolvió 403 para un admin autenticado"
