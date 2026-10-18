from datetime import date, datetime, time, timedelta

import pytest

from app import db
from app.models.barbero import BloqueoHorario, crear_disponibilidad_predeterminada
from app.services import disponibilidad
from app.services.disponibilidad import horarios_libres
from tests.test_reservas_caracterizacion import _dia_habil


@pytest.fixture
def barbero_con_horario(barbero):
    crear_disponibilidad_predeterminada(barbero.id)
    return barbero


def _reloj(monkeypatch, momento):
    monkeypatch.setattr(disponibilidad, 'ahora_negocio', lambda: momento)


def test_devuelve_horas_libres_en_orden(app, barbero_con_horario, servicio):
    r = horarios_libres(barbero_con_horario, _dia_habil(), servicio.id)
    assert r.horarios[0] == '08:00'
    assert r.horarios == sorted(r.horarios)
    assert r.duracion_servicio == 30
    assert r.barbero_nombre == barbero_con_horario.nombre
    assert r.mensaje.startswith('Horarios disponibles para')


def test_duracion_viene_del_servicio(app, barbero_con_horario, servicio):
    servicio.duracion_estimada = '1 hora'
    db.session.commit()
    r = horarios_libres(barbero_con_horario, _dia_habil(), servicio.id)
    assert r.duracion_servicio == 60
    assert '11:15' not in r.horarios  # una hora desde las 11:15 pasaría de las 12:00


def test_servicio_inexistente_o_ausente_usa_30_minutos(app, barbero_con_horario):
    assert horarios_libres(barbero_con_horario, _dia_habil()).duracion_servicio == 30
    assert horarios_libres(barbero_con_horario, _dia_habil(), 9999).duracion_servicio == 30


def test_bloqueo_horario_se_respeta(app, barbero_con_horario, servicio):
    dia = _dia_habil()
    db.session.add(BloqueoHorario(barbero_id=barbero_con_horario.id, fecha=dia,
                                  hora_inicio=time(9, 0), hora_fin=time(10, 0)))
    db.session.commit()
    horas = horarios_libres(barbero_con_horario, dia, servicio.id).horarios
    assert '09:00' not in horas and '09:45' not in horas
    assert '10:00' in horas


def test_domingo_sin_horario_configurado(app, barbero_con_horario, servicio):
    d = _dia_habil()
    while d.weekday() != 6:
        d += timedelta(days=1)
    r = horarios_libres(barbero_con_horario, d, servicio.id)
    assert r.horarios == []
    assert r.mensaje == f'{barbero_con_horario.nombre} no tiene horario configurado para este día.'


def test_etiqueta_de_fecha_en_el_mensaje(app, barbero_con_horario, servicio):
    servicio.duracion_estimada = '9 horas'
    db.session.commit()
    r = horarios_libres(barbero_con_horario, _dia_habil(), servicio.id, etiqueta_fecha='la-fecha-pedida')
    assert 'el la-fecha-pedida con duración de 540 min' in r.mensaje


# ----------------------------------------------------------- excluir_pasadas

def test_por_defecto_no_excluye_horas_pasadas(app, barbero_con_horario, servicio, monkeypatch):
    dia = _dia_habil()
    _reloj(monkeypatch, datetime.combine(dia, time(15, 0)))
    assert '08:00' in horarios_libres(barbero_con_horario, dia, servicio.id).horarios


def test_excluir_pasadas_descarta_lo_anterior_a_ahora(app, barbero_con_horario, servicio, monkeypatch):
    dia = _dia_habil()
    _reloj(monkeypatch, datetime.combine(dia, time(15, 10)))
    horas = horarios_libres(barbero_con_horario, dia, servicio.id, excluir_pasadas=True).horarios
    assert horas and all(h >= '15:10' for h in horas)
    assert '15:15' in horas and '15:00' not in horas and '08:00' not in horas


def test_excluir_pasadas_incluye_una_hora_exacta_ahora(app, barbero_con_horario, servicio, monkeypatch):
    dia = _dia_habil()
    _reloj(monkeypatch, datetime.combine(dia, time(15, 0)))
    assert '15:00' in horarios_libres(barbero_con_horario, dia, servicio.id, excluir_pasadas=True).horarios


def test_excluir_pasadas_con_fecha_anterior_a_hoy_no_deja_nada(app, barbero_con_horario, servicio, monkeypatch):
    dia = _dia_habil()
    _reloj(monkeypatch, datetime.combine(dia + timedelta(days=1), time(9, 0)))
    r = horarios_libres(barbero_con_horario, dia, servicio.id, excluir_pasadas=True)
    assert r.horarios == []
    assert r.mensaje.startswith('No hay horarios disponibles')


def test_excluir_pasadas_no_toca_dias_futuros(app, barbero_con_horario, servicio, monkeypatch):
    dia = _dia_habil()
    _reloj(monkeypatch, datetime.combine(dia - timedelta(days=3), time(23, 0)))
    sin = horarios_libres(barbero_con_horario, dia, servicio.id).horarios
    con = horarios_libres(barbero_con_horario, dia, servicio.id, excluir_pasadas=True).horarios
    assert sin == con
