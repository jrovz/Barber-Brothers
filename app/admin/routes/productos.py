"""CRUD de productos del catalogo."""
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.admin import bp
from app.utils.decorators import admin_required
from app.models.producto import Producto
from app import db
from app.admin.forms import ProductoForm
from app.admin.utils import save_image


@bp.route('/productos', methods=['GET', 'POST'])
@login_required
@admin_required
def gestionar_productos():
    form = ProductoForm()
    if form.validate_on_submit():
        imagen_url = None
        if form.imagen_file.data:
            imagen_url = save_image(form.imagen_file.data, 'productos')
        elif form.imagen_url.data:
            imagen_url = form.imagen_url.data
        
        selected_categoria_id = form.categoria_id.data
        if selected_categoria_id == 0:
            selected_categoria_id = None

        nuevo_producto = Producto(
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            precio=form.precio.data,
            cantidad=form.cantidad.data,  # Guardar la cantidad
            categoria_id=selected_categoria_id,
            imagen_url=imagen_url
        )
        
        db.session.add(nuevo_producto)
        try:
            db.session.commit()
            flash('Producto añadido correctamente.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al añadir producto: {str(e)}', 'danger')
        return redirect(url_for('admin.gestionar_productos'))
    
    productos_lista = Producto.query.order_by(Producto.creado.desc()).all()
    return render_template("admin/productos.html", 
                           title="Gestionar Productos", 
                           productos=productos_lista, 
                           form=form)


@bp.route('/productos/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_producto(id):
    producto = Producto.query.get_or_404(id)
    form = ProductoForm(obj=producto if request.method == 'GET' else None)
    
    if form.validate_on_submit():
        producto.nombre = form.nombre.data
        producto.descripcion = form.descripcion.data
        producto.precio = form.precio.data
        producto.cantidad = form.cantidad.data  # Actualizar la cantidad
        selected_categoria_id = form.categoria_id.data
        producto.categoria_id = selected_categoria_id if selected_categoria_id != 0 else None
        
        if form.imagen_file.data:
            nueva_imagen = save_image(form.imagen_file.data, 'productos')
            if nueva_imagen:
                producto.imagen_url = nueva_imagen
        elif form.imagen_url.data and form.imagen_url.data != producto.imagen_url:
            producto.imagen_url = form.imagen_url.data
        
        try:
            db.session.commit()
            flash('Producto actualizado correctamente.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar producto: {str(e)}', 'danger')
        return redirect(url_for('admin.gestionar_productos'))
    
    if request.method == 'GET':
        form.nombre.data = producto.nombre
        form.descripcion.data = producto.descripcion
        form.precio.data = producto.precio
        form.cantidad.data = producto.cantidad  # Prellenar la cantidad
        form.categoria_id.data = producto.categoria_id if producto.categoria_id is not None else 0
        form.imagen_url.data = producto.imagen_url

    return render_template('admin/editar_producto.html', 
                           title="Editar Producto", 
                           form=form, 
                           producto=producto)


@bp.route('/productos/eliminar/<int:id>', methods=['POST'])
@login_required
@admin_required
def eliminar_producto(id):
    producto = Producto.query.get_or_404(id)
    try:
        db.session.delete(producto)
        db.session.commit()
        flash('Producto eliminado correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar producto: {str(e)}', 'danger')
    return redirect(url_for('admin.gestionar_productos'))

# --- Gestión de Categorías (CRUD) ---

