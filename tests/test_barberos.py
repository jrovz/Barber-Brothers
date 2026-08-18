from tests.conftest import login_as
from app.models.barbero import Barbero


def test_eliminar_barbero(client, admin_user, barbero):
    login_as(client, admin_user)
    resp = client.post(f'/admin/barberos/eliminar/{barbero.id}', follow_redirects=True)
    assert resp.status_code == 200
    assert Barbero.query.get(barbero.id) is None
