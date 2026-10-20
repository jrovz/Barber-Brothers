"""Lógica del script deployment/alerta_disco.py (corre en el servidor con cron)."""
import importlib.util
import json
import pathlib
from datetime import datetime, timedelta

import pytest

_RUTA = pathlib.Path(__file__).resolve().parent.parent / 'deployment' / 'alerta_disco.py'
_spec = importlib.util.spec_from_file_location('alerta_disco', _RUTA)
alerta = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(alerta)

AHORA = datetime(2026, 10, 20, 12, 0)
ARCHIVOS = [('/var/log/barber-brothers/app.log', 300 * 1024 * 1024), ('/var/log/syslog', 1024 * 1024)]


# ------------------------------------------------------------------ nivel

@pytest.mark.parametrize('uso, mayor, esperado', [
    (40, 10, 'ok'),
    (69.9, 199, 'ok'),
    (70, 10, 'aviso'),
    (50, 200, 'aviso'),      # un log enorme avisa aunque el disco esté bien
    (84.9, 10, 'aviso'),
    (85, 10, 'urgente'),
    (99, 500, 'urgente'),
])
def test_nivel(uso, mayor, esperado):
    assert alerta.nivel(uso, mayor) == esperado


def test_nivel_con_umbrales_propios():
    assert alerta.nivel(5, 0, aviso=1, urgente=50, log_max_mb=200) == 'aviso'


# ----------------------------------------------------------------- decidir

def test_primer_aviso_se_envia():
    assert alerta.decidir('aviso', {}, AHORA) == 'alerta'


def test_no_repite_dentro_de_24_horas():
    estado = {'nivel': 'aviso', 'enviado': (AHORA - timedelta(hours=3)).isoformat()}
    assert alerta.decidir('aviso', estado, AHORA) is None


def test_repite_pasadas_24_horas():
    estado = {'nivel': 'aviso', 'enviado': (AHORA - timedelta(hours=25)).isoformat()}
    assert alerta.decidir('aviso', estado, AHORA) == 'alerta'


def test_subir_de_nivel_avisa_de_inmediato():
    estado = {'nivel': 'aviso', 'enviado': (AHORA - timedelta(minutes=30)).isoformat()}
    assert alerta.decidir('urgente', estado, AHORA) == 'alerta'


def test_bajar_de_urgente_a_aviso_no_reenvia():
    estado = {'nivel': 'urgente', 'enviado': (AHORA - timedelta(hours=1)).isoformat()}
    assert alerta.decidir('aviso', estado, AHORA) is None


def test_normalidad_sin_historial_no_avisa():
    assert alerta.decidir('ok', {}, AHORA) is None
    assert alerta.decidir('ok', {'nivel': 'ok', 'enviado': None}, AHORA) is None


def test_vuelta_a_la_normalidad_manda_resuelto():
    assert alerta.decidir('ok', {'nivel': 'urgente', 'enviado': AHORA.isoformat()}, AHORA) == 'resuelto'


def test_estado_corrupto_equivale_a_sin_historial(tmp_path):
    ruta = tmp_path / 'estado.json'
    ruta.write_text('{no es json')
    assert alerta.leer_estado(str(ruta)) == {}
    assert alerta.leer_estado(str(tmp_path / 'no_existe.json')) == {}


# ----------------------------------------------------------------- mensaje

def test_mensaje_urgente_y_sin_datos_personales():
    asunto, cuerpo = alerta.armar_mensaje('alerta', 'urgente', 91.4, 1.2, ARCHIVOS, AHORA, 'srv')
    assert 'URGENTE' in asunto and '91' in asunto
    assert '/var/log/barber-brothers/app.log' in cuerpo and '300 MB' in cuerpo
    assert 'truncate' in cuerpo and 'NUNCA rm' in cuerpo
    assert '@' not in cuerpo


def test_mensaje_resuelto():
    asunto, cuerpo = alerta.armar_mensaje('resuelto', 'ok', 35, 20.0, [], AHORA, 'srv')
    assert 'normalizado' in asunto.lower()
    assert 'no se pudo leer' in cuerpo


# ---------------------------------------------------------------- archivos

def test_archivos_grandes_ordena_y_limita(tmp_path):
    (tmp_path / 'sub').mkdir()
    for nombre, tam in [('a.log', 10), ('b.log', 5000), ('sub/c.log', 300), ('d.log', 1)]:
        (tmp_path / nombre).write_bytes(b'x' * tam)
    top = alerta.archivos_grandes(str(tmp_path), cuantos=2)
    assert [pathlib.Path(r).name for r, _ in top] == ['b.log', 'c.log']


def test_archivos_grandes_en_ruta_inexistente_no_falla(tmp_path):
    assert alerta.archivos_grandes(str(tmp_path / 'nada')) == []


# ------------------------------------------------------------------ correo

class FakeSMTP:
    instancias = []

    def __init__(self, servidor, puerto, timeout=None):
        self.servidor, self.puerto, self.acciones, self.mensaje = servidor, puerto, [], None
        FakeSMTP.instancias.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def starttls(self):
        self.acciones.append('starttls')

    def login(self, usuario, clave):
        self.acciones.append(('login', usuario, clave))

    def send_message(self, msg):
        self.mensaje = msg


def test_enviar_correo_usa_el_smtp_de_la_app():
    FakeSMTP.instancias.clear()
    env = {'MAIL_SERVER': 'smtp.ejemplo.com', 'MAIL_PORT': '587', 'MAIL_USE_TLS': 'True',
           'MAIL_USERNAME': 'app@ejemplo.com', 'MAIL_PASSWORD': 'secreta'}
    alerta.enviar_correo('Asunto', 'Cuerpo', 'yo@ejemplo.com', env=env, smtp_cls=FakeSMTP)
    smtp = FakeSMTP.instancias[0]
    assert (smtp.servidor, smtp.puerto) == ('smtp.ejemplo.com', 587)
    assert smtp.acciones == ['starttls', ('login', 'app@ejemplo.com', 'secreta')]
    assert smtp.mensaje['To'] == 'yo@ejemplo.com' and smtp.mensaje['Subject'] == 'Asunto'


def test_enviar_correo_sin_configuracion_falla_sin_filtrar_nada():
    with pytest.raises(RuntimeError) as e:
        alerta.enviar_correo('a', 'b', 'c@d.com', env={'MAIL_SERVER': 'x'}, smtp_cls=FakeSMTP)
    assert 'secreta' not in str(e.value)


# -------------------------------------------------------------------- main

def _args(tmp_path, *extra):
    return alerta.parsear(['--a', 'yo@ejemplo.com', '--estado', str(tmp_path / 'estado.json'), *extra])


def test_ejecutar_envia_una_vez_y_recuerda_el_estado(tmp_path):
    enviados = []
    args = _args(tmp_path, '--aviso', '50')
    kw = dict(enviar=lambda a, c: enviados.append(a), uso=(60.0, 5.0), archivos=ARCHIVOS[1:])
    assert alerta.ejecutar(args, ahora=AHORA, **kw) == 0
    assert alerta.ejecutar(args, ahora=AHORA + timedelta(minutes=30), **kw) == 0
    assert len(enviados) == 1                      # la segunda pasada no repite
    assert json.loads((tmp_path / 'estado.json').read_text())['nivel'] == 'aviso'


def test_ejecutar_manda_resuelto_al_normalizarse(tmp_path):
    enviados = []
    args = _args(tmp_path, '--aviso', '50')
    alerta.ejecutar(args, ahora=AHORA, enviar=lambda a, c: enviados.append(a), uso=(60.0, 5.0), archivos=[])
    alerta.ejecutar(args, ahora=AHORA + timedelta(hours=1), enviar=lambda a, c: enviados.append(a),
                    uso=(30.0, 20.0), archivos=[])
    assert len(enviados) == 2 and 'normalizado' in enviados[1].lower()


def test_ejecutar_sin_problema_no_envia_ni_guarda_alerta(tmp_path):
    enviados = []
    alerta.ejecutar(_args(tmp_path), ahora=AHORA, enviar=lambda a, c: enviados.append(a),
                    uso=(30.0, 20.0), archivos=ARCHIVOS[1:])
    assert enviados == []


def test_sin_enviar_no_envia_ni_guarda_estado(tmp_path):
    enviados = []
    args = _args(tmp_path, '--aviso', '1', '--sin-enviar')
    alerta.ejecutar(args, ahora=AHORA, enviar=lambda a, c: enviados.append(a), uso=(60.0, 5.0), archivos=[])
    assert enviados == [] and not (tmp_path / 'estado.json').exists()


def test_probar_envia_aunque_todo_este_bien(tmp_path):
    enviados = []
    alerta.ejecutar(_args(tmp_path, '--probar'), ahora=AHORA,
                    enviar=lambda a, c: enviados.append((a, c)), uso=(10.0, 30.0), archivos=ARCHIVOS[1:])
    assert len(enviados) == 1 and enviados[0][0].startswith('[PRUEBA]')


def test_si_falla_el_correo_devuelve_2_y_no_marca_como_avisado(tmp_path, capsys):
    def roto(asunto, cuerpo):
        raise OSError('sin red')
    args = _args(tmp_path, '--aviso', '1')
    codigo = alerta.ejecutar(args, ahora=AHORA, enviar=roto, uso=(60.0, 5.0), archivos=[])
    assert codigo == 2
    assert 'OSError' in capsys.readouterr().err
    # el siguiente intento vuelve a probar, porque no quedó registrado como enviado
    enviados = []
    alerta.ejecutar(args, ahora=AHORA + timedelta(minutes=30), enviar=lambda a, c: enviados.append(a),
                    uso=(60.0, 5.0), archivos=[])
    assert len(enviados) == 1
