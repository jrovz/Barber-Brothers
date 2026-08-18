"""CRUD de servicios y su galeria de imagenes."""
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.admin import bp
from app.utils.decorators import admin_required
from app.models.cliente import Cita
from app.models.servicio import Servicio
from app import db
from app.admin.forms import ServicioForm
from app.admin.utils import save_image


@bp.route('/servicios', methods=['GET', 'POST'])
@login_required
@admin_required
def gestionar_servicios():
    form = ServicioForm()
    try:
        if form.validate_on_submit():
            imagen_url = None
            if form.imagen_file.data:
                imagen_url = save_image(form.imagen_file.data, 'servicios')
            elif form.imagen_url.data:
                imagen_url = form.imagen_url.data

            nuevo_servicio = Servicio(
                nombre=form.nombre.data,
                descripcion=form.descripcion.data,
                precio=form.precio.data,
                duracion_estimada=form.duracion_estimada.data,
                activo=form.activo.data,
                imagen_url=imagen_url,
                orden=form.orden.data
            )
            db.session.add(nuevo_servicio)
            
            try:
                db.session.flush()  # Para obtener el ID del servicio antes de commit
                
                # Procesar múltiples imágenes
                if form.imagenes_files.data:
                    from app.models.servicio_imagen import ServicioImagen
                    for i, file in enumerate(form.imagenes_files.data):
                        if file and file.filename:  # Verificar que el archivo sea válido
                            ruta_imagen = save_image(file, 'servicios')
                            if ruta_imagen:
                                imagen_servicio = ServicioImagen(
                                    servicio_id=nuevo_servicio.id,
                                    ruta_imagen=ruta_imagen,
                                    orden=i,
                                    activa=True
                                )
                                db.session.add(imagen_servicio)
                
                db.session.commit()
                flash('Servicio añadido correctamente.', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error al añadir servicio: {str(e)}', 'danger')
                print(f"Error al guardar servicio en la base de datos: {e}")
                import traceback
                traceback.print_exc()
            return redirect(url_for('admin.gestionar_servicios'))

        # Obtener la lista de servicios
        # MODIFICADO: Ordenar por el campo 'orden' y luego por 'nombre' para consistencia
        servicios_lista = Servicio.query.order_by(Servicio.orden.asc(), Servicio.nombre.asc()).all()
        return render_template("admin/servicios.html", 
                            title="Gestionar Servicios", 
                            servicios=servicios_lista, 
                            form=form)
    except Exception as e:
        print(f"Error en gestionar_servicios: {e}")
        import traceback
        traceback.print_exc()
        flash(f'Error al cargar servicios: {str(e)}', 'danger')
        return render_template("admin/servicios.html", 
                            title="Gestionar Servicios", 
                            servicios=[], 
                            form=form,
                            error="No se pudieron cargar los servicios")


@bp.route('/servicios/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_servicio(id):
    servicio = Servicio.query.get_or_404(id)
    form = ServicioForm(obj=servicio if request.method == 'GET' else None)

    if form.validate_on_submit():
        servicio.nombre = form.nombre.data
        servicio.descripcion = form.descripcion.data
        servicio.precio = form.precio.data
        servicio.duracion_estimada = form.duracion_estimada.data
        servicio.activo = form.activo.data
        servicio.orden = form.orden.data
        
        if form.imagen_file.data:
            imagen_path = save_image(form.imagen_file.data, 'servicios')
            if imagen_path:
                servicio.imagen_url = imagen_path
        elif form.imagen_url.data and form.imagen_url.data != servicio.imagen_url:
            servicio.imagen_url = form.imagen_url.data
        
        try:
            # Procesar múltiples imágenes nuevas
            if form.imagenes_files.data:
                from app.models.servicio_imagen import ServicioImagen
                # Obtener el orden máximo actual para continuar la secuencia
                max_orden = db.session.query(db.func.max(ServicioImagen.orden)).filter_by(
                    servicio_id=servicio.id, activa=True
                ).scalar() or -1
                
                for i, file in enumerate(form.imagenes_files.data):
                    if file and file.filename:  # Verificar que el archivo sea válido
                        ruta_imagen = save_image(file, 'servicios')
                        if ruta_imagen:
                            imagen_servicio = ServicioImagen(
                                servicio_id=servicio.id,
                                ruta_imagen=ruta_imagen,
                                orden=max_orden + i + 1,
                                activa=True
                            )
                            db.session.add(imagen_servicio)
            
            db.session.commit()
            flash('Servicio actualizado correctamente.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar servicio: {str(e)}', 'danger')
        return redirect(url_for('admin.gestionar_servicios'))

    if request.method == 'GET': # Ensure form is pre-filled
        form.nombre.data = servicio.nombre
        form.descripcion.data = servicio.descripcion
        form.precio.data = servicio.precio
        form.duracion_estimada.data = servicio.duracion_estimada
        form.activo.data = servicio.activo
        form.imagen_url.data = servicio.imagen_url
        form.orden.data = servicio.orden

    return render_template('admin/editar_servicio.html', 
                           title="Editar Servicio", 
                           form=form, 
                           servicio=servicio)


@bp.route('/servicios/imagen/<int:imagen_id>/eliminar', methods=['POST'])
@login_required
def eliminar_imagen_servicio(imagen_id):
    """Eliminar una imagen específica de un servicio"""
    if not hasattr(current_user, 'is_admin') or not current_user.is_admin():
        return jsonify({'success': False, 'message': 'No autorizado'}), 403
    
    try:
        from app.models.servicio_imagen import ServicioImagen
        imagen = ServicioImagen.query.get_or_404(imagen_id)
        
        # Marcar como inactiva en lugar de eliminar (soft delete)
        imagen.activa = False
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Imagen eliminada correctamente'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/servicios/eliminar/<int:id>', methods=['POST'])
@login_required
@admin_required
def eliminar_servicio(id):
    servicio = Servicio.query.get_or_404(id)
    # Add check for associated Citas if necessary
    if Cita.query.filter_by(servicio_id=id).first(): # Assuming Cita has servicio_id
         flash(f'No se puede eliminar el servicio {servicio.nombre} porque tiene citas asociadas.', 'danger')
         return redirect(url_for('admin.gestionar_servicios'))
    try:
        db.session.delete(servicio)
        db.session.commit()
        flash('Servicio eliminado correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar servicio: {str(e)}', 'danger')
    return redirect(url_for('admin.gestionar_servicios'))



