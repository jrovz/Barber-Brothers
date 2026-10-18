from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from app.utils.tiempo import ahora_negocio


def _utc_naive():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _cerca(a, b, segundos=5):
    return abs(a - b) < timedelta(seconds=segundos)


def test_bogota_equivale_a_utc_menos_5():
    """Es lo que hacía agendar_cita a mano: Colombia no tiene horario de verano."""
    ahora = ahora_negocio(SimpleNamespace(zona_horaria='America/Bogota'))
    assert _cerca(ahora, _utc_naive() - timedelta(hours=5))
    assert ahora.tzinfo is None


def test_usa_la_zona_del_negocio():
    ahora = ahora_negocio(SimpleNamespace(zona_horaria='Asia/Tokyo'))
    assert _cerca(ahora, _utc_naive() + timedelta(hours=9))


def test_zona_invalida_cae_en_bogota():
    ahora = ahora_negocio(SimpleNamespace(zona_horaria='No/Existe'))
    assert _cerca(ahora, _utc_naive() - timedelta(hours=5))


def test_zona_vacia_o_ausente_cae_en_bogota():
    assert _cerca(ahora_negocio(SimpleNamespace(zona_horaria=None)), _utc_naive() - timedelta(hours=5))
    assert _cerca(ahora_negocio(SimpleNamespace()), _utc_naive() - timedelta(hours=5))


def test_sin_argumento_usa_el_negocio_actual(app, negocio):
    negocio.zona_horaria = 'America/Bogota'
    assert _cerca(ahora_negocio(), _utc_naive() - timedelta(hours=5))
