"""Las conexiones a la base no deben heredarse por fork() (ver app.liberar_conexiones).

Con Gunicorn + preload_app=True, una conexión abierta en el proceso maestro la compartían los
workers y producía "SSL error: decryption failed or bad record mac" y "SSL SYSCALL error: EOF
detected" (310 fallos en 16 meses, incluidas reservas que no se pudieron enviar).
"""
import os

import pytest
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

import app as app_pkg
from app import liberar_conexiones
from app.config import ProductionConfig


@pytest.fixture
def app_con_pool(tmp_path):
    """App mínima con SQLite en archivo y el pool normal (QueuePool), para observar el pool."""
    aplicacion = Flask(__name__)
    aplicacion.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{tmp_path / 'pool.db'}"
    ext = SQLAlchemy()
    ext.init_app(aplicacion)
    yield aplicacion, ext
    with aplicacion.app_context():
        ext.engine.dispose()


def _abrir_y_devolver_conexion(aplicacion, ext):
    """Lo que hace init_database_if_needed al arrancar: usa la BD y deja la conexión en el pool."""
    with aplicacion.app_context():
        ext.session.execute(text('select 1'))
        ext.session.remove()


def test_liberar_conexiones_deja_el_pool_vacio(app_con_pool):
    aplicacion, ext = app_con_pool
    _abrir_y_devolver_conexion(aplicacion, ext)
    with aplicacion.app_context():
        assert ext.engine.pool.checkedin() == 1        # el maestro se queda con una conexión

    liberar_conexiones(aplicacion, base=ext)

    with aplicacion.app_context():
        assert ext.engine.pool.checkedin() == 0        # y ya no hay nada que heredar


def test_la_app_sigue_funcionando_tras_liberar_conexiones(app_con_pool):
    aplicacion, ext = app_con_pool
    _abrir_y_devolver_conexion(aplicacion, ext)
    liberar_conexiones(aplicacion, base=ext)
    with aplicacion.app_context():
        assert ext.session.execute(text('select 1')).scalar() == 1   # abre una conexión nueva


@pytest.mark.skipif(not hasattr(os, 'fork'), reason='os.fork solo existe en Linux/macOS (el CI y el servidor)')
def test_un_worker_hijo_no_hereda_conexiones(app_con_pool):
    aplicacion, ext = app_con_pool
    _abrir_y_devolver_conexion(aplicacion, ext)
    liberar_conexiones(aplicacion, base=ext)

    lectura, escritura = os.pipe()
    pid = os.fork()
    if pid == 0:                                       # "worker"
        try:
            with aplicacion.app_context():
                heredadas = ext.engine.pool.checkedin()
                ok = ext.session.execute(text('select 1')).scalar()
            os.write(escritura, f'{heredadas},{ok}'.encode())
        finally:
            os._exit(0)
    os.waitpid(pid, 0)
    heredadas, ok = os.read(lectura, 64).decode().split(',')
    assert (heredadas, ok) == ('0', '1')


def test_produccion_usa_pre_ping_y_recicla_conexiones():
    assert ProductionConfig.SQLALCHEMY_ENGINE_OPTIONS == {'pool_pre_ping': True, 'pool_recycle': 1800}


def test_create_app_en_produccion_libera_las_conexiones(monkeypatch, tmp_path):
    monkeypatch.setenv('DATABASE_URL', f"sqlite:///{tmp_path / 'prod.db'}")
    monkeypatch.setenv('SECRET_KEY', 'clave-de-prueba')
    monkeypatch.setattr(ProductionConfig, 'SQLALCHEMY_DATABASE_URI', f"sqlite:///{tmp_path / 'prod.db'}")
    llamadas = []
    monkeypatch.setattr(app_pkg, 'liberar_conexiones', lambda a, base=None: llamadas.append(a))

    aplicacion = app_pkg.create_app('production')

    assert llamadas == [aplicacion]


def test_create_app_en_pruebas_no_libera_las_conexiones(monkeypatch):
    """Los tests usan SQLite en memoria: dispose() borraría la base de pruebas."""
    llamadas = []
    monkeypatch.setattr(app_pkg, 'liberar_conexiones', lambda a, base=None: llamadas.append(a))
    app_pkg.create_app('testing')
    assert llamadas == []
