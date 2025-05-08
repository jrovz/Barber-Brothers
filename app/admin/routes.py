from flask import render_template, request, redirect, url_for, flash, abort, current_app, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app.admin import bp
# Import models
from app.models.producto import Producto
from app.models.admin import User # Assuming User model is in admin.py as per your context
from app.models.cliente import Mensaje, Cliente, Cita # Assuming Mensaje, Cliente, Cita are in cliente.py
from app.models.servicio import Servicio
from app.models.barbero import Barbero, DisponibilidadBarbero
from app.models.categoria import Categoria # Correctly import Categoria
from app import db
# Import forms
from .forms import LoginForm, ProductoForm, BarberoForm, ServicioForm, CitaForm, DisponibilidadForm, CategoriaForm
from app.admin.utils import save_image # Assuming you have this utility
from datetime import datetime, time
import logging # For better logging, especially in edit_barbero

# Configure logging for specific routes if needed
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated and hasattr(current_user, 'is_admin') and current_user.is_admin():
        return redirect(url_for('admin.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Usuario o contraseña inválidos.', 'danger')
            return redirect(url_for('admin.login'))
        
        if not hasattr(user, 'is_admin') or not user.is_admin():
            flash('Acceso denegado. No tienes permisos de administrador.', 'danger')
            return redirect(url_for('public.home'))

        login_user(user, remember=form.remember_me.data)
        flash('Inicio de sesión exitoso.', 'success')
        
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('admin.dashboard')
        return redirect(next_page)
        
    return render_template('login.html', title='Iniciar Sesión Admin', form=form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión.', 'info')
    return redirect(url_for('public.home'))

@bp.route('/')
@login_required
def dashboard():
    if not hasattr(current_user, 'is_admin') or not current_user.is_admin():
        abort(403)

    product_count = Producto.query.count()
    barber_count = Barbero.query.count()
    unread_messages_count = Mensaje.query.filter_by(leido=False).count()
    recent_messages = Mensaje.query.order_by(Mensaje.creado.desc()).limit(5).all()
    # Add more stats as needed, e.g., upcoming appointments
    upcoming_citas_count = Cita.query.filter(Cita.fecha >= datetime.utcnow(), Cita.estado != 'cancelada').count()


    return render_template(
        'admin/dashboard.html', 
        title='Dashboard Admin',
        product_count=product_count,
        barber_count=barber_count,
        unread_messages_count=unread_messages_count,
        recent_messages=recent_messages,
        upcoming_citas_count=upcoming_citas_count
    )

# --- Gestión de Productos (CRUD) ---
@bp.route('/productos', methods=['GET', 'POST'])
@login_required
def gestionar_productos():
    if not hasattr(current_user, 'is_admin') or not current_user.is_admin():
        abort(403)
        
    form = ProductoForm()
    if form.validate_on_submit():
        imagen_url = None
        if form.imagen_file.data:
            imagen_url = save_image(form.imagen_file.data, 'productos')
        elif form.imagen_url.data: # Use URL if file not provided
            imagen_url = form.imagen_url.data
        
        selected_categoria_id = form.categoria_id.data
        if selected_categoria_id == 0: # 'Sin Categoría'
            selected_categoria_id = None

        nuevo_producto = Producto(
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            precio=form.precio.data,
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
def editar_producto(id):
    if not hasattr(current_user, 'is_admin') or not current_user.is_admin():
        abort(403)
    producto = Producto.query.get_or_404(id)
    form = ProductoForm(obj=producto if request.method == 'GET' else None)
    
    if form.validate_on_submit():
        producto.nombre = form.nombre.data
        producto.descripcion = form.descripcion.data
        producto.precio = form.precio.data
        
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
    
    # Pre-fill form for GET request if not using obj=producto for some fields
    if request.method == 'GET':
        form.nombre.data = producto.nombre
        form.descripcion.data = producto.descripcion
        form.precio.data = producto.precio
        form.categoria_id.data = producto.categoria_id if producto.categoria_id is not None else 0
        form.imagen_url.data = producto.imagen_url

    return render_template('admin/editar_producto.html', 
                           title="Editar Producto", 
                           form=form, 
                           producto=producto)

@bp.route('/productos/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar_producto(id):
    if not hasattr(current_user, 'is_admin') or not current_user.is_admin():
        abort(403)
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
@bp.route('/categorias', methods=['GET', 'POST'])
@login_required
def gestionar_categorias():
    if not hasattr(current_user, 'is_admin') or not current_user.is_admin():
        abort(403)
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
def editar_categoria(id):
    if not hasattr(current_user, 'is_admin') or not current_user.is_admin():
        abort(403)
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
def eliminar_categoria(id):
    if not hasattr(current_user, 'is_admin') or not current_user.is_admin():
        abort(403)
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
@bp.route('/barberos', methods=['GET', 'POST'])
@login_required
def gestionar_barberos():
    if not hasattr(current_user, 'is_admin') or not current_user.is_admin():
        abort(403)
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
    if not hasattr(current_user, 'is_admin') or not current_user.is_admin():
        abort(403)
    barbero = Barbero.query.get_or_404(id)
    # Pass obj=barbero to pre-fill the form on GET
    form = BarberoForm(obj=barbero if request.method == 'GET' else None)
    
    if form.validate_on_submit():
        barbero.nombre = form.nombre.data
        barbero.especialidad = form.especialidad.data
        barbero.descripcion = form.descripcion.data
        barbero.activo = form.activo.data
        
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
        # form.imagen_url.data = barbero.imagen_url # If you have this field

    return render_template('admin/editar_barbero.html', 
                          title="Editar Barbero", 
                          form=form, 
                          barbero=barbero)

@bp.route('/barberos/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar_barbero(id):
    if not hasattr(current_user, 'is_admin') or not current_user.is_admin():
        abort(403)
    barbero = Barbero.query.get_or_404(id)
    # Add check for associated Citas if necessary
    if Cita.query.filter_by(barbero_id=id).first():
         flash(f'No se puede eliminar el barbero {barbero.nombre} porque tiene citas asociadas.', 'danger')
         return redirect(url_for('admin.gestionar_barberos'))
    try:
        # Delete associated availabilities first
        DisponibilidadBarbero.query.filter_by(barbero_id=id).delete()
        db.session.delete(barbero)
        db.session.commit()
        flash('Barbero y su disponibilidad eliminados correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar barbero: {str(e)}', 'danger')
    return redirect(url_for('admin.gestionar_barberos'))

# --- Gestión de Disponibilidad de Barberos ---
@bp.route('/barberos/<int:barbero_id>/disponibilidad', methods=['GET', 'POST'])
@login_required
def gestionar_disponibilidad(barbero_id):
    if not hasattr(current_user, 'is_admin') or not current_user.is_admin():
        abort(403)
    barbero = Barbero.query.get_or_404(barbero_id)
    form = DisponibilidadForm()

    if form.validate_on_submit():
        try:
            hora_inicio = datetime.strptime(form.hora_inicio.data, '%H:%M').time()
            hora_fin = datetime.strptime(form.hora_fin.data, '%H:%M').time()

            if hora_fin <= hora_inicio:
                flash('La hora de fin debe ser posterior a la hora de inicio.', 'danger')
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
def eliminar_disponibilidad(disp_id):
    if not hasattr(current_user, 'is_admin') or not current_user.is_admin():
        abort(403)
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
def crear_disponibilidad_predeterminada(barbero_id):
    if not hasattr(current_user, 'is_admin') or not current_user.is_admin():
        abort(403)
    barbero = Barbero.query.get_or_404(barbero_id)
    horario_estandar = {
        0: [(time(9, 0), time(13, 0)), (time(14, 0), time(18, 0))], # Lunes
        1: [(time(9, 0), time(13, 0)), (time(14, 0), time(18, 0))], # Martes
        2: [(time(9, 0), time(13, 0)), (time(14, 0), time(18, 0))], # Miércoles
        3: [(time(9, 0), time(13, 0)), (time(14, 0), time(18, 0))], # Jueves
        4: [(time(9, 0), time(13, 0)), (time(14, 0), time(18, 0))], # Viernes
        5: [(time(9, 0), time(14, 0))]                             # Sábado
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
@bp.route('/servicios', methods=['GET', 'POST'])
@login_required
def gestionar_servicios():
    if not hasattr(current_user, 'is_admin') or not current_user.is_admin():
        abort(403)
    form = ServicioForm()
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
            imagen_url=imagen_url
        )
        db.session.add(nuevo_servicio)
        try:
            db.session.commit()
            flash('Servicio añadido correctamente.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al añadir servicio: {str(e)}', 'danger')
        return redirect(url_for('admin.gestionar_servicios'))

    servicios_lista = Servicio.query.order_by(Servicio.nombre).all()
    return render_template("admin/servicios.html", 
                           title="Gestionar Servicios", 
                           servicios=servicios_lista, 
                           form=form)

@bp.route('/servicios/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_servicio(id):
    if not hasattr(current_user, 'is_admin') or not current_user.is_admin():
        abort(403)
    servicio = Servicio.query.get_or_404(id)
    form = ServicioForm(obj=servicio if request.method == 'GET' else None)

    if form.validate_on_submit():
        servicio.nombre = form.nombre.data
        servicio.descripcion = form.descripcion.data
        servicio.precio = form.precio.data
        servicio.duracion_estimada = form.duracion_estimada.data
        servicio.activo = form.activo.data
        
        if form.imagen_file.data:
            imagen_path = save_image(form.imagen_file.data, 'servicios')
            if imagen_path:
                servicio.imagen_url = imagen_path
        elif form.imagen_url.data and form.imagen_url.data != servicio.imagen_url:
            servicio.imagen_url = form.imagen_url.data
        
        try:
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
        form.duracion_estimada.data = form.duracion_estimada
        form.activo.data = servicio.activo
        form.imagen_url.data = servicio.imagen_url

    return render_template('admin/editar_servicio.html', 
                           title="Editar Servicio", 
                           form=form, 
                           servicio=servicio)

@bp.route('/servicios/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar_servicio(id):
    if not hasattr(current_user, 'is_admin') or not current_user.is_admin():
        abort(403)
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

# --- Gestión de Citas (CRUD) ---
@bp.route('/citas', methods=['GET', 'POST'])
@login_required
def gestionar_citas():
    if not hasattr(current_user, 'is_admin') or not current_user.is_admin():
        abort(403)
    form = CitaForm()
    # Populate choices dynamically
    form.cliente_id.choices = [(c.id, c.nombre) for c in Cliente.query.order_by(Cliente.nombre).all()]
    form.barbero_id.choices = [(b.id, b.nombre) for b in Barbero.query.filter_by(activo=True).order_by(Barbero.nombre).all()]
    # Assuming CitaForm's servicio field stores service ID and needs choices like (s.id, s.nombre)
    # If it stores service name, then (s.nombre, s.nombre) is fine.
    # For consistency, let's assume it stores service_id
    form.servicio_id.choices = [(s.id, s.nombre) for s in Servicio.query.filter_by(activo=True).order_by(Servicio.nombre).all()]


    if form.validate_on_submit():
        # Client handling: if CitaForm has a text field for new client name,
        # you'd create client here. Assuming cliente_id is a SelectField of existing clients.
        cliente = Cliente.query.get(form.cliente_id.data)
        if not cliente:
            flash('Cliente seleccionado no válido.', 'danger')
            # Re-render form with choices
            citas_lista = Cita.query.order_by(Cita.fecha.desc()).all()
            return render_template("admin/citas.html", title="Gestionar Citas", citas=citas_lista, form=form, datetime=datetime)

        nueva_cita = Cita(
            cliente_id=cliente.id,
            barbero_id=form.barbero_id.data,
            servicio_id=form.servicio_id.data, # Use servicio_id
            fecha=form.fecha.data,
            estado=form.estado.data,
            notas=form.notas.data if hasattr(form, 'notas') else None # Optional notes
        )
        db.session.add(nueva_cita)
        try:
            db.session.commit()
            flash('Cita creada correctamente.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al guardar la cita: {str(e)}', 'danger')
        return redirect(url_for('admin.gestionar_citas'))

    citas_lista = Cita.query.order_by(Cita.fecha.desc()).all()
    return render_template("admin/citas.html", title="Gestionar Citas", citas=citas_lista, form=form, datetime=datetime)

@bp.route('/citas/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_cita(id):
    if not hasattr(current_user, 'is_admin') or not current_user.is_admin():
        abort(403)
    cita = Cita.query.get_or_404(id)
    form = CitaForm(obj=cita if request.method == 'GET' else None)
    
    # Populate choices dynamically
    form.cliente_id.choices = [(c.id, c.nombre) for c in Cliente.query.order_by(Cliente.nombre).all()]
    form.barbero_id.choices = [(b.id, b.nombre) for b in Barbero.query.filter_by(activo=True).order_by(Barbero.nombre).all()]
    form.servicio_id.choices = [(s.id, s.nombre) for s in Servicio.query.filter_by(activo=True).order_by(Servicio.nombre).all()]


    if form.validate_on_submit():
        cita.cliente_id = form.cliente_id.data
        cita.barbero_id = form.barbero_id.data
        cita.servicio_id = form.servicio_id.data # Use servicio_id
        cita.fecha = form.fecha.data
        cita.estado = form.estado.data
        cita.notas = form.notas.data if hasattr(form, 'notas') else cita.notas # Optional notes

        try:
            db.session.commit()
            flash('Cita actualizada correctamente.', 'success')
            return redirect(url_for('admin.gestionar_citas'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar la cita: {str(e)}', 'danger')

    if request.method == 'GET': # Ensure form is pre-filled
        form.cliente_id.data = cita.cliente_id
        form.barbero_id.data = cita.barbero_id
        form.servicio_id.data = cita.servicio_id
        form.fecha.data = cita.fecha
        form.estado.data = cita.estado
        if hasattr(form, 'notas'):
            form.notas.data = cita.notas


    return render_template('admin/editar_cita.html', title="Editar Cita", form=form, cita=cita, datetime=datetime)    

@bp.route('/citas/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar_cita(id):
    if not hasattr(current_user, 'is_admin') or not current_user.is_admin():
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

# --- Debug Images ---
@bp.route('/debug/images')
@login_required
def debug_images():
    if not hasattr(current_user, 'is_admin') or not current_user.is_admin():
        abort(403)
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