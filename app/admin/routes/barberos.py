"""CRUD de barberos, sus servicios asociados y disponibilidad horaria."""
from flask import render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required
from app.admin import bp
from app.utils.decorators import admin_required
from app.models.cliente import Cita
from app.models.servicio import Servicio
from app.models.barbero import Barbero, DisponibilidadBarbero, BloqueoHorario
from app.models.barbero_servicio import BarberoServicio
from decimal import Decimal
from app import db
from app.admin.forms import BarberoForm, DisponibilidadForm
from app.admin.utils import save_image
from datetime import datetime, time

import logging

logger = logging.getLogger(__name__)


@bp.route('/barberos', methods=['GET', 'POST'])
@login_required
@admin_required
def gestionar_barberos():
    form = BarberoForm()
    if form.validate_on_submit():
        imagen_url = None
        if form.imagen_file.data: # Prefer uploaded file
            imagen_url = save_image(form.imagen_file.data, 'barberos')
        # Add logic for imagen_url field if you have it in BarberoForm and want to use it as fallback
        # elif form.imagen_url.data:
        #     imagen_url = form.imagen_url.data

        nuevo_barbero = Barbero(
            nombre=form.nombre.data,
            especialidad=form.especialidad.data,
            descripcion=form.descripcion.data,
            activo=form.activo.data,
            imagen_url=imagen_url,
            tiene_acceso_web=form.tiene_acceso_web.data
        )
        
        # Configurar acceso web si está habilitado
        if form.tiene_acceso_web.data:
            if form.username.data:
                nuevo_barbero.username = form.username.data
            else:
                nuevo_barbero.generate_username()
            
            if form.password.data:
                nuevo_barbero.set_password(form.password.data)
        
        db.session.add(nuevo_barbero)
        try:
            db.session.commit()
            flash('Barbero añadido correctamente.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al añadir barbero: {str(e)}', 'danger')
        return redirect(url_for('admin.gestionar_barberos'))

    barberos_lista = Barbero.query.order_by(Barbero.nombre).all()
    return render_template("admin/barberos.html", 
                           title="Gestionar Barberos", 
                           barberos=barberos_lista, 
                           form=form)


@bp.route('/barberos/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_barbero(id):
    barbero = Barbero.query.get_or_404(id)
    # Pass obj=barbero to pre-fill the form on GET
    form = BarberoForm(obj=barbero if request.method == 'GET' else None)
    
    # Añadir barbero_id al form para validación de username ANTES de validar
    form.barbero_id = barbero.id
    
    if form.validate_on_submit():
        
        barbero.nombre = form.nombre.data
        barbero.especialidad = form.especialidad.data
        barbero.descripcion = form.descripcion.data
        barbero.activo = form.activo.data
        barbero.tiene_acceso_web = form.tiene_acceso_web.data
        
        # Configurar acceso web
        if form.tiene_acceso_web.data:
            if form.username.data:
                barbero.username = form.username.data
            elif not barbero.username:
                barbero.generate_username()
            
            if form.password.data:
                barbero.set_password(form.password.data)
        else:
            # Si se desactiva el acceso web, limpiar credenciales
            barbero.username = None
            barbero.password_hash = None
            barbero.tiene_acceso_web = False
        
        if form.imagen_file.data:
            imagen_url = save_image(form.imagen_file.data, 'barberos')
            if imagen_url:
                barbero.imagen_url = imagen_url
        # Add logic for imagen_url field if you have it in BarberoForm
        # elif form.imagen_url.data and form.imagen_url.data != barbero.imagen_url:
        #     barbero.imagen_url = form.imagen_url.data
        
        try:
            db.session.commit()
            flash('Barbero actualizado correctamente.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar barbero: {str(e)}', 'danger')
        return redirect(url_for('admin.gestionar_barberos'))
    
    # For GET, ensure form is pre-filled if not using obj in constructor for all fields
    if request.method == 'GET':
        form.nombre.data = barbero.nombre
        form.especialidad.data = barbero.especialidad
        form.descripcion.data = barbero.descripcion
        form.activo.data = barbero.activo
        form.tiene_acceso_web.data = barbero.tiene_acceso_web
        form.username.data = barbero.username
        # No precargar la contraseña por seguridad

    return render_template('admin/editar_barbero.html', 
                          title="Editar Barbero", 
                          form=form, 
                          barbero=barbero)


@bp.route('/barberos/eliminar/<int:id>', methods=['POST'])
@login_required
@admin_required
def eliminar_barbero(id):
    barbero = Barbero.query.get_or_404(id)
    # Add check for associated Citas if necessary
    try:
        # Delete associated records manually (Cascading delete)
        # 1. Eliminar bloqueos de horario
        BloqueoHorario.query.filter_by(barbero_id=id).delete()
        
        # 2. Eliminar precios personalizados/configuración de servicios
        BarberoServicio.query.filter_by(barbero_id=id).delete()
        
        # 3. Eliminar citas asociadas (Pasadas y futuras)
        Cita.query.filter_by(barbero_id=id).delete()
        
        # 4. Eliminar disponibilidad (Horarios recurrentes)
        DisponibilidadBarbero.query.filter_by(barbero_id=id).delete()
        
        # Finalmente, eliminar al barbero
        db.session.delete(barbero)
        db.session.commit()
        flash('Barbero y todos sus registros asociados (citas, servicios, horarios) eliminados correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error al eliminar barbero: {str(e)}")
        flash(f'Error al eliminar barbero: {str(e)}', 'danger')
    return redirect(url_for('admin.gestionar_barberos'))

# --- Gestión de Servicios y Precios por Barbero ---

@bp.route('/barberos/<int:barbero_id>/servicios', methods=['GET', 'POST'])
@login_required
@admin_required
def gestionar_servicios_barbero(barbero_id):
    """
    Gestionar qué servicios ofrece un barbero y sus precios personalizados.
    
    GET: Muestra tabla con todos los servicios y configuración del barbero
    POST: Guarda la configuración de servicios y precios
    """
    
    barbero = Barbero.query.get_or_404(barbero_id)
    servicios = Servicio.query.filter_by(activo=True).order_by(Servicio.orden, Servicio.nombre).all()
    
    if request.method == 'POST':
        try:
            # Procesar formulario de servicios
            for servicio in servicios:
                # Verificar si el checkbox está marcado
                activo = request.form.get(f'servicio_{servicio.id}_activo') == 'on'
                precio_str = request.form.get(f'servicio_{servicio.id}_precio', '').strip()
                
                # Buscar configuración existente
                config = BarberoServicio.query.filter_by(
                    barbero_id=barbero_id,
                    servicio_id=servicio.id
                ).first()
                
                if activo:
                    # Si está activo, crear o actualizar configuración
                    if not config:
                        config = BarberoServicio(
                            barbero_id=barbero_id,
                            servicio_id=servicio.id
                        )
                        db.session.add(config)
                    
                    config.activo = True
                    
                    # Procesar precio personalizado
                    if precio_str:
                        try:
                            precio_nuevo = Decimal(precio_str)
                            # Solo guardar si es diferente al precio base
                            if precio_nuevo != servicio.precio:
                                config.precio_personalizado = precio_nuevo
                            else:
                                config.precio_personalizado = None
                        except:
                            config.precio_personalizado = None
                    else:
                        config.precio_personalizado = None
                else:
                    # Si está desactivado
                    if config:
                        config.activo = False
            
            db.session.commit()
            flash(f'Servicios de {barbero.nombre} actualizados correctamente.', 'success')
            return redirect(url_for('admin.gestionar_servicios_barbero', barbero_id=barbero_id))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error al actualizar servicios del barbero: {str(e)}")
            flash(f'Error al guardar cambios: {str(e)}', 'danger')
    
    # Preparar datos para la vista
    servicios_config = {}
    for servicio in servicios:
        config = BarberoServicio.query.filter_by(
            barbero_id=barbero_id,
            servicio_id=servicio.id
        ).first()
        
        if config:
            servicios_config[servicio.id] = {
                'servicio': servicio,
                'activo': config.activo,
                'precio_personalizado': config.precio_personalizado,
                'precio_final': config.get_precio_final()
            }
        else:
            # Por defecto, todos los servicios están activos al precio base
            servicios_config[servicio.id] = {
                'servicio': servicio,
                'activo': True,
                'precio_personalizado': None,
                'precio_final': servicio.precio
            }
    
    return render_template('admin/barbero_servicios.html',
                          title=f'Servicios de {barbero.nombre}',
                          barbero=barbero,
                          servicios_config=servicios_config)

# --- Gestión de Disponibilidad de Barberos ---

@bp.route('/barberos/<int:barbero_id>/disponibilidad', methods=['GET', 'POST'])
@login_required
@admin_required
def gestionar_disponibilidad(barbero_id):
    barbero = Barbero.query.get_or_404(barbero_id)
    form = DisponibilidadForm()

    if form.validate_on_submit():
        try:
            hora_inicio = datetime.strptime(form.hora_inicio.data, '%H:%M').time()
            hora_fin = datetime.strptime(form.hora_fin.data, '%H:%M').time()

            if hora_fin <= hora_inicio:
                flash('La hora de fin debe ser posterior a la hora de inicio.', 'danger')
            else:
                # Verificar si ya existe un horario solapado para el mismo día
                disponibilidad_existente = DisponibilidadBarbero.query.filter_by(
                    barbero_id=barbero.id,
                    dia_semana=form.dia_semana.data
                ).filter(
                    # Verificar solapamiento de horarios
                    (DisponibilidadBarbero.hora_inicio < hora_fin) &
                    (DisponibilidadBarbero.hora_fin > hora_inicio)
                ).first()
                
                if disponibilidad_existente:
                    dias_nombres = {0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves', 4: 'Viernes', 5: 'Sábado', 6: 'Domingo'}
                    flash(f'Ya existe un horario que se solapa para el día {dias_nombres.get(form.dia_semana.data, "desconocido")}.', 'warning')
                else:
                    disponibilidad = DisponibilidadBarbero(
                        barbero_id=barbero.id,
                        dia_semana=form.dia_semana.data,
                        hora_inicio=hora_inicio,
                        hora_fin=hora_fin,
                        activo=form.activo.data
                    )
                    db.session.add(disponibilidad)
                    db.session.commit()
                    flash('Disponibilidad añadida correctamente.', 'success')
                    return redirect(url_for('admin.gestionar_disponibilidad', barbero_id=barbero.id))
        except ValueError:
            flash('Formato de hora inválido. Use HH:MM.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al añadir disponibilidad: {str(e)}', 'danger')
    
    # Corrected typo: Disponana -> DisponibilidadBarbero.dia_semana
    disponibilidades = DisponibilidadBarbero.query.filter_by(barbero_id=barbero.id).order_by(DisponibilidadBarbero.dia_semana, DisponibilidadBarbero.hora_inicio).all()
    dias_semana = {0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves', 4: 'Viernes', 5: 'Sábado', 6: 'Domingo'}

    return render_template('admin/disponibilidad.html',
                           title=f'Gestionar Horarios de {barbero.nombre}',
                           form=form,
                           barbero=barbero,
                           disponibilidades=disponibilidades,
                           dias_semana=dias_semana)


@bp.route('/barberos/disponibilidad/eliminar/<int:disp_id>', methods=['POST'])
@login_required
@admin_required
def eliminar_disponibilidad(disp_id):
    disp = DisponibilidadBarbero.query.get_or_404(disp_id)
    barbero_id = disp.barbero_id
    try:
        db.session.delete(disp)
        db.session.commit()
        flash('Horario eliminado correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar el horario: {str(e)}', 'danger')
    return redirect(url_for('admin.gestionar_disponibilidad', barbero_id=barbero_id))


@bp.route('/barberos/<int:barbero_id>/disponibilidad/crear_predeterminada', methods=['POST'])
@login_required
@admin_required
def crear_disponibilidad_predeterminada(barbero_id):
    barbero = Barbero.query.get_or_404(barbero_id)
    horario_estandar = {
        0: [(time(8, 0), time(12, 0)), (time(13, 0), time(20, 0))], # Lunes
        1: [(time(8, 0), time(12, 0)), (time(13, 0), time(20, 0))], # Martes
        2: [(time(8, 0), time(12, 0)), (time(13, 0), time(20, 0))], # Miércoles
        3: [(time(8, 0), time(12, 0)), (time(13, 0), time(20, 0))], # Jueves
        4: [(time(8, 0), time(12, 0)), (time(13, 0), time(20, 0))], # Viernes
        5: [(time(8, 0), time(12, 0)), (time(13, 0), time(20, 0))] # Sábado
    }
    try:
        # Optional: Delete existing before adding defaults
        # DisponibilidadBarbero.query.filter_by(barbero_id=barbero_id).delete()
        # db.session.flush()
        for dia, slots in horario_estandar.items():
            for inicio, fin in slots:
                nueva_disp = DisponibilidadBarbero(
                    barbero_id=barbero.id, dia_semana=dia,
                    hora_inicio=inicio, hora_fin=fin, activo=True
                )
                db.session.add(nueva_disp)
        db.session.commit()
        flash('Horario estándar aplicado correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al aplicar horario estándar: {str(e)}', 'danger')
    return redirect(url_for('admin.gestionar_disponibilidad', barbero_id=barbero_id))

# --- Gestión de Servicios (CRUD) ---

