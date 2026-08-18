"""CRUD de citas agendadas."""
from flask import render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required
from app.admin import bp
from app.utils.decorators import admin_required
from app.models.cliente import Cliente, Cita
from app import db
from app.admin.forms import CitaForm
from datetime import datetime

import logging

logger = logging.getLogger(__name__)


@bp.route('/citas', methods=['GET', 'POST'])
@login_required
@admin_required
def gestionar_citas():
    form = CitaForm()

    if request.method == 'POST':
        fecha_str = request.form.get('fecha_cita')
        hora_str = request.form.get('hora_cita')

        if not fecha_str or not hora_str:
            flash('Debe seleccionar una fecha y un horario para la cita.', 'danger')
        elif form.validate_on_submit(): # La validación ahora incluye el email
            try:
                fecha_hora_obj = datetime.strptime(f"{fecha_str} {hora_str}", '%Y-%m-%d %H:%M')
                
                cliente_nombre_form = form.cliente_nombre.data.strip()
                cliente_email_form = form.cliente_email.data.strip().lower() # Guardar email en minúsculas

                # Buscar cliente por email primero (más único)
                cliente = Cliente.query.filter(db.func.lower(Cliente.email) == cliente_email_form).first()
                
                if not cliente:
                    # Si no se encuentra por email, intentar por nombre (menos fiable, pero como fallback)
                    cliente_por_nombre = Cliente.query.filter(db.func.lower(Cliente.nombre) == db.func.lower(cliente_nombre_form)).first()
                    if cliente_por_nombre:
                        # Si existe un cliente con ese nombre pero diferente email, podría ser un problema.
                        # Por ahora, se creará uno nuevo si el email no coincide.
                        # Considerar una lógica más avanzada si es necesario.
                        pass

                    # Crear nuevo cliente si no se encontró por email
                    cliente_telefono_form = request.form.get('cliente_telefono', '').strip()
                    cliente = Cliente(nombre=cliente_nombre_form, email=cliente_email_form, telefono=cliente_telefono_form if cliente_telefono_form else None)
                    db.session.add(cliente)
                    flash(f'Nuevo cliente "{cliente_nombre_form}" con email "{cliente_email_form}" será creado.', 'info')
                elif cliente.nombre.lower() != cliente_nombre_form.lower():
                    # Si el email existe pero el nombre es diferente, actualizar el nombre.
                    flash(f'Cliente encontrado por email. Nombre actualizado de "{cliente.nombre}" a "{cliente_nombre_form}".', 'info')
                    cliente.nombre = cliente_nombre_form
                
                # Actualizar teléfono del cliente existente si se proporciona
                cliente_telefono_form = request.form.get('cliente_telefono', '').strip()
                if cliente_telefono_form:
                    cliente.telefono = cliente_telefono_form
                
                # Aquí 'cliente' ya está definido (existente o nuevo)
                nueva_cita = Cita(
                    cliente_id=cliente.id if cliente.id else None, 
                    barbero_id=form.barbero_id.data,
                    servicio_id=form.servicio_id.data,
                    fecha=fecha_hora_obj,
                    estado=form.estado.data,
                    notas=request.form.get('notas_cita', '')
                )
                if not cliente.id: 
                    nueva_cita.cliente = cliente 

                db.session.add(nueva_cita)
                db.session.commit()
                flash('Cita creada correctamente.', 'success')
                return redirect(url_for('admin.gestionar_citas'))

            except ValueError:
                flash('Formato de fecha u hora inválido.', 'danger')
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error al crear la cita: {str(e)}")
                flash(f'Error al crear la cita: {str(e)}', 'danger')
        else:
            flash('Por favor corrige los errores en el formulario.', 'warning')
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"Error en {getattr(form, field).label.text}: {error}", 'danger')

    # Aplicar filtros GET
    query_citas = Cita.query
    
    # Filtro por estado
    estado_filtro = request.args.get('estado')
    if estado_filtro:
        query_citas = query_citas.filter(Cita.estado == estado_filtro)
    
    # Filtro por fecha
    fecha_filtro = request.args.get('fecha')
    if fecha_filtro:
        try:
            # Convertir string a fecha y filtrar por el día completo
            fecha_obj = datetime.strptime(fecha_filtro, '%Y-%m-%d').date()
            query_citas = query_citas.filter(db.func.date(Cita.fecha) == fecha_obj)
        except ValueError:
            flash('Formato de fecha inválido para el filtro.', 'warning')
    
    # Ejecutar query con filtros aplicados
    citas_lista = query_citas.order_by(Cita.fecha.desc()).all()
    
    # NUEVO: Guardar filtros utilizados en cookies para acceso rápido
    if request.method == 'GET' and (estado_filtro or fecha_filtro):
        from flask import make_response
        from app.utils.admin_cookies import AdminCookieManager
        
        filter_data = {}
        if estado_filtro:
            filter_data['estado'] = estado_filtro
        if fecha_filtro:
            filter_data['fecha'] = fecha_filtro
        
        # Esta función se llamará en el after_request del middleware
        # pero podemos también forzarla aquí para casos específicos
    
    return render_template("admin/citas.html", 
                         title="Gestionar Citas", 
                         citas=citas_lista, 
                         form=form, 
                         datetime=datetime,
                         filtros_aplicados={
                             'estado': estado_filtro,
                             'fecha': fecha_filtro
                         })


@bp.route('/citas/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_cita(id):
    cita = Cita.query.get_or_404(id)
    form = CitaForm(obj=cita if request.method == 'GET' else None)

    if request.method == 'GET':
        if cita.cliente:
            form.cliente_nombre.data = cita.cliente.nombre
            form.cliente_email.data = cita.cliente.email # Poblar email
        form.barbero_id.data = cita.barbero_id
        form.servicio_id.data = cita.servicio_id
        form.estado.data = cita.estado
    
    if request.method == 'POST':
        fecha_str = request.form.get('fecha_cita')
        hora_str = request.form.get('hora_cita')

        if not fecha_str or not hora_str:
            flash('Debe seleccionar una fecha y un horario para la cita.', 'danger')
        elif form.validate_on_submit(): # Validación incluye email
            try:
                fecha_hora_obj = datetime.strptime(f"{fecha_str} {hora_str}", '%Y-%m-%d %H:%M')
                
                cliente_nombre_form = form.cliente_nombre.data.strip()
                cliente_email_form = form.cliente_email.data.strip().lower()

                # Lógica para manejar el cliente
                cliente_actual_id = cita.cliente_id
                cliente_encontrado_por_email = Cliente.query.filter(db.func.lower(Cliente.email) == cliente_email_form).first()

                if cliente_encontrado_por_email:
                    # Si el email ya existe y pertenece a otro cliente, es un error.
                    if cliente_actual_id and cliente_encontrado_por_email.id != cliente_actual_id:
                        flash(f'El correo electrónico "{cliente_email_form}" ya está en uso por otro cliente. Por favor, usa un correo diferente o verifica los datos.', 'danger')
                        cliente_para_cita = None # Indica que no se puede proceder
                    else:
                        # El email es el mismo o pertenece al cliente actual. Actualizar nombre si es necesario.
                        cliente_encontrado_por_email.nombre = cliente_nombre_form
                        # Actualizar teléfono si se proporciona
                        cliente_telefono_form = request.form.get('cliente_telefono', '').strip()
                        if cliente_telefono_form:
                            cliente_encontrado_por_email.telefono = cliente_telefono_form
                        cliente_para_cita = cliente_encontrado_por_email
                else:
                    # El email es nuevo.
                    # Si la cita ya tenía un cliente, y el email cambió, se considera crear uno nuevo
                    # o actualizar el existente si el admin lo desea (esto es más complejo, por ahora creamos/actualizamos basado en el nuevo email).
                    if cita.cliente and cita.cliente.email.lower() != cliente_email_form : # Email ha cambiado
                         # Se podría preguntar si se quiere crear un nuevo cliente o actualizar el email del existente.
                         # Por simplicidad, si el email es nuevo, creamos un nuevo cliente.
                         # O, si se quiere actualizar el email del cliente existente:
                         # cita.cliente.email = cliente_email_form
                         # cita.cliente.nombre = cliente_nombre_form
                         # cliente_para_cita = cita.cliente
                         # flash('Email del cliente actualizado.', 'info')
                         
                         # Opción: Crear nuevo cliente si el email es nuevo y diferente al original
                         cliente_telefono_form = request.form.get('cliente_telefono', '').strip()
                         telefono_cliente = cliente_telefono_form if cliente_telefono_form else (cita.cliente.telefono if cita.cliente else None)
                         cliente_para_cita = Cliente(nombre=cliente_nombre_form, email=cliente_email_form, telefono=telefono_cliente)
                         db.session.add(cliente_para_cita)
                         flash(f'Nuevo cliente creado con email "{cliente_email_form}" ya que el email cambió.', 'info')

                    elif not cita.cliente: # La cita no tenía cliente, crear uno nuevo
                        cliente_telefono_form = request.form.get('cliente_telefono', '').strip()
                        cliente_para_cita = Cliente(nombre=cliente_nombre_form, email=cliente_email_form, telefono=cliente_telefono_form if cliente_telefono_form else None)
                        db.session.add(cliente_para_cita)
                        flash(f'Nuevo cliente "{cliente_nombre_form}" será creado.', 'info')
                    else: # El email no cambió, y el cliente ya existía
                        cita.cliente.nombre = cliente_nombre_form # Actualizar nombre
                        # Actualizar teléfono si se proporciona
                        cliente_telefono_form = request.form.get('cliente_telefono', '').strip()
                        if cliente_telefono_form:
                            cita.cliente.telefono = cliente_telefono_form
                        cliente_para_cita = cita.cliente


                if cliente_para_cita: 
                    cita.cliente = cliente_para_cita
                    cita.barbero_id = form.barbero_id.data
                    cita.servicio_id = form.servicio_id.data
                    cita.fecha = fecha_hora_obj
                    cita.estado = form.estado.data
                    cita.notas = request.form.get('notas_cita', cita.notas)
                    db.session.commit()
                    flash('Cita actualizada correctamente.', 'success')
                    return redirect(url_for('admin.gestionar_citas'))
                # else: el flash de error de email duplicado ya se mostró

            except ValueError:
                flash('Formato de fecha u hora inválido.', 'danger')
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error al actualizar la cita: {str(e)}")
                flash(f'Error al actualizar la cita: {str(e)}', 'danger')
        else:
            flash('Por favor corrige los errores en el formulario.', 'warning')
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"Error en {getattr(form, field).label.text}: {error}", 'danger')

    return render_template('admin/editar_cita.html', 
                           title="Editar Cita", 
                           form=form, 
                           cita=cita, 
                           cita_fecha_str=cita.fecha.strftime('%Y-%m-%d') if cita.fecha else None,
                           cita_hora_str=cita.fecha.strftime('%H:%M') if cita.fecha else None,
                           datetime=datetime)


@bp.route('/citas/eliminar/<int:id>', methods=['POST'])
@login_required
@admin_required
def eliminar_cita(id):
    cita = Cita.query.get_or_404(id)
    try:
        db.session.delete(cita)
        db.session.commit()
        flash('Cita eliminada correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar cita: {str(e)}', 'danger')
    return redirect(url_for('admin.gestionar_citas'))

# --- Debug Images ---

