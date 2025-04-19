from app.api import bp

@bp.route('/info')
def info():
    return {
        'nombre': 'Barberia',
        'direccion': 'Calle Falsa 123',
        'telefono': '123456789'
    }