"""Vista de depuracion para auditar imagenes y rutas de subida."""
from flask import render_template, current_app
from flask_login import login_required
from app.admin import bp
from app.utils.decorators import admin_required
from app.models.producto import Producto
from app.models.servicio import Servicio
from app.models.barbero import Barbero


@bp.route('/debug/images')
@login_required
@admin_required
def debug_images():
    barberos = Barbero.query.all()
    productos = Producto.query.all()
    servicios = Servicio.query.all()
    app_path = current_app.root_path
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'app/static/uploads') # Get UPLOAD_FOLDER from config

    return render_template(
        'admin/debug_images.html',
        barberos=barberos,
        productos=productos,
        servicios=servicios,
        app_path=app_path,
        upload_folder=upload_folder # Pass the actual upload folder path
    )

# --- Gestión de Clientes y Segmentación ---

