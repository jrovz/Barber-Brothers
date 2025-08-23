"""
Rutas del panel de administración de Barber Brothers.

Este módulo registra todas las rutas del Blueprint `admin` (`bp`) que dan soporte
al backoffice. Incluye autenticación de administradores, panel con métricas y
CRUDs de entidades principales del sistema, además de utilidades de depuración.

Contenido principal
- Autenticación y sesión:
  - `GET/POST /login`: Inicio de sesión para administradores. Valida credenciales
    con el modelo `User` y verifica `is_admin()` antes de permitir acceso.
  - `GET /logout`: Cierra la sesión del usuario actual.
  - Todas las rutas administrativas aplican `@login_required` y verifican
    `current_user.is_admin()`; de lo contrario devuelven 403.

- Dashboard (`GET /`):
  - Verifica conectividad a la base de datos.
  - Métricas: conteos de productos, barberos, clientes; mensajes no leídos;
    citas de hoy/semana/mes; servicios más solicitados; productos con bajo stock.
  - Estadísticas por barbero: cálculo aproximado de ocupación a partir de su
    disponibilidad semanal.

- Productos:
  - `GET/POST /productos`: Alta de productos con subida de imagen (archivo o URL).
  - `GET/POST /productos/editar/<id>`: Edición de datos, cantidad y portada.
  - `POST /productos/eliminar/<id>`: Eliminación segura con manejo de errores.

- Categorías:
  - `GET/POST /categorias`, `GET/POST /categorias/editar/<id>`,
    `POST /categorias/eliminar/<id>` con validaciones (no eliminar si tiene
    productos asociados).

- Barberos y disponibilidad:
  - `GET/POST /barberos`, `GET/POST /barberos/editar/<id>`,
    `POST /barberos/eliminar/<id>` (no eliminar si tiene citas).
  - `GET/POST /barberos/<barbero_id>/disponibilidad`: Alta de tramos horarios,
    detectando solapamientos por día de la semana.
  - `POST /barberos/disponibilidad/eliminar/<disp_id>`: Eliminación de un tramo.
  - `POST /barberos/<barbero_id>/disponibilidad/crear_predeterminada`: Genera un
    horario estándar de trabajo.

- Servicios y galería de imágenes:
  - `GET/POST /servicios`: Alta con imagen principal y carga múltiple de
    imágenes a la galería (`ServicioImagen`).
  - `GET/POST /servicios/editar/<id>`: Edición, agregando imágenes nuevas al
    final de la secuencia de orden.
  - `POST /servicios/imagen/<imagen_id>/eliminar`: "Soft delete" (marca como
    inactiva) y responde en JSON.
  - `POST /servicios/eliminar/<id>`: Eliminación segura (evita si hay citas).

- Citas:
  - `GET/POST /citas`: Creación validando fecha y hora. Vincula cliente por
    email (crea si no existe) y actualiza teléfono/nombre cuando corresponde.
  - `GET/POST /citas/editar/<id>`: Maneja cambio de email con casos de conflicto
    y creación de nuevo cliente cuando aplica.
  - `POST /citas/eliminar/<id>`: Eliminación con control de errores.
  - Filtros por `estado` y por `fecha` (día completo) vía query string.

- Clientes y segmentación:
  - `GET/POST /clientes`: Listado con filtros por `segmento` y orden por nombre,
    total de visitas o última visita. Incluye métricas agregadas por segmento.
  - `GET /clientes/<id>`: Detalle del cliente con historial de citas y gasto.
  - `POST /clientes/actualizar-segmentos`: Recalcula segmentación.

- Sliders (portada):
  - `GET/POST /sliders`: Alta de slides tipo `imagen` o `instagram`.
  - `GET/POST /sliders/editar/<id>`: Edición, intercambio de tipo y limpieza de
    campos incompatibles (por ejemplo, eliminar imagen si pasa a Instagram).
  - `POST /sliders/eliminar/<id>`: Borra el registro y elimina la imagen física
    si existía.

- Depuración:
  - `GET /debug/images`: Vista para auditar imágenes disponibles y rutas de
    subida.

Dependencias y utilidades
- Formularios: `LoginForm`, `ProductoForm`, `BarberoForm`, `ServicioForm`,
  `CitaForm`, `DisponibilidadForm`, `CategoriaForm`, `ClienteFilterForm`.
- Modelos: `Producto`, `User`, `Mensaje`, `Cliente`, `Cita`, `Servicio`,
  `Barbero`, `DisponibilidadBarbero`, `Categoria`, `Slider`, `ServicioImagen`.
- Subida de archivos: `save_image(file, carpeta)` guarda en
  `UPLOAD_FOLDER/<carpeta>` y retorna la ruta accesible.
- Transacciones: todas las operaciones de escritura usan `db.session.commit()` y
  `db.session.rollback()` ante excepciones, mostrando mensajes con `flash`.
- Respuestas: HTML (render de plantillas en `templates/admin/*.html`) y JSON en
  endpoints específicos de API interna (por ejemplo, eliminar imagen de
  servicio).
- Seguridad: cada ruta administrativa verifica explícitamente `is_admin()` para
  evitar accesos indebidos, devolviendo 403 en caso contrario.

Notas de mantenimiento
- Si cambian los modelos, revisar las importaciones y relaciones usadas.
- El cálculo de ocupación en el dashboard es estimado y mejorable si se dispone
  de duración real por cita y ventanas exactas de agenda.
- Asegurar que `UPLOAD_FOLDER` esté configurado y exista para evitar errores de
  E/S al gestionar imágenes.
"""
from flask import render_template, request, redirect, url_for, flash, abort, current_app, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app.admin import bp
# Import models
from app.models.producto import Producto
from app.models.admin import User # Assuming User model is in admin.py
from app.models.cliente import Mensaje, Cliente, Cita # Assuming Mensaje, Cliente, Cita are in cliente.py
from app.models.servicio import Servicio
from app.models.barbero import Barbero, DisponibilidadBarbero
from app.models.categoria import Categoria # Correctly import Categoria
try:
    from app.models.slider import Slider
except Exception as e:
    print(f"Warning: No se pudo importar el modelo Slider: {e}")
    Slider = None
from app import db
# Import forms
from .forms import LoginForm, ProductoForm, BarberoForm, ServicioForm, CitaForm, DisponibilidadForm, CategoriaForm, ClienteFilterForm
from .slider_forms import SliderForm
from app.admin.utils import save_image # Assuming you have this utility
from datetime import datetime, time, timedelta
import logging # For better logging, especially in edit_barbero
import os # For file operations

# Configure logging for specific routes if needed
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    logger.info("Acceso a la ruta de login de administrador")
    
    try:
        if current_user.is_authenticated:
            logger.info(f"Usuario ya autenticado: {current_user.username}")
            if hasattr(current_user, 'is_admin') and current_user.is_admin():
                logger.info(f"Usuario confirmado como admin: {current_user.username}")
                return redirect(url_for('admin.dashboard'))
            else:
                logger.warning(f"Usuario autenticado pero no es admin: {current_user.username}")
    except Exception as e:
        logger.error(f"Error al verificar usuario autenticado: {str(e)}", exc_info=True)

    form = LoginForm()
    if form.validate_on_submit():
        logger.info(f"Intento de inicio de sesión con usuario: {form.username.data}")
        try:
            user = User.query.filter_by(username=form.username.data).first()
            if user is None:
                logger.warning(f"Usuario no encontrado: {form.username.data}")
                flash('Usuario o contraseña inválidos.', 'danger')
                return redirect(url_for('admin.login'))
            
            logger.info(f"Usuario encontrado: {user.username}, rol: {user.role}")
            
            if not user.check_password(form.password.data):
                logger.warning(f"Contraseña incorrecta para usuario: {user.username}")
                flash('Usuario o contraseña inválidos.', 'danger')
                return redirect(url_for('admin.login'))
            
            if not hasattr(user, 'is_admin'):
                logger.error(f"El usuario {user.username} no tiene el atributo is_admin")
                flash('Acceso denegado. No tienes permisos de administrador.', 'danger')
                return redirect(url_for('public.home'))
                
            if not user.is_admin():
                logger.warning(f"Usuario no es admin: {user.username}, rol: {user.role}")
                flash('Acceso denegado. No tienes permisos de administrador.', 'danger')
                return redirect(url_for('public.home'))

            login_user(user, remember=form.remember_me.data)
            logger.info(f"Inicio de sesión exitoso para admin: {user.username}")
            flash('Inicio de sesión exitoso.', 'success')
            
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('admin.dashboard')
            return redirect(next_page)
            
        except Exception as e:
            logger.error(f"Error durante el proceso de autenticación: {str(e)}", exc_info=True)
            flash('Ocurrió un error durante la autenticación. Por favor, inténtalo de nuevo.', 'danger')
            return redirect(url_for('admin.login'))
        
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

    try:
        # Verificar conexión a la base de datos primero
        from sqlalchemy.sql import text
        from app import db
        db.session.execute(text("SELECT 1"))
        print("Admin dashboard: Conexión a la base de datos verificada correctamente")
        
        # Estadísticas básicas
        product_count = Producto.query.count()
        barber_count = Barbero.query.count()
        unread_messages_count = Mensaje.query.filter_by(leido=False).count()
        recent_messages = Mensaje.query.order_by(Mensaje.creado.desc()).limit(5).all()
    
        # Estadísticas de clientes y segmentación
        cliente_count = Cliente.query.count()
        nuevos_clientes = Cliente.query.filter_by(segmento='nuevo').count()
        clientes_recurrentes = Cliente.query.filter_by(segmento='recurrente').count()
        clientes_vip = Cliente.query.filter_by(segmento='vip').count()
        clientes_inactivos = Cliente.query.filter_by(segmento='inactivo').count()
    except Exception as e:
        print(f"Error al consultar datos para el dashboard: {str(e)}")
        # Inicializar con valores predeterminados en caso de error
        product_count = 0
        barber_count = 0
        unread_messages_count = 0
        recent_messages = []
        cliente_count = 0
        nuevos_clientes = 0
        clientes_recurrentes = 0
        clientes_vip = 0
        clientes_inactivos = 0
    
    # Citas y ocupación
    today = datetime.today().date()
    tomorrow = today + timedelta(days=1)
    this_month_start = today.replace(day=1)
    next_month_start = (this_month_start + timedelta(days=32)).replace(day=1)
    
    # Citas próximas
    proximas_citas = Cita.query.filter(
        Cita.fecha >= datetime.now(),
        Cita.fecha <= datetime.now() + timedelta(days=7),
        Cita.estado != 'cancelada'
    ).order_by(Cita.fecha).limit(10).all()
    
    # Citas expiradas (para notificación)
    citas_expiradas = Cita.query.filter(
        Cita.estado == 'expirada'
    ).order_by(Cita.fecha.desc()).limit(10).all()
    
    # Citas pendientes de confirmación
    citas_pendientes = Cita.query.filter_by(estado='pendiente_confirmacion').count()
    
    # Ejecutar limpieza de citas expiradas (aquellas pendientes que pasaron el tiempo límite)
    try:
        citas_limpiadas = Cita.limpiar_citas_expiradas()
        if citas_limpiadas > 0:
            flash(f'Se han detectado {citas_limpiadas} citas expiradas sin confirmar', 'warning')
    except Exception as e:
        current_app.logger.error(f"Error al limpiar citas expiradas: {str(e)}")
        print(f"Error al limpiar citas expiradas: {str(e)}")
    
    # Citas de hoy
    citas_hoy = Cita.query.filter(
        Cita.fecha >= datetime.combine(today, time.min),
        Cita.fecha < datetime.combine(tomorrow, time.min)
    ).count()
    
    # Citas del mes
    citas_mes = Cita.query.filter(
        Cita.fecha >= datetime.combine(this_month_start, time.min),
        Cita.fecha < datetime.combine(next_month_start, time.min)
    ).count()
    
    # Estadísticas por barbero
    barberos = Barbero.query.all()
    stats_barberos = []
    
    for barbero in barberos:
        # Citas asignadas a este barbero este mes
        citas_barbero = Cita.query.filter(
            Cita.barbero_id == barbero.id,
            Cita.fecha >= datetime.combine(this_month_start, time.min),
            Cita.fecha < datetime.combine(next_month_start, time.min)
        ).count()
        
        # Calculando tasa de ocupación basada en disponibilidad
        disponibilidad = DisponibilidadBarbero.query.filter_by(barbero_id=barbero.id, activo=True).all()
        horas_disponibles = 0
        for disp in disponibilidad:
            # Calculamos horas disponibles por semana
            inicio = disp.hora_inicio
            fin = disp.hora_fin
            delta = (datetime.combine(today, fin) - datetime.combine(today, inicio))
            horas_disponibles += delta.total_seconds() / 3600  # horas por día
        
        # La tasa sería un estimado (mejorable con datos reales de duración de citas)
        tasa_ocupacion = round((citas_barbero / (horas_disponibles * 4)) * 100) if horas_disponibles > 0 else 0
        
        stats_barberos.append({
            'id': barbero.id,
            'nombre': barbero.nombre,
            'citas': citas_barbero,
            'ocupacion': min(tasa_ocupacion, 100)  # Limitar a 100% máximo
        })
    
    # Servicios más solicitados
    top_servicios = db.session.query(
        Servicio.nombre, 
        db.func.count(Cita.id).label('total')
    ).join(Cita, Servicio.id == Cita.servicio_id)\
     .group_by(Servicio.nombre)\
     .order_by(db.desc('total'))\
     .limit(5).all()
      # Productos con bajo stock
    productos_bajo_stock = Producto.query.filter(Producto.cantidad <= 5).order_by(Producto.cantidad).all()
    
    # Datos para gráfico de segmentación de clientes
    segmentos_data = {
        'labels': ['Nuevos', 'Ocasionales', 'Recurrentes', 'VIP', 'Inactivos'],
        'data': [
            nuevos_clientes,
            Cliente.query.filter_by(segmento='ocasional').count(),
            clientes_recurrentes,
            clientes_vip,
            clientes_inactivos
        ]
    }

    # NUEVO: Usar configuraciones personalizadas del administrador
    from flask import g
    from app.middleware.admin_middleware import AdminDashboardOptimizer
    from app.utils.admin_cookies import AdminCookieManager
    
    # Obtener configuraciones personalizadas (cargadas por middleware)
    dashboard_config = getattr(g, 'admin_dashboard_config', AdminCookieManager.DEFAULT_DASHBOARD_CONFIG.copy())
    metrics_config = getattr(g, 'admin_metrics_config', {})
    interface_settings = getattr(g, 'admin_interface_settings', AdminCookieManager.DEFAULT_INTERFACE_SETTINGS.copy())
    productivity_metrics = getattr(g, 'admin_productivity_metrics', {})
    trending_data = getattr(g, 'admin_trending_data', {})
    
    # Personalizar widgets según configuración
    widgets_to_show = AdminDashboardOptimizer.get_personalized_widgets(dashboard_config)
    smart_kpis = AdminDashboardOptimizer.get_smart_kpis(metrics_config)
    
    # Configurar período de métricas según preferencias
    metrics_period = dashboard_config.get('metrics_period', 'month')
    
    return render_template(
        'admin/dashboard.html', 
        title='Dashboard Admin',
        product_count=product_count,
        barber_count=barber_count,
        cliente_count=cliente_count,
        nuevos_clientes=nuevos_clientes,
        clientes_recurrentes=clientes_recurrentes,
        clientes_vip=clientes_vip,
        segmentos_data=segmentos_data,
        unread_messages_count=unread_messages_count,
        recent_messages=recent_messages,
        proximas_citas=proximas_citas,
        citas_expiradas=citas_expiradas,
        citas_pendientes=citas_pendientes,
        citas_hoy=citas_hoy,
        citas_mes=citas_mes,
        stats_barberos=stats_barberos,
        top_servicios=top_servicios,
        productos_bajo_stock=productos_bajo_stock,
        # NUEVO: Variables de personalización
        dashboard_config=dashboard_config,
        metrics_config=metrics_config,
        interface_settings=interface_settings,
        widgets_to_show=widgets_to_show,
        smart_kpis=smart_kpis,
        metrics_period=metrics_period,
        productivity_metrics=productivity_metrics,
        trending_data=trending_data
    )

# --- Gestión de Productos (CRUD) ---
@bp.route('/productos', methods=['GET', 'POST'])
@login_required
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
def editar_barbero(id):
    if not hasattr(current_user, 'is_admin') or not current_user.is_admin():
        abort(403)
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
@bp.route('/servicios', methods=['GET', 'POST'])
@login_required
def gestionar_servicios():
    if not hasattr(current_user, 'is_admin') or not current_user.is_admin():
        abort(403)
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


@bp.route('/citas', methods=['GET', 'POST'])
@login_required
def gestionar_citas():
    if not hasattr(current_user, 'is_admin') or not current_user.is_admin():
        abort(403)
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
def editar_cita(id):
    if not hasattr(current_user, 'is_admin') or not current_user.is_admin():
        abort(403)
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

# --- Gestión de Clientes y Segmentación ---
@bp.route('/clientes', methods=['GET', 'POST'])
@login_required
def gestionar_clientes():
    if not hasattr(current_user, 'is_admin') or not current_user.is_admin():
        abort(403)
    
    form = ClienteFilterForm()
    
    # Si se envía el formulario, redirigir con los filtros como parámetros de URL
    if form.validate_on_submit():
        return redirect(url_for('admin.gestionar_clientes', 
                              segmento=form.segmento.data, 
                              ordenar_por=form.ordenar_por.data))
    
    # Obtener filtros de la URL
    segmento_filtro = request.args.get('segmento', '')
    ordenar_por = request.args.get('ordenar_por', 'nombre')
    
    # Preseleccionar los valores del formulario
    form.segmento.data = segmento_filtro
    form.ordenar_por.data = ordenar_por
    
    # Configurar la consulta base
    query = Cliente.query
    
    # Aplicar filtros si existen
    if segmento_filtro:
        query = query.filter_by(segmento=segmento_filtro)
    
    # Aplicar ordenamiento
    if ordenar_por == 'visitas':
        query = query.order_by(Cliente.total_visitas.desc())
    elif ordenar_por == 'ultima_visita':
        query = query.order_by(Cliente.ultima_visita.desc())
    else:  # Por defecto, ordenar por nombre
        query = query.order_by(Cliente.nombre)
    
    # Ejecutar consulta
    clientes = query.all()
    
    # Estadísticas de segmentación
    stats = {
        'total': Cliente.query.count(),
        'nuevos': Cliente.query.filter_by(segmento='nuevo').count(),
        'ocasionales': Cliente.query.filter_by(segmento='ocasional').count(),
        'recurrentes': Cliente.query.filter_by(segmento='recurrente').count(),
        'vip': Cliente.query.filter_by(segmento='vip').count(),
        'inactivos': Cliente.query.filter_by(segmento='inactivo').count(),
    }
    
    return render_template(
        'admin/clientes.html',
        title='Gestionar Clientes',
        clientes=clientes,
        stats=stats,
        segmento_actual=segmento_filtro,
        ordenar_por=ordenar_por,
        form=form
    )

@bp.route('/clientes/<int:id>')
@login_required
def detalle_cliente(id):
    if not hasattr(current_user, 'is_admin') or not current_user.is_admin():
        abort(403)
        
    cliente = Cliente.query.get_or_404(id)
    
    # Obtener historial de citas
    citas = Cita.query.filter_by(cliente_id=cliente.id).order_by(Cita.fecha.desc()).all()
    
    # Calcular métricas
    total_gastado = sum(cita.servicio_rel.precio for cita in citas if cita.servicio_rel and cita.estado == 'completada')
    promedio_gasto = total_gastado / len(citas) if citas else 0
    
    return render_template(
        'admin/detalle_cliente.html',
        title=f'Cliente: {cliente.nombre}',
        cliente=cliente,
        citas=citas,
        total_gastado=total_gastado,
        promedio_gasto=promedio_gasto
    )

@bp.route('/clientes/actualizar-segmentos', methods=['POST'])
@login_required
def actualizar_segmentos():
    if not hasattr(current_user, 'is_admin') or not current_user.is_admin():
        abort(403)
        
    # Obtener todos los clientes
    clientes = Cliente.query.all()
    count = 0
    
    try:
        for cliente in clientes:
            if cliente.clasificar_segmento() != cliente.segmento:
                count += 1
        
        db.session.commit()
        flash(f'Segmentación actualizada para {count} clientes.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al actualizar segmentación: {str(e)}', 'danger')
        
    return redirect(url_for('admin.gestionar_clientes'))

# ================================
# GESTIÓN DE SLIDERS
# ================================

@bp.route('/sliders', methods=['GET', 'POST'])
@login_required
def gestionar_sliders():
    if not hasattr(current_user, 'is_admin') or not current_user.is_admin():
        abort(403)
    
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
def editar_slider(id):
    if not hasattr(current_user, 'is_admin') or not current_user.is_admin():
        abort(403)
    
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
def eliminar_slider(id):
    if not hasattr(current_user, 'is_admin') or not current_user.is_admin():
        abort(403)
    
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

@bp.route('/api/save-dashboard-config', methods=['POST'])
@login_required
def save_dashboard_config():
    """Guarda la configuración del dashboard en cookies"""
    if not hasattr(current_user, 'is_admin') or not current_user.is_admin():
        abort(403)
    
    try:
        from flask import request, make_response, jsonify
        from app.utils.admin_cookies import AdminCookieManager
        
        config_data = request.get_json()
        if not config_data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        response = make_response(jsonify({'success': True, 'message': 'Configuración guardada'}))
        AdminCookieManager.save_dashboard_config(response, config_data)
        
        logger.info(f"Dashboard config saved for admin {current_user.id}")
        return response
        
    except Exception as e:
        logger.error(f"Error saving dashboard config: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/save-interface-setting', methods=['POST'])
@login_required
def save_interface_setting():
    """Guarda una configuración específica de interfaz"""
    if not hasattr(current_user, 'is_admin') or not current_user.is_admin():
        abort(403)
    
    try:
        from flask import request, make_response, jsonify
        from app.utils.admin_cookies import AdminCookieManager
        
        setting_data = request.get_json()
        if not setting_data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        response = make_response(jsonify({'success': True, 'message': 'Configuración guardada'}))
        
        # Guardar cada configuración
        for key, value in setting_data.items():
            AdminCookieManager.save_interface_setting(response, key, value)
        
        return response
        
    except Exception as e:
        logger.error(f"Error saving interface setting: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/refresh-metrics', methods=['POST'])
@login_required
def refresh_metrics():
    """Actualiza las métricas del dashboard"""
    if not hasattr(current_user, 'is_admin') or not current_user.is_admin():
        abort(403)
    
    try:
        from app.utils.admin_cookies import AdminMetricsCalculator
        
        metrics = AdminMetricsCalculator.calculate_productivity_metrics()
        trending = AdminMetricsCalculator.get_trending_data()
        
        return jsonify({
            'success': True,
            'metrics': metrics,
            'trending': trending,
            'updated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error refreshing metrics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/get-quick-access', methods=['GET'])
@login_required
def get_quick_access():
    """Obtiene datos de acceso rápido"""
    if not hasattr(current_user, 'is_admin') or not current_user.is_admin():
        abort(403)
    
    try:
        from app.utils.admin_cookies import AdminCookieManager
        
        quick_access = AdminCookieManager.get_quick_access_data()
        
        return jsonify({
            'success': True,
            'data': quick_access
        })
        
    except Exception as e:
        logger.error(f"Error getting quick access data: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500