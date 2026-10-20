#!/usr/bin/env python3
"""Avisa por correo cuando el disco se llena o un log crece demasiado.

Pensado para correr con cron cada 30 minutos, como el usuario que corre la app:

    */30 * * * * /opt/barber-brothers/venv/bin/python /opt/barber-brothers/deployment/alerta_disco.py --a tucorreo@ejemplo.com >> /var/log/barber-brothers/alerta_disco.log 2>&1

Usa el mismo SMTP que la app (variables MAIL_* del .env), sin instalar nada más.

- aviso: disco >= 70 % o algún archivo de log >= 200 MB
- urgente: disco >= 85 %
- Escribe una vez por cada subida de nivel y la repite cada 24 h mientras siga el problema.
  Cuando vuelve a la normalidad manda un aviso de "resuelto".
- No envía datos de clientes: solo cifras de disco y nombres/tamaños de archivos de log.

Probar que el correo llega:        alerta_disco.py --a correo --probar
Ver qué haría sin enviar nada:     alerta_disco.py --a correo --sin-enviar
Simular el problema (umbral bajo): alerta_disco.py --a correo --aviso 1
"""
import argparse
import json
import os
import shutil
import smtplib
import socket
import sys
from datetime import datetime, timedelta
from email.message import EmailMessage

UMBRAL_AVISO = 70          # % de disco usado
UMBRAL_URGENTE = 85
LOG_MAX_MB = 200           # tamaño de un archivo de log que ya es sospechoso
REPETIR_HORAS = 24
RUTA_DISCO = '/'
RUTA_LOGS = '/var/log'
RUTA_ENV = '/opt/barber-brothers/.env'
RUTA_ESTADO = '/var/tmp/alerta_disco_estado.json'

ORDEN = {'ok': 0, 'aviso': 1, 'urgente': 2}


# ---------------------------------------------------------------- lógica pura

def nivel(uso_pct, archivo_max_mb, aviso=UMBRAL_AVISO, urgente=UMBRAL_URGENTE, log_max_mb=LOG_MAX_MB):
    if uso_pct >= urgente:
        return 'urgente'
    if uso_pct >= aviso or archivo_max_mb >= log_max_mb:
        return 'aviso'
    return 'ok'


def decidir(nivel_actual, estado, ahora, repetir_horas=REPETIR_HORAS):
    """Devuelve 'alerta', 'resuelto' o None según el nivel actual y lo último que se avisó."""
    anterior = (estado or {}).get('nivel', 'ok')
    if nivel_actual == 'ok':
        return 'resuelto' if ORDEN.get(anterior, 0) > 0 else None
    if ORDEN[nivel_actual] > ORDEN.get(anterior, 0):
        return 'alerta'
    enviado = (estado or {}).get('enviado')
    if not enviado:
        return 'alerta'
    if ahora - datetime.fromisoformat(enviado) >= timedelta(hours=repetir_horas):
        return 'alerta'
    return None


def estado_nuevo(accion, nivel_actual, estado, ahora):
    """Estado a guardar tras la decisión. Si no se avisó, se conserva el que había."""
    if accion in ('alerta', 'resuelto'):
        return {'nivel': nivel_actual, 'enviado': ahora.isoformat()}
    if nivel_actual == 'ok':
        return {'nivel': 'ok', 'enviado': (estado or {}).get('enviado')}
    return estado or {'nivel': nivel_actual, 'enviado': ahora.isoformat()}


def mb(nbytes):
    return nbytes / (1024 * 1024)


def armar_mensaje(accion, nivel_actual, uso_pct, libre_gb, archivos, ahora, host):
    """(asunto, cuerpo) del correo. Solo cifras y nombres de archivos de log."""
    if accion == 'resuelto':
        asunto = f'[{host}] Disco normalizado ({uso_pct:.0f} %)'
        intro = 'El disco volvió a niveles normales.'
    else:
        etiqueta = 'URGENTE' if nivel_actual == 'urgente' else 'AVISO'
        asunto = f'[{host}] {etiqueta}: disco al {uso_pct:.0f} %'
        intro = ('El disco está casi lleno: si se llena del todo la base de datos y la aplicación dejan de funcionar.'
                 if nivel_actual == 'urgente' else
                 'El disco o algún log está creciendo más de lo normal.')
    lineas = [intro, '',
              f'Servidor: {host}',
              f'Hora (UTC): {ahora:%Y-%m-%d %H:%M}',
              f'Uso del disco: {uso_pct:.0f} %  ({libre_gb:.1f} GB libres)',
              '', 'Archivos más grandes en /var/log:']
    lineas += [f'  {mb(t):8.0f} MB  {ruta}' for ruta, t in archivos] or ['  (no se pudo leer)']
    lineas += ['',
               'Qué hacer: revisa el archivo más grande de la lista. Para vaciar un log que el servicio',
               'tiene abierto usa  sudo truncate -s 0 <archivo>  (NUNCA rm: el espacio no se libera).',
               'Ver qué ocupa espacio:  sudo du -xh --max-depth=2 /var | sort -rh | head']
    return asunto, '\n'.join(lineas)


# ----------------------------------------------------------------- lectura

def uso_disco(ruta=RUTA_DISCO):
    """(porcentaje usado como lo muestra df, GB libres para usuarios no root)."""
    # En Linux shutil entrega lo mismo que df: usado sin el espacio reservado a root, y libre
    # para usuarios normales. df calcula el porcentaje como usado / (usado + libre).
    _, usado, libre = shutil.disk_usage(ruta)
    return 100.0 * usado / (usado + libre), libre / 1024 ** 3


def archivos_grandes(ruta=RUTA_LOGS, cuantos=5, profundidad=3):
    """Los archivos más pesados bajo `ruta`. Ignora lo que no pueda leer."""
    hallados = []

    def recorrer(directorio, nivel_actual):
        try:
            with os.scandir(directorio) as it:
                for e in it:
                    try:
                        if e.is_file(follow_symlinks=False):
                            hallados.append((e.path, e.stat(follow_symlinks=False).st_size))
                        elif e.is_dir(follow_symlinks=False) and nivel_actual < profundidad:
                            recorrer(e.path, nivel_actual + 1)
                    except OSError:
                        continue
        except OSError:
            return

    recorrer(ruta, 1)
    return sorted(hallados, key=lambda x: x[1], reverse=True)[:cuantos]


def leer_estado(ruta):
    try:
        with open(ruta, encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def guardar_estado(ruta, estado):
    tmp = f'{ruta}.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(estado, f)
    os.replace(tmp, ruta)


# ------------------------------------------------------------------ correo

def cargar_env(ruta=RUTA_ENV):
    try:
        from dotenv import load_dotenv
        load_dotenv(ruta)
    except ImportError:
        pass


def enviar_correo(asunto, cuerpo, destino, env=None, smtp_cls=None):
    """Envía por el SMTP de la app. Lanza excepción si falla (sin incluir la contraseña)."""
    env = env if env is not None else os.environ
    servidor = env.get('MAIL_SERVER')
    usuario = env.get('MAIL_USERNAME')
    clave = env.get('MAIL_PASSWORD')
    if not (servidor and usuario and clave):
        raise RuntimeError('Faltan MAIL_SERVER, MAIL_USERNAME o MAIL_PASSWORD en el entorno')
    puerto = int(env.get('MAIL_PORT') or 587)
    usa_tls = str(env.get('MAIL_USE_TLS', 'True')).lower() in ('true', '1', 't')

    msg = EmailMessage()
    msg['Subject'] = asunto
    msg['From'] = usuario
    msg['To'] = destino
    msg.set_content(cuerpo)

    if smtp_cls is None:
        smtp_cls = smtplib.SMTP_SSL if puerto == 465 else smtplib.SMTP
    with smtp_cls(servidor, puerto, timeout=30) as smtp:
        if usa_tls and puerto != 465:
            smtp.starttls()
        smtp.login(usuario, clave)
        smtp.send_message(msg)


# -------------------------------------------------------------------- main

def ejecutar(args, ahora=None, enviar=None, uso=None, archivos=None):
    """Una pasada de la alerta. Devuelve el código de salida (0 bien, 2 si falló el envío)."""
    ahora = ahora or datetime.utcnow()
    enviar = enviar or (lambda asunto, cuerpo: enviar_correo(asunto, cuerpo, args.a))
    host = socket.gethostname()
    uso_pct, libre_gb = uso or uso_disco()
    archivos = archivos if archivos is not None else archivos_grandes()
    mayor_mb = mb(archivos[0][1]) if archivos else 0

    if args.probar:
        asunto, cuerpo = armar_mensaje('alerta', 'aviso', uso_pct, libre_gb, archivos, ahora, host)
        enviar('[PRUEBA] ' + asunto, 'Este es un correo de PRUEBA de la alerta de disco.\n\n' + cuerpo)
        print('Correo de prueba enviado.')
        return 0

    actual = nivel(uso_pct, mayor_mb, args.aviso, args.urgente, args.log_max_mb)
    estado = leer_estado(args.estado)
    accion = decidir(actual, estado, ahora)
    print(f'{ahora:%Y-%m-%d %H:%M} disco={uso_pct:.0f}% libre={libre_gb:.1f}GB mayor_log={mayor_mb:.0f}MB '
          f'nivel={actual} accion={accion or "-"}')

    if accion and not args.sin_enviar:
        asunto, cuerpo = armar_mensaje(accion, actual, uso_pct, libre_gb, archivos, ahora, host)
        try:
            enviar(asunto, cuerpo)
        except Exception as e:  # noqa: BLE001  (no hay que filtrar credenciales en el mensaje)
            print(f'ERROR al enviar el correo: {type(e).__name__}', file=sys.stderr)
            return 2
    if not args.sin_enviar:
        guardar_estado(args.estado, estado_nuevo(accion, actual, estado, ahora))
    return 0


def parsear(argv=None):
    p = argparse.ArgumentParser(description='Alerta por correo de disco lleno o logs enormes.')
    p.add_argument('--a', required=True, help='correo que recibe la alerta')
    p.add_argument('--probar', action='store_true', help='envía un correo de prueba y termina')
    p.add_argument('--sin-enviar', action='store_true', help='solo muestra qué haría; no envía ni guarda estado')
    p.add_argument('--aviso', type=float, default=UMBRAL_AVISO)
    p.add_argument('--urgente', type=float, default=UMBRAL_URGENTE)
    p.add_argument('--log-max-mb', type=float, default=LOG_MAX_MB)
    p.add_argument('--estado', default=RUTA_ESTADO)
    p.add_argument('--env', default=RUTA_ENV)
    return p.parse_args(argv)


if __name__ == '__main__':
    argumentos = parsear()
    cargar_env(argumentos.env)
    sys.exit(ejecutar(argumentos))
