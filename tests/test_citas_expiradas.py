"""Cita.limpiar_citas_expiradas no debe llenar el log ni exponer datos de clientes.

Antes escribía una línea con el correo de cada cita pendiente en cada consulta de
disponibilidad: con ~3 500 pendientes eran ~7 000 líneas por visita y un log de 21 GB.
"""
import logging
from datetime import datetime, timedelta

import pytest
from sqlalchemy import event

from app import db
from app.models.cliente import Cita, Cliente
from tests.conftest import fecha_futura

CORREO = 'cliente.privado@ejemplo.com'


def _crear_citas(barbero, servicio, n, estado='pendiente_confirmacion', hace=timedelta(hours=3)):
    cliente = Cliente.query.filter_by(email=CORREO).first()
    if not cliente:
        cliente = Cliente(nombre='Cliente Privado', email=CORREO, telefono='3000000000')
        db.session.add(cliente)
        db.session.flush()
    base = datetime.fromisoformat(f'{fecha_futura()}T08:00:00')
    for i in range(n):
        db.session.add(Cita(
            cliente_id=cliente.id, barbero_id=barbero.id, servicio_id=servicio.id,
            fecha=base + timedelta(minutes=30 * i), estado=estado, duracion=30,
            creado=datetime.utcnow() - hace,
        ))
    db.session.commit()


def test_cuenta_las_pendientes_con_mas_de_una_hora(app, barbero, servicio):
    _crear_citas(barbero, servicio, 3)
    assert Cita.limpiar_citas_expiradas() == 3


def test_no_cuenta_las_recientes_ni_otros_estados(app, barbero, servicio):
    _crear_citas(barbero, servicio, 2, hace=timedelta(minutes=10))     # aún dentro de la hora
    _crear_citas(barbero, servicio, 2, estado='confirmada')
    _crear_citas(barbero, servicio, 2, estado='cancelada')
    assert Cita.limpiar_citas_expiradas() == 0


def test_no_cambia_el_estado_de_las_citas(app, barbero, servicio):
    """Siguen pendientes y ocupando horario: así está definido el negocio."""
    _crear_citas(barbero, servicio, 2)
    Cita.limpiar_citas_expiradas()
    assert Cita.query.filter_by(estado='pendiente_confirmacion').count() == 2


def test_sin_citas_devuelve_cero(app):
    assert Cita.limpiar_citas_expiradas() == 0


def test_no_escribe_datos_del_cliente_en_los_logs(app, barbero, servicio, caplog):
    _crear_citas(barbero, servicio, 5)
    with caplog.at_level(logging.DEBUG):
        Cita.limpiar_citas_expiradas()
    texto = caplog.text
    assert CORREO not in texto
    assert 'Cliente Privado' not in texto
    assert '3000000000' not in texto


@pytest.mark.parametrize('cantidad', [1, 5, 50])
def test_el_log_no_crece_con_el_numero_de_citas(app, barbero, servicio, caplog, cantidad):
    _crear_citas(barbero, servicio, cantidad)
    with caplog.at_level(logging.DEBUG):
        Cita.limpiar_citas_expiradas()
    lineas = [r for r in caplog.records if r.name == 'app']
    assert len(lineas) <= 1


def test_hace_una_sola_consulta_sin_importar_cuantas_citas_haya(app, barbero, servicio):
    _crear_citas(barbero, servicio, 40)
    db.session.expire_all()
    sentencias = []

    def contar(conn, cursor, statement, *args):
        sentencias.append(statement)

    event.listen(db.engine, 'before_cursor_execute', contar)
    try:
        assert Cita.limpiar_citas_expiradas() == 40
    finally:
        event.remove(db.engine, 'before_cursor_execute', contar)
    assert len(sentencias) == 1, sentencias
