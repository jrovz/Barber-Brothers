from functools import wraps
from flask import abort, g
from flask_login import current_user


def admin_required(f):
    """Bloquea el acceso con 403 a quien no sea un administrador autenticado."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not getattr(current_user, 'is_admin', None):
            abort(403)
        if not current_user.is_admin():
            abort(403)
        return f(*args, **kwargs)
    return wrapper


def requiere_tienda(f):
    """Devuelve 404 si el negocio actual tiene la tienda desactivada."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not getattr(g.negocio, 'tienda_activa', False):
            abort(404)
        return f(*args, **kwargs)
    return wrapper
