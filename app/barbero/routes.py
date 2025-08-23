from flask import render_template, request, redirect, url_for, flash, abort, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app.barbero import bp
from app.models.barbero import Barbero
from app.models.cliente import Cita, Cliente
from app.admin.forms import BarberoLoginForm, CitaForm
from app import db
from datetime import datetime, timedelta, time, date
from sqlalchemy import and_, or_

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login específico para barberos"""
    # Si ya está autenticado y es un barbero, redirigir al dashboard de barbero
    if current_user.is_authenticated:
        if hasattr(current_user, 'tiene_acceso_web') and current_user.tiene_acceso_web:
            return redirect(url_for('barbero.dashboard'))
        # Si está autenticado pero no es barbero, cerrar sesión
        logout_user()
    
    form = BarberoLoginForm()
    if form.validate_on_submit():
        barbero = Barbero.query.filter_by(username=form.username.data).first()
        
        if barbero and barbero.check_password(form.password.data) and barbero.puede_acceder_web():
            login_user(barbero, remember=form.remember_me.data)
            flash(f'¡Bienvenido, {barbero.nombre}!', 'success')
            next_page = request.args.get('next')
            # Asegurarse de que next_page sea una ruta de barbero
            if not next_page or not next_page.startswith('/barbero'):
                next_page = url_for('barbero.dashboard')
            return redirect(next_page)
        else:
            flash('Usuario o contraseña incorrectos, o acceso web no habilitado.', 'danger')
    
    return render_template('barbero/login.html', title='Acceso Barberos', form=form)

@bp.route('/logout')
@login_required
def logout():
    """Logout específico para barberos"""
    if hasattr(current_user, 'tiene_acceso_web') and current_user.tiene_acceso_web:
        flash(f'Hasta luego, {current_user.nombre}!', 'info')
        logout_user()
    return redirect(url_for('barbero.login'))

@bp.route('/')
@bp.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    """Dashboard principal del barbero"""
    # Verificar que sea un barbero
    if not hasattr(current_user, 'tiene_acceso_web') or not current_user.tiene_acceso_web:
        abort(403)
    
    # Ejecutar limpieza de bloqueos pasados
    try:
        from app.models.tareas import limpiar_bloqueos_pasados
        bloqueos_eliminados = limpiar_bloqueos_pasados()
        if bloqueos_eliminados > 0:
            print(f"Se han eliminado {bloqueos_eliminados} bloqueos de horario pasados.")
    except Exception as e:
        print(f"Error al limpiar bloqueos pasados: {str(e)}")
    
    barbero = current_user
    
    # Manejar creación de nueva cita desde el dashboard
    if request.method == 'POST':
        try:
            cliente_nombre = request.form.get('cliente_nombre')
            cliente_email = request.form.get('cliente_email')
            servicio_id = request.form.get('servicio_id')
            fecha_str = request.form.get('fecha')
            hora_str = request.form.get('hora')
            estado = request.form.get('estado', 'pendiente')
            
            # Validar datos requeridos
            if not all([cliente_nombre, cliente_email, servicio_id, fecha_str, hora_str]):
                flash('Todos los campos son obligatorios.', 'danger')
                return redirect(url_for('barbero.dashboard'))
            
            # Buscar o crear cliente
            cliente = Cliente.query.filter_by(email=cliente_email).first()
            if not cliente:
                cliente = Cliente(nombre=cliente_nombre, email=cliente_email)
                db.session.add(cliente)
                db.session.flush()
            
            # Crear fecha y hora completa
            fecha_completa = datetime.strptime(f"{fecha_str} {hora_str}", '%Y-%m-%d %H:%M')
            
            # Crear nueva cita
            nueva_cita = Cita(
                cliente_id=cliente.id,
                barbero_id=barbero.id,
                servicio_id=int(servicio_id),
                fecha=fecha_completa,
                estado=estado
            )
            
            db.session.add(nueva_cita)
            db.session.commit()
            
            flash(f'¡Cita creada exitosamente para {cliente_nombre}!', 'success')
            return redirect(url_for('barbero.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear la cita: {str(e)}', 'danger')
            return redirect(url_for('barbero.dashboard'))
    
    today = date.today()
    tomorrow = today + timedelta(days=1)
    week_from_now = today + timedelta(days=7)
    
    # Estadísticas rápidas
    citas_hoy = Cita.query.filter(
        Cita.barbero_id == barbero.id,
        Cita.fecha >= datetime.combine(today, time.min),
        Cita.fecha < datetime.combine(tomorrow, time.min)
    ).count()
    
    citas_pendientes = Cita.query.filter(
        Cita.barbero_id == barbero.id,
        Cita.estado == 'pendiente',
        Cita.fecha >= datetime.now()
    ).count()
    
    # Obtener servicios disponibles para el formulario
    from app.models.servicio import Servicio
    servicios_disponibles = Servicio.query.filter_by(activo=True).all()
    
    # Filtrar citas según el parámetro
    filtro = request.args.get('filtro', 'proximas')  # Default: próximas 7 días
    
    if filtro == 'hoy':
        citas_query = Cita.query.filter(
            Cita.barbero_id == barbero.id,
            Cita.fecha >= datetime.combine(today, time.min),
            Cita.fecha < datetime.combine(tomorrow, time.min)
        )
        titulo_filtro = "Citas de Hoy"
    elif filtro == 'pendientes':
        citas_query = Cita.query.filter(
            Cita.barbero_id == barbero.id,
            Cita.estado == 'pendiente'
        )
        titulo_filtro = "Citas Pendientes"
    elif filtro == 'proximas':
        citas_query = Cita.query.filter(
            Cita.barbero_id == barbero.id,
            Cita.fecha >= datetime.now(),
            Cita.fecha <= datetime.combine(week_from_now, time.max)
        )
        titulo_filtro = "Próximas 7 días"
    else:  # todas
        citas_query = Cita.query.filter(Cita.barbero_id == barbero.id)
        titulo_filtro = "Todas las Citas"
    
    # Obtener las citas con límite
    citas_mostrar = citas_query.order_by(Cita.fecha.asc()).limit(15).all()
    total_citas = citas_query.count()
    
    return render_template('barbero/dashboard.html', 
                          title=f'Panel de {barbero.nombre}',
                          barbero=barbero,
                          citas_hoy=citas_hoy,
                          citas_pendientes=citas_pendientes,
                          citas_mostrar=citas_mostrar,
                          total_citas=total_citas,
                          titulo_filtro=titulo_filtro,
                          servicios_disponibles=servicios_disponibles,
                          fecha_hoy=today.strftime('%Y-%m-%d'))

@bp.route('/citas')
@login_required
def mis_citas():
    """Lista todas las citas del barbero"""
    if not hasattr(current_user, 'tiene_acceso_web') or not current_user.tiene_acceso_web:
        abort(403)
    
    barbero = current_user
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Fecha actual para filtro por defecto
    today = date.today()
    
    # Filtros
    estado = request.args.get('estado', '')
    
    # Verificar si se solicitó mostrar todas las citas (sin filtro por defecto)
    mostrar_todo = request.args.get('mostrar_todo', '0') == '1'
    
    # Si no hay filtros de fecha y no se solicitó mostrar todo, usar la fecha actual por defecto
    if not mostrar_todo and not any([request.args.get('fecha_inicio'), request.args.get('fecha_fin'), 
                request.args.get('estado'), request.args.get('page')]):
        fecha_inicio = today.strftime('%Y-%m-%d')
        fecha_fin = today.strftime('%Y-%m-%d')
    else:
        fecha_inicio = request.args.get('fecha_inicio', '')
        fecha_fin = request.args.get('fecha_fin', '')
    
    # Construir query
    query = Cita.query.filter_by(barbero_id=barbero.id)
    
    if estado:
        query = query.filter(Cita.estado == estado)
    
    if fecha_inicio:
        try:
            fecha_inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d')
            query = query.filter(Cita.fecha >= fecha_inicio_dt)
        except ValueError:
            flash('Formato de fecha de inicio inválido.', 'warning')
    
    if fecha_fin:
        try:
            fecha_fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d')
            fecha_fin_dt = fecha_fin_dt.replace(hour=23, minute=59, second=59)
            query = query.filter(Cita.fecha <= fecha_fin_dt)
        except ValueError:
            flash('Formato de fecha de fin inválido.', 'warning')
    
    citas = query.order_by(Cita.fecha.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('barbero/mis_citas.html',
                          title='Mis Citas',
                          citas=citas,
                          barbero=barbero,
                          estado=estado,
                          fecha_inicio=fecha_inicio,
                          fecha_fin=fecha_fin,
                          mostrar_todo=mostrar_todo)

@bp.route('/citas/nueva', methods=['GET', 'POST'])
@login_required
def nueva_cita():
    """Crear una nueva cita para el barbero"""
    if not hasattr(current_user, 'tiene_acceso_web') or not current_user.tiene_acceso_web:
        abort(403)
    
    barbero = current_user
    form = CitaForm()
    
    # Preseleccionar el barbero actual
    form.barbero_id.data = barbero.id
    form.barbero_id.render_kw = {'disabled': True}
    
    if form.validate_on_submit():
        try:
            # Buscar o crear cliente
            cliente = Cliente.query.filter_by(email=form.cliente_email.data).first()
            if not cliente:
                cliente = Cliente(
                    nombre=form.cliente_nombre.data,
                    email=form.cliente_email.data
                )
                db.session.add(cliente)
                db.session.flush()  # Para obtener el ID
            
            # Crear la cita
            nueva_cita = Cita(
                cliente_id=cliente.id,
                barbero_id=barbero.id,
                servicio_id=form.servicio_id.data,
                estado=form.estado.data
            )
            
            # La fecha se establecerá mediante JavaScript/AJAX
            # Por ahora crear sin fecha específica
            db.session.add(nueva_cita)
            db.session.commit()
            
            flash('Cita creada correctamente.', 'success')
            return redirect(url_for('barbero.mis_citas'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear la cita: {str(e)}', 'danger')
    
    return render_template('barbero/nueva_cita.html',
                          title='Nueva Cita',
                          form=form,
                          barbero=barbero)

@bp.route('/citas/<int:cita_id>/actualizar', methods=['POST'])
@login_required
def actualizar_estado_cita(cita_id):
    """Actualizar el estado de una cita"""
    if not hasattr(current_user, 'tiene_acceso_web') or not current_user.tiene_acceso_web:
        abort(403)
    
    barbero = current_user
    cita = Cita.query.filter_by(id=cita_id, barbero_id=barbero.id).first_or_404()
    
    nuevo_estado = request.form.get('estado')
    estados_validos = ['pendiente', 'confirmada', 'cancelada', 'completada']
    
    if nuevo_estado in estados_validos:
        cita.estado = nuevo_estado
        db.session.commit()
        flash(f'Estado de la cita actualizado a: {nuevo_estado.title()}', 'success')
    else:
        flash('Estado inválido.', 'danger')
    
    # Redirigir de vuelta al dashboard si vino de ahí
    if request.referrer and 'dashboard' in request.referrer:
        return redirect(url_for('barbero.dashboard'))
    return redirect(url_for('barbero.mis_citas'))

@bp.route('/citas/<int:cita_id>/eliminar', methods=['POST'])
@login_required
def eliminar_cita(cita_id):
    """Eliminar una cita del barbero"""
    if not hasattr(current_user, 'tiene_acceso_web') or not current_user.tiene_acceso_web:
        abort(403)
    
    barbero = current_user
    cita = Cita.query.filter_by(id=cita_id, barbero_id=barbero.id).first_or_404()
    
    try:
        cliente_nombre = cita.cliente.nombre if cita.cliente else 'Cliente desconocido'
        db.session.delete(cita)
        db.session.commit()
        flash(f'Cita con {cliente_nombre} eliminada correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar la cita: {str(e)}', 'danger')
    
    # Redirigir de vuelta al dashboard si vino de ahí
    if request.referrer and 'dashboard' in request.referrer:
        return redirect(url_for('barbero.dashboard'))
    return redirect(url_for('barbero.mis_citas'))

@bp.route('/horarios', methods=['GET', 'POST'])
@login_required
def ver_horarios():
    """Ver los horarios del barbero y gestionar bloqueos temporales"""
    if not hasattr(current_user, 'tiene_acceso_web') or not current_user.tiene_acceso_web:
        abort(403)
    
    from app.admin.forms import BloqueoHorarioForm
    from app.models.barbero import BloqueoHorario
    from datetime import datetime, time, date, timedelta
    
    barbero = current_user
    form = BloqueoHorarioForm()
    
    # Procesar el formulario de bloqueo
    if form.validate_on_submit():
        try:
            # Convertir fecha y horas a objetos date y time
            fecha = datetime.strptime(form.fecha.data, '%Y-%m-%d').date()
            hora_inicio = datetime.strptime(form.hora_inicio.data, '%H:%M').time()
            hora_fin = datetime.strptime(form.hora_fin.data, '%H:%M').time()
            
            # Crear el bloqueo
            bloqueo, mensaje = barbero.crear_bloqueo_horario(
                fecha=fecha,
                hora_inicio=hora_inicio,
                hora_fin=hora_fin,
                motivo=form.motivo.data
            )
            
            if bloqueo:
                flash('Bloqueo de horario creado correctamente.', 'success')
            else:
                flash(mensaje, 'danger')
                
        except ValueError as e:
            flash(f'Error en el formato de fecha u hora: {str(e)}', 'danger')
        except Exception as e:
            flash(f'Error al crear bloqueo: {str(e)}', 'danger')
            
        return redirect(url_for('barbero.ver_horarios'))
    
    # Obtener disponibilidades regulares
    from app.models.barbero import DisponibilidadBarbero
    disponibilidades = barbero.disponibilidad.filter_by(activo=True).order_by(
        DisponibilidadBarbero.dia_semana,
        DisponibilidadBarbero.hora_inicio
    ).all()
    
    # Obtener bloqueos futuros
    hoy = date.today()
    try:
        bloqueos_futuros = barbero.get_bloqueos_horario(fecha_inicio=hoy)
    except Exception as e:
        print(f"Error al obtener bloqueos: {str(e)}")
        bloqueos_futuros = []
    
    # Eliminar un bloqueo si se solicita
    if request.args.get('eliminar_bloqueo'):
        try:
            bloqueo_id = request.args.get('eliminar_bloqueo')
            exito, mensaje = barbero.eliminar_bloqueo_horario(bloqueo_id)
            if exito:
                flash('Bloqueo eliminado correctamente.', 'success')
            else:
                flash(mensaje, 'danger')
        except Exception as e:
            flash(f'Error al eliminar bloqueo: {str(e)}', 'danger')
        return redirect(url_for('barbero.ver_horarios'))
    
    dias_semana = {0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves', 4: 'Viernes', 5: 'Sábado', 6: 'Domingo'}
    
    return render_template('barbero/horarios.html',
                          title='Mis Horarios',
                          barbero=barbero,
                          disponibilidades=disponibilidades,
                          dias_semana=dias_semana,
                          form=form,
                          bloqueos_futuros=bloqueos_futuros,
                          fecha_hoy=hoy.strftime('%Y-%m-%d'))

@bp.route('/perfil')
@login_required
def perfil():
    """Ver perfil del barbero"""
    if not hasattr(current_user, 'tiene_acceso_web') or not current_user.tiene_acceso_web:
        abort(403)
    
    barbero = current_user
    
    # Estadísticas del mes actual
    today = date.today()
    first_day_month = today.replace(day=1)
    next_month = (first_day_month + timedelta(days=32)).replace(day=1)
    
    stats = {
        'completadas': Cita.query.filter(
            Cita.barbero_id == barbero.id,
            Cita.estado == 'completada',
            Cita.fecha >= datetime.combine(first_day_month, time.min),
            Cita.fecha < datetime.combine(next_month, time.min)
        ).count(),
        'pendientes': Cita.query.filter(
            Cita.barbero_id == barbero.id,
            Cita.estado == 'pendiente',
            Cita.fecha >= datetime.now()
        ).count(),
        'canceladas': Cita.query.filter(
            Cita.barbero_id == barbero.id,
            Cita.estado == 'cancelada',
            Cita.fecha >= datetime.combine(first_day_month, time.min),
            Cita.fecha < datetime.combine(next_month, time.min)
        ).count()
    }
    
    # Obtener horarios de trabajo
    from app.models.barbero import DisponibilidadBarbero
    disponibilidades = DisponibilidadBarbero.query.filter_by(
        barbero_id=barbero.id, activo=True
    ).order_by(DisponibilidadBarbero.dia_semana, DisponibilidadBarbero.hora_inicio).all()
    
    return render_template('barbero/perfil.html',
                          title='Mi Perfil',
                          barbero=barbero,
                          stats=stats,
                          disponibilidades=disponibilidades)

# Ruta API para obtener horarios disponibles (registrada en el blueprint principal)
@bp.route('/horarios-disponibles/<int:barbero_id>')
@login_required
def api_horarios_disponibles(barbero_id):
    """API para obtener horarios disponibles de un barbero en una fecha específica"""
    if not hasattr(current_user, 'tiene_acceso_web') or not current_user.tiene_acceso_web:
        return {'success': False, 'error': 'No autorizado'}, 403
    
    # Solo permitir consultar horarios del barbero actual
    if current_user.id != barbero_id:
        return {'success': False, 'error': 'No autorizado'}, 403
    
    fecha_str = request.args.get('fecha')
    if not fecha_str:
        return {'success': False, 'error': 'Fecha requerida'}, 400
    
    try:
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        dia_semana = fecha.weekday()  # 0=Lunes, 6=Domingo
        
        # Obtener disponibilidades del barbero para ese día
        from app.models.barbero import DisponibilidadBarbero
        disponibilidades = DisponibilidadBarbero.query.filter_by(
            barbero_id=barbero_id,
            dia_semana=dia_semana,
            activo=True
        ).all()
        
        horarios_disponibles = []
        
        for disponibilidad in disponibilidades:
            # Generar slots de tiempo cada 30 minutos
            hora_actual = disponibilidad.hora_inicio
            while hora_actual < disponibilidad.hora_fin:
                # Verificar si este slot está ocupado
                fecha_hora_completa = datetime.combine(fecha, hora_actual)
                
                cita_existente = Cita.query.filter_by(
                    barbero_id=barbero_id,
                    fecha=fecha_hora_completa
                ).first()
                
                if not cita_existente:
                    horarios_disponibles.append({
                        'hora': hora_actual.strftime('%H:%M'),
                        'disponible': True
                    })
                
                # Añadir 30 minutos
                hora_actual = (datetime.combine(fecha, hora_actual) + timedelta(minutes=30)).time()
        
        return {
            'success': True,
            'horarios': horarios_disponibles
        }
        
    except ValueError:
        return {'success': False, 'error': 'Formato de fecha inválido'}, 400
    except Exception as e:
        return {'success': False, 'error': str(e)}, 500