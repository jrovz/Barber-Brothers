# filepath: app/admin/routes.py
from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import login_user, logout_user, login_required, current_user
from app.admin import bp
from app.models import Producto, Barbero, User, Mensaje, Servicio # Añadir Servicio
from app import db
from .forms import LoginForm, ProductoForm, BarberoForm, ServicioForm # Añadir ServicioForm

# --- Autenticación ---

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
    if form.validate_on_submit(): # Procesa el formulario de añadir/editar
        # Determinar si es una edición (si se envía un ID oculto, por ejemplo)
        # O manejar la edición en una ruta separada (recomendado)
        # --- Lógica para Añadir ---
        nuevo_producto = Producto(
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            precio=form.precio.data,
            imagen_url=form.imagen_url.data,
            categoria=form.categoria.data
        )
        db.session.add(nuevo_producto)
        try:
            db.session.commit()
            flash('Producto añadido correctamente.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al añadir producto: {e}', 'danger')
        return redirect(url_for('admin.gestionar_productos')) # Redirigir para evitar reenvío de formulario

    # --- Lógica para Mostrar (GET) ---
    productos_lista = Producto.query.order_by(Producto.creado.desc()).all()
    # Pasar el formulario vacío para el 'modal' o sección de añadir
    return render_template("admin/productos.html", title="Gestionar Productos", productos=productos_lista, form=form)

@bp.route('/productos/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_producto(id):
    if not current_user.is_admin():
        abort(403)
    producto = Producto.query.get_or_404(id)
    form = ProductoForm(obj=producto) # Pre-rellenar formulario con datos del producto

    if form.validate_on_submit():
        # Actualizar los campos del objeto producto existente
        form.populate_obj(producto) 
        try:
            db.session.commit()
            flash('Producto actualizado correctamente.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar producto: {e}', 'danger')
        return redirect(url_for('admin.gestionar_productos'))

    # Mostrar el formulario de edición
    return render_template('editar_producto.html', title="Editar Producto", form=form, producto=producto)

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

# @bp.route('/productos/eliminar/<int:id>', methods=['POST']) # Usar POST para eliminar
# @login_required
# def eliminar_producto(id):
#     if not current_user.is_admin():
#         abort(403)
#     producto = Producto.query.get_or_404(id)
    
#     # --- INICIO: Modificación Temporal para Depuración ---
#     # Comenta o elimina el try...except para ver el error real
#     # try:
#     db.session.delete(producto)
#     db.session.commit() # Si esto falla, ahora Flask mostrará el error completo
#     flash('Producto eliminado correctamente.', 'success')
#     # except Exception as e:
#     #     db.session.rollback()
#     #     flash(f'Error al eliminar producto: {e}', 'danger')
#     # --- FIN: Modificación Temporal ---
        
#     return redirect(url_for('admin.gestionar_productos'))


# --- Gestión de Barberos (CRUD) ---

@bp.route('/barberos', methods=['GET', 'POST'])
@login_required
def gestionar_barberos():
    if not current_user.is_admin():
        abort(403)
        
    form = BarberoForm()
    if form.validate_on_submit():
        nuevo_barbero = Barbero()
        form.populate_obj(nuevo_barbero) # Rellena el objeto desde el form
        db.session.add(nuevo_barbero)
        try:
            db.session.commit()
            flash('Barbero añadido correctamente.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al añadir barbero: {e}', 'danger')
        return redirect(url_for('admin.gestionar_barberos'))

    barberos_lista = Barbero.query.order_by(Barbero.nombre).all()
    return render_template("barberos.html", title="Gestionar Barberos", barberos=barberos_lista, form=form)

@bp.route('/barberos/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_barbero(id):
    if not current_user.is_admin():
        abort(403)
    barbero = Barbero.query.get_or_404(id)
    form = BarberoForm(obj=barbero)

    if form.validate_on_submit():
        form.populate_obj(barbero)
        try:
            db.session.commit()
            flash('Barbero actualizado correctamente.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar barbero: {e}', 'danger')
        return redirect(url_for('admin.gestionar_barberos'))

    return render_template('editar_barbero.html', title="Editar Barbero", form=form, barbero=barbero)

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
        # Lógica para Añadir
        nuevo_servicio = Servicio(
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            precio=form.precio.data,
            duracion_estimada=form.duracion_estimada.data,
            activo=form.activo.data
        )
        db.session.add(nuevo_servicio)
        try:
            db.session.commit()
            flash('Servicio añadido correctamente.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al añadir servicio: {e}', 'danger')
        return redirect(url_for('admin.gestionar_servicios')) # Redirigir siempre tras POST exitoso

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
    # Pasar obj=servicio en GET para pre-rellenar, no en POST
    form = ServicioForm(obj=servicio if request.method == 'GET' else None) 

    if form.validate_on_submit():
        # Actualizar los campos del objeto servicio existente
        form.populate_obj(servicio) 
        try:
            db.session.commit()
            flash('Servicio actualizado correctamente.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar servicio: {e}', 'danger')
        return redirect(url_for('admin.gestionar_servicios'))

    # Mostrar el formulario de edición (en GET o si POST falla validación)
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