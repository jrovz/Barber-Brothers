"""CRUD de sliders (portada) del sitio publico."""
from flask import render_template, redirect, url_for, flash, current_app
from flask_login import login_required
from app.admin import bp
from app.utils.decorators import admin_required
try:
    from app.models.slider import Slider
except Exception as e:
    print(f"Warning: No se pudo importar el modelo Slider: {e}")
    Slider = None
from app import db
from app.admin.slider_forms import SliderForm
from app.admin.utils import save_image
from datetime import datetime
import os

import logging

logger = logging.getLogger(__name__)


@bp.route('/sliders', methods=['GET', 'POST'])
@login_required
@admin_required
def gestionar_sliders():
    
    if Slider is None:
        flash('Error: El modelo Slider no está disponible. Verifica que la tabla exista en la base de datos.', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    form = SliderForm()
    
    if form.validate_on_submit():
        try:
            slider = Slider(
                titulo=form.titulo.data,
                subtitulo=form.subtitulo.data,
                tipo=form.tipo.data,
                activo=form.activo.data,
                orden=form.orden.data
            )
            
            # Procesar según el tipo de slide
            if form.tipo.data == 'imagen':
                if form.imagen.data:
                    filename = save_image(form.imagen.data, 'sliders')
                    slider.imagen_url = filename
            
            elif form.tipo.data == 'instagram':
                slider.instagram_embed_code = form.instagram_embed_code.data
            
            db.session.add(slider)
            db.session.commit()
            
            flash(f'Slide "{slider.titulo}" creado exitosamente.', 'success')
            return redirect(url_for('admin.gestionar_sliders'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error al crear slider: {str(e)}", exc_info=True)
            flash('Error al crear el slide. Por favor, inténtalo de nuevo.', 'danger')
    
    # Obtener todos los sliders ordenados
    sliders = Slider.query.order_by(Slider.orden.asc(), Slider.fecha_creacion.desc()).all()
    
    return render_template('admin/sliders.html', 
                         title='Gestión de Sliders', 
                         form=form, 
                         sliders=sliders)


@bp.route('/sliders/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_slider(id):
    
    if Slider is None:
        flash('Error: El modelo Slider no está disponible. Verifica que la tabla exista en la base de datos.', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    slider = Slider.query.get_or_404(id)
    form = SliderForm(obj=slider)
    form._editing = True  # Marcar que estamos editando
    
    if form.validate_on_submit():
        try:
            slider.titulo = form.titulo.data
            slider.subtitulo = form.subtitulo.data
            slider.tipo = form.tipo.data
            slider.activo = form.activo.data
            slider.orden = form.orden.data
            slider.fecha_actualizacion = datetime.utcnow()
            
            # Procesar según el tipo de slide
            if form.tipo.data == 'imagen':
                if form.imagen.data:
                    # Eliminar imagen anterior si existe
                    if slider.imagen_url:
                        old_filename = slider.imagen_url.split('/')[-1]
                        old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'sliders', old_filename)
                        try:
                            if os.path.exists(old_path):
                                os.remove(old_path)
                                logger.info(f"Imagen anterior eliminada: {old_path}")
                        except Exception as e:
                            logger.warning(f"No se pudo eliminar la imagen anterior: {str(e)}")
                    
                    # Guardar nueva imagen
                    filename = save_image(form.imagen.data, 'sliders')
                    slider.imagen_url = filename
                
                # Limpiar código de Instagram si cambió a imagen
                if slider.tipo != 'imagen':
                    slider.instagram_embed_code = None
            
            elif form.tipo.data == 'instagram':
                slider.instagram_embed_code = form.instagram_embed_code.data
                
                # Limpiar imagen si cambió a Instagram
                if slider.tipo != 'instagram':
                    if slider.imagen_url:
                        old_filename = slider.imagen_url.split('/')[-1]
                        old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'sliders', old_filename)
                        try:
                            if os.path.exists(old_path):
                                os.remove(old_path)
                                logger.info(f"Imagen eliminada al cambiar a Instagram: {old_path}")
                        except Exception as e:
                            logger.warning(f"No se pudo eliminar la imagen: {str(e)}")
                    slider.imagen_url = None
            
            db.session.commit()
            flash(f'Slide "{slider.titulo}" actualizado exitosamente.', 'success')
            return redirect(url_for('admin.gestionar_sliders'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error al actualizar slider: {str(e)}", exc_info=True)
            flash('Error al actualizar el slide. Por favor, inténtalo de nuevo.', 'danger')
    
    return render_template('admin/editar_slider.html', 
                         title=f'Editar Slide - {slider.titulo}', 
                         form=form, 
                         slider=slider)


@bp.route('/sliders/eliminar/<int:id>', methods=['POST'])
@login_required
@admin_required
def eliminar_slider(id):
    
    if Slider is None:
        flash('Error: El modelo Slider no está disponible. Verifica que la tabla exista en la base de datos.', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    slider = Slider.query.get_or_404(id)
    
    try:
        titulo = slider.titulo
        imagen_eliminada = False
        error_imagen = None
        
        # Eliminar imagen asociada si existe
        if slider.imagen_url and slider.tipo == 'imagen':
            try:
                filename = slider.imagen_url.split('/')[-1]
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'sliders', filename)
                
                logger.info(f"Intentando eliminar archivo: {file_path}")
                
                if os.path.exists(file_path):
                    os.remove(file_path)
                    imagen_eliminada = True
                    logger.info(f"Imagen eliminada exitosamente: {file_path}")
                else:
                    logger.warning(f"El archivo no existe: {file_path}")
                    error_imagen = f"El archivo de imagen no fue encontrado en el servidor"
                    
            except Exception as e:
                error_imagen = f"Error al eliminar la imagen: {str(e)}"
                logger.error(f"Error al eliminar imagen del slide: {str(e)}", exc_info=True)
        
        # Eliminar el slider de la base de datos
        db.session.delete(slider)
        db.session.commit()
        
        # Mostrar mensaje de éxito con información adicional
        if error_imagen:
            flash(f'Slide "{titulo}" eliminado de la base de datos, pero hubo un problema con la imagen: {error_imagen}', 'warning')
        else:
            mensaje = f'Slide "{titulo}" eliminado exitosamente.'
            if imagen_eliminada:
                mensaje += ' La imagen también fue eliminada del servidor.'
            flash(mensaje, 'success')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error al eliminar slider: {str(e)}", exc_info=True)
        flash(f'Error al eliminar el slide: {str(e)}', 'danger')
    
    return redirect(url_for('admin.gestionar_sliders'))

# ================================
# API ENDPOINTS PARA CONFIGURACIONES
# ================================


