from flask import render_template, request, redirect, url_for, flash, abort, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app.admin import bp
from app.models import Producto, Barbero, User, Mensaje, Servicio, Cliente, Cita # Añadir Cliente y Cita
from app import db
from .forms import LoginForm, ProductoForm, BarberoForm, ServicioForm, CitaForm # Añadir ServicioForm
from app.admin.utils import save_image
import datetime
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated and current_user.is_admin():
        return redirect(url_for('admin.dashboard')) # Redirigir si ya está logueado como admin

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Usuario o contraseña inválidos.', 'danger')
            return redirect(url_for('admin.login'))
        
        # Verificar si es admin
        if not user.is_admin():
            flash('Acceso denegado. No tienes permisos de administrador.', 'danger')
            return redirect(url_for('public.home')) # O a donde quieras redirigir a no-admins

        login_user(user, remember=form.remember_me.data)
        flash('Inicio de sesión exitoso.', 'success')
        
        # Redirigir a la página solicitada originalmente o al dashboard
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('admin.dashboard') # Ruta del dashboard principal
        return redirect(next_page)
        
    return render_template('login.html', title='Iniciar Sesión Admin', form=form)

@bp.route('/logout')
@login_required # Solo usuarios logueados pueden desloguearse
def logout():
    logout_user()
    flash('Has cerrado sesión.', 'info')
    return redirect(url_for('public.home'))

# --- Dashboard (Ejemplo) ---

@bp.route('/') # Ruta raíz del admin blueprint (/admin/)
@login_required
def dashboard():
    if not current_user.is_admin():
        abort(403) # Prohibido si no es admin

    # --- Obtener Datos para el Dashboard ---
    
    # A. Estadísticas Clave
    product_count = Producto.query.count()
    barber_count = Barbero.query.count()
    # Asumiendo que el modelo Mensaje tiene un campo booleano 'leido'
    unread_messages_count = Mensaje.query.filter_by(leido=False).count() 

    # B. Mensajes Recientes (Ej: los 5 más nuevos)
    # Asumiendo que Mensaje tiene un campo 'creado' (DateTime) y relación con Cliente
    recent_messages = Mensaje.query.order_by(Mensaje.creado.desc()).limit(5).all()

    # --- Renderizar Plantilla con los Datos ---
    return render_template(
        'dashboard.html', 
        title='Dashboard Admin',
        # Pasar datos a la plantilla
        product_count=product_count,
        barber_count=barber_count,
        unread_messages_count=unread_messages_count,
        recent_messages=recent_messages
    )

# --- Gestión de Productos (CRUD) ---

@bp.route('/productos', methods=['GET', 'POST'])
@login_required
def gestionar_productos():
    if not current_user.is_admin():
        abort(403)
        
    form = ProductoForm()
    if form.validate_on_submit():
        # Procesar la imagen
        imagen_url = None
        
        # Primero intentar con el archivo subido
        if form.imagen_file.data:
            imagen_url = save_image(form.imagen_file.data, 'productos')
            
        # Si no hay archivo, usar la URL si se proporcionó
        if not imagen_url and form.imagen_url.data:
            imagen_url = form.imagen_url.data
        
        nuevo_producto = Producto(
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            precio=form.precio.data,
            categoria=form.categoria.data,
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
    
    # Resto del código para GET...
    productos_lista = Producto.query.order_by(Producto.creado.desc()).all()
    return render_template("admin/productos.html", 
                           title="Gestionar Productos", 
                           productos=productos_lista, 
                           form=form)
@bp.route('/productos/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_producto(id):
    producto = Producto.query.get_or_404(id)
    form = ProductoForm(obj=producto if request.method == 'GET' else None)
    
    if form.validate_on_submit():
        # Actualizar los datos básicos
        producto.nombre = form.nombre.data
        producto.descripcion = form.descripcion.data
        producto.precio = form.precio.data
        producto.categoria = form.categoria.data
        
        # Procesar imagen solo si se subió una nueva
        if form.imagen_file.data:
            nueva_imagen = save_image(form.imagen_file.data, 'productos')
            if nueva_imagen:
                producto.imagen_url = nueva_imagen
        # Solo actualizar URL si hay una nueva y no se subió archivo
        elif form.imagen_url.data and form.imagen_url.data != producto.imagen_url:
            producto.imagen_url = form.imagen_url.data
        
        try:
            db.session.commit()
            flash('Producto actualizado correctamente.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar producto: {str(e)}', 'danger')
            
        return redirect(url_for('admin.gestionar_productos'))
    
    # Para GET, prellenar el formulario
    if request.method == 'GET':
        form.nombre.data = producto.nombre
        form.descripcion.data = producto.descripcion
        form.precio.data = producto.precio
        form.categoria.data = producto.categoria
        form.imagen_url.data = producto.imagen_url
        # No prellenamos imagen_file porque es un campo de carga

    return render_template('admin/editar_producto.html', 
                           title="Editar Producto", 
                           form=form, 
                           producto=producto)

@bp.route('/productos/eliminar/<int:id>', methods=['POST']) # Usar POST para eliminar
@login_required
def eliminar_producto(id):
    if not current_user.is_admin():
        abort(403)
    producto = Producto.query.get_or_404(id)
    try:
        db.session.delete(producto)
        db.session.commit()
        flash('Producto eliminado correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar producto: {e}', 'danger')
    return redirect(url_for('admin.gestionar_productos'))

@bp.route('/barberos', methods=['GET', 'POST'])
@login_required
def gestionar_barberos():
    
    form = BarberoForm()
    if form.validate_on_submit():
        # Procesar la imagen
        imagen_url = None
        
        # Primero intentar con el archivo subido
        if form.imagen_file.data:
            imagen_url = save_image(form.imagen_file.data, 'barberos')
            
        # Si no hay archivo, usar la URL si se proporcionó
        if not imagen_url and form.imagen_url.data:
            imagen_url = form.imagen_url.data
        
        nuevo_barbero = Barbero(
            nombre=form.nombre.data,
            especialidad=form.especialidad.data,
            descripcion=form.descripcion.data,
            activo=form.activo.data,
            imagen_url=imagen_url
        )
        
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
def editar_barbero(id):
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger('barberos_route')
    
    barbero = Barbero.query.get_or_404(id)
    form = BarberoForm()
    
    if form.validate_on_submit():
        # Actualizar datos básicos
        barbero.nombre = form.nombre.data
        barbero.especialidad = form.especialidad.data
        barbero.descripcion = form.descripcion.data
        barbero.activo = form.activo.data
        
        # Manejar la imagen
        old_imagen_url = barbero.imagen_url
        logger.info(f"URL de imagen anterior: {old_imagen_url}")
        
        if form.imagen_file.data:
            logger.info(f"Procesando nueva imagen subida: {form.imagen_file.data.filename}")
            imagen_url = save_image(form.imagen_file.data, 'barberos')
            
            if imagen_url:
                logger.info(f"Nueva URL de imagen: {imagen_url}")
                barbero.imagen_url = imagen_url
            else:
                logger.warning("No se pudo guardar la nueva imagen")
        elif form.imagen_url.data:
            logger.info(f"Usando URL proporcionada: {form.imagen_url.data}")
            barbero.imagen_url = form.imagen_url.data
        
        try:
            db.session.commit()
            logger.info(f"Barbero actualizado. URL final: {barbero.imagen_url}")
            flash('Barbero actualizado correctamente', 'success')
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error al actualizar barbero: {str(e)}")
            flash(f'Error al actualizar barbero: {str(e)}', 'danger')
        
        return redirect(url_for('admin.gestionar_barberos'))
        
    
    return render_template('admin/editar_barbero.html', 
                          title="Editar Barbero", 
                          form=form, 
                          barbero=barbero)

@bp.route('/barberos/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar_barbero(id):
    if not current_user.is_admin():
        abort(403)
    barbero = Barbero.query.get_or_404(id)
    try:
        db.session.delete(barbero)
        db.session.commit()
        flash('Barbero eliminado correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar barbero: {e}', 'danger')
    return redirect(url_for('admin.gestionar_barberos'))

# --- Gestión de Servicios (CRUD) ---

@bp.route('/servicios', methods=['GET', 'POST'])
@login_required
def gestionar_servicios():
    if not current_user.is_admin():
        abort(403)
    
    form = ServicioForm()
    if form.validate_on_submit():
        # Crear objeto servicio
        nuevo_servicio = Servicio(
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            precio=form.precio.data,
            duracion_estimada=form.duracion_estimada.data,
            activo=form.activo.data
        )
        
        # Procesar la imagen cargada o la URL
        if form.imagen_file.data:
            imagen_path = save_image(form.imagen_file.data, 'servicios')
            if imagen_path:
                nuevo_servicio.imagen_url = imagen_path
        elif form.imagen_url.data:
            nuevo_servicio.imagen_url = form.imagen_url.data
            
        db.session.add(nuevo_servicio)
        try:
            db.session.commit()
            flash('Servicio añadido correctamente.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al añadir servicio: {e}', 'danger')
        return redirect(url_for('admin.gestionar_servicios'))

    # Lógica para Mostrar (GET)
    servicios_lista = Servicio.query.order_by(Servicio.nombre).all()
    return render_template("admin/servicios.html", 
                           title="Gestionar Servicios", 
                           servicios=servicios_lista, 
                           form=form)

@bp.route('/servicios/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_servicio(id):
    if not current_user.is_admin():
        abort(403)
    servicio = Servicio.query.get_or_404(id)
    form = ServicioForm(obj=servicio if request.method == 'GET' else None)

    if form.validate_on_submit():
        # Actualizar datos de texto
        servicio.nombre = form.nombre.data
        servicio.descripcion = form.descripcion.data
        servicio.precio = form.precio.data
        servicio.duracion_estimada = form.duracion_estimada.data
        servicio.activo = form.activo.data
        
        # Procesar imagen
        if form.imagen_file.data:
            # Si se sube un nuevo archivo, guardarlo y actualizar la URL
            imagen_path = save_image(form.imagen_file.data, 'servicios')
            if imagen_path:
                servicio.imagen_url = imagen_path
        elif form.imagen_url.data and form.imagen_url.data != servicio.imagen_url:
            # Si la URL es diferente a la actual, actualizarla
            servicio.imagen_url = form.imagen_url.data
        
        # Si ninguno de los campos está completo, se mantiene la imagen actual
        
        try:
            db.session.commit()
            flash('Servicio actualizado correctamente.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar servicio: {e}', 'danger')
        return redirect(url_for('admin.gestionar_servicios'))

    # Para GET, ya está prellenado con obj=servicio

    return render_template('admin/editar_servicio.html', 
                           title="Editar Servicio", 
                           form=form, 
                           servicio=servicio)

@bp.route('/servicios/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar_servicio(id):
    if not current_user.is_admin():
        abort(403)
    servicio = Servicio.query.get_or_404(id)
    try:
        db.session.delete(servicio)
        db.session.commit()
        flash('Servicio eliminado correctamente.', 'success')
    except Exception as e:
        # Podría fallar si hay dependencias futuras (ej. citas asociadas)
        db.session.rollback()
        flash(f'Error al eliminar servicio: {e}', 'danger')
    return redirect(url_for('admin.gestionar_servicios'))

@bp.route('/citas', methods=['GET', 'POST'])
@login_required
def gestionar_citas():
    if not current_user.is_admin():
        abort(403)
    
    form = CitaForm()
    # Poblar opciones dinámicas
    form.cliente_id.choices = [(c.id, c.nombre) for c in Cliente.query.all()]
    form.barbero_id.choices = [(b.id, b.nombre) for b in Barbero.query.filter_by(activo=True).all()]
    form.servicio.choices = [(s.nombre, s.nombre) for s in Servicio.query.all()]
    
    if form.validate_on_submit():
        resultado, mensaje_o_cita = Cita.crear_cita(
            cliente_id=form.cliente_id.data,
            barbero_id=form.barbero_id.data,
            fecha=form.fecha.data,
            servicio=form.servicio.data
        )
        
        if resultado:
            flash('Cita creada correctamente.', 'success')
            return redirect(url_for('admin.gestionar_citas'))
        else:
            flash(f'Error al crear cita: {mensaje_o_cita}', 'danger')
    
    # Mostrar citas filtradas o todas
    filtro_estado = request.args.get('estado', '')
    filtro_fecha = request.args.get('fecha', '')
    
    query = Cita.query
    if filtro_estado:
        query = query.filter_by(estado=filtro_estado)
    if filtro_fecha:
        try:
            fecha = datetime.strptime(filtro_fecha, '%Y-%m-%d')
            query = query.filter(db.func.date(Cita.fecha) == fecha.date())
        except ValueError:
            pass
            
    citas = query.order_by(Cita.fecha.desc()).all()
    
    return render_template('admin/citas.html', 
                          title="Gestionar Citas", 
                          form=form, 
                          citas=citas)

@bp.route('/calendario', methods=['GET'])
@login_required
def calendario_citas():
    if not current_user.is_admin():
        abort(403)
    
    # Obtener parámetro de mes (por defecto mes actual)
    import calendar
    from datetime import datetime, timedelta
    
    today = datetime.today()
    month = request.args.get('month', today.month, type=int)
    year = request.args.get('year', today.year, type=int)
    
    # Validar mes y año
    if month < 1 or month > 12:
        month = today.month
    
    # Obtener todas las citas del mes
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = datetime(year, month + 1, 1) - timedelta(days=1)
    
    citas = Cita.query.filter(
        Cita.fecha >= start_date,
        Cita.fecha <= end_date.replace(hour=23, minute=59, second=59)
    ).all()
    
    # Organizar citas por día
    citas_por_dia = {}
    for cita in citas:
        day = cita.fecha.day
        if day not in citas_por_dia:
            citas_por_dia[day] = []
        citas_por_dia[day].append(cita)
    
    # Crear matriz del calendario
    cal = calendar.monthcalendar(year, month)
    
    return render_template('admin/calendario.html',
                          title="Calendario de Citas",
                          calendar=cal,
                          month=month,
                          year=year,
                          citas_por_dia=citas_por_dia,
                          month_name=calendar.month_name[month])

@bp.route('/citas/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_cita(id):
    if not current_user.is_admin():
        abort(403)
        
    cita = Cita.query.get_or_404(id)
    form = CitaForm(obj=cita if request.method == 'GET' else None)
    
    # Poblar opciones dinámicas
    form.cliente_id.choices = [(c.id, c.nombre) for c in Cliente.query.all()]
    form.barbero_id.choices = [(b.id, b.nombre) for b in Barbero.query.filter_by(activo=True).all()]
    form.servicio.choices = [(s.nombre, s.nombre) for s in Servicio.query.all()]
    
    if form.validate_on_submit():
        cita.cliente_id = form.cliente_id.data
        cita.barbero_id = form.barbero_id.data
        cita.fecha = form.fecha.data
        cita.servicio = form.servicio.data
        cita.estado = form.estado.data
        
        try:
            db.session.commit()
            flash('Cita actualizada correctamente.', 'success')
            return redirect(url_for('admin.gestionar_citas'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar cita: {str(e)}', 'danger')
    
    return render_template('admin/editar_cita.html',
                          title="Editar Cita",
                          form=form,
                          cita=cita)

@bp.route('/citas/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar_cita(id):
    if not current_user.is_admin():
        abort(403)
        
    cita = Cita.query.get_or_404(id)
    try:
        db.session.delete(cita)
        db.session.commit()
        flash('Cita eliminada correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar cita: {str(e)}', 'danger')
        
    return redirect(url_for('admin.gestionar_citas'))

@bp.route('/debug/images')
@login_required
def debug_images():
    if not current_user.is_admin():
        abort(403)
        
    barberos = Barbero.query.all()
    productos = Producto.query.all()
    servicios = Servicio.query.all()
    
    app_path = current_app.root_path
    upload_path = current_app.config['UPLOAD_FOLDER']
    
    return render_template(
        'admin/debug_images.html',
        barberos=barberos,
        productos=productos,
        servicios=servicios,
        app_path=app_path,
        upload_path=upload_path
    )