from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

ZONA_POR_DEFECTO = 'America/Bogota'


def _zona(nombre):
    try:
        return ZoneInfo(nombre or ZONA_POR_DEFECTO)
    except (ZoneInfoNotFoundError, ValueError):
        pass
    try:
        return ZoneInfo(ZONA_POR_DEFECTO)
    except ZoneInfoNotFoundError:
        # Sin base de datos de zonas horarias (falta tzdata): Colombia es UTC-5 todo el año.
        return timezone(timedelta(hours=-5))


def ahora_negocio(negocio=None):
    """Hora actual en la zona horaria del negocio, sin información de zona (naive).

    Las citas se guardan como fecha/hora local sin zona, así que esta es la hora con la
    que hay que compararlas. Si el negocio no tiene zona válida se usa America/Bogota.
    """
    if negocio is None:
        from app.utils.negocio_actual import obtener_negocio
        negocio = obtener_negocio()
    zona = _zona(getattr(negocio, 'zona_horaria', None))
    return datetime.now(timezone.utc).astimezone(zona).replace(tzinfo=None)
