"""CRUD de categorias de productos."""
from flask import render_template, redirect, url_for, flash
from flask_login import login_required
from app.admin import bp
from app.utils.decorators import admin_required
from app.models.categoria import Categoria
from app import db
from app.admin.forms import CategoriaForm


@bp.route('/categorias', methods=['GET', 'POST'])
@login_required
@admin_required
def gestionar_categorias():
    form = CategoriaForm()
    if form.validate_on_submit():
        nueva_categoria = Categoria(nombre=form.nombre.data)
        db.session.add(nueva_categoria)
        try:
            db.session.commit()
            flash('Categoría añadida correctamente.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al añadir categoría: {str(e)}', 'danger')
        return redirect(url_for('admin.gestionar_categorias'))
    
    categorias_lista = Categoria.query.order_by(Categoria.nombre).all()
    return render_template('admin/categorias.html',
                           title="Gestionar Categorías",
                           categorias=categorias_lista,
                           form=form)


@bp.route('/categorias/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_categoria(id):
    categoria = Categoria.query.get_or_404(id)
    form = CategoriaForm(obj=categoria) # Pass obj to pre-fill and for validation context

    if form.validate_on_submit():
        categoria.nombre = form.nombre.data
        try:
            db.session.commit()
            flash('Categoría actualizada correctamente.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar categoría: {str(e)}', 'danger')
        return redirect(url_for('admin.gestionar_categorias'))
    
    return render_template('admin/editar_categoria.html',
                           title="Editar Categoría",
                           form=form,
                           categoria=categoria)


@bp.route('/categorias/eliminar/<int:id>', methods=['POST'])
@login_required
@admin_required
def eliminar_categoria(id):
    categoria = Categoria.query.get_or_404(id)
    if categoria.productos.first():
        flash('No se puede eliminar la categoría porque tiene productos asociados. Por favor, reasigne o elimine esos productos primero.', 'danger')
        return redirect(url_for('admin.gestionar_categorias'))
    try:
        db.session.delete(categoria)
        db.session.commit()
        flash('Categoría eliminada correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar categoría: {str(e)}', 'danger')
    return redirect(url_for('admin.gestionar_categorias'))

# --- Gestión de Barberos (CRUD) ---

