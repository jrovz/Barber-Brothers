"""
Rutas públicas del sitio Barber Brothers.

Este módulo define las vistas y endpoints del Blueprint `public` orientados a la
parte pública del sitio: página principal, productos, servicios, checkout de
tienda, contacto, y APIs de soporte para disponibilidad y agenda de citas.

Resumen de rutas y responsabilidades
- Home (`GET /`):
  - Carga sliders activos (si el modelo `Slider` está disponible) en orden.
  - Obtiene productos destacados (últimos por fecha de creación).
  - Lista barberos activos y servicios activos (ordenados por `orden`, `nombre`).
  - Genera un rango de fechas próximas para el calendario de cita.
  - Renderiza `templates/public/Home.html`.

- About (`GET /about`):
  - Página informativa estática (`about.html`).

- Contacto (`GET/POST /contacto`):
  - Muestra formulario de contacto (GET) y persiste `Cliente` y `Mensaje` (POST).
  - Realiza `flush()` para obtener IDs y `commit()` con manejo básico de errores.
  - Renderiza `contacto.html` en GET; retorna estado 201 en POST exitoso.

- Productos (`GET /productos`):
  - Construye `categorias_con_productos` agrupando productos activos por
    `Categoria` para la vista pública.
  - Renderiza `templates/public/productos.html`.

- Checkout y confirmación de pedido:
  - `GET/POST /checkout`: Usa `CheckoutForm` para datos del cliente y carrito
    (JSON en `cart_data`). Crea `Pedido` y `PedidoItem`, calcula totales y
    confirma transacción. Renderiza `templates/public/checkout.html`.
  - `GET /confirmacion-pedido/<pedido_id>`: Muestra `templates/public/confirmacion_pedido.html`.

- Servicios (`GET /servicios`):
  - Verifica conectividad y lista solo `Servicio` activos.
  - Renderiza `templates/public/servicios.html`.

- API: Servicio (`GET /api/servicio/<servicio_id>`):
  - Retorna JSON con datos de un servicio activo, precio formateado con
    `utils.format_cop`, imagen principal y galería (`get_imagenes_activas`).

- API: Disponibilidad (`GET /api/disponibilidad/<barbero_id>/<fecha>`):
  - Calcula horarios disponibles para un barbero y fecha dada (YYYY-MM-DD),
    considerando la duración del servicio (`get_duracion_minutos`) y su
    disponibilidad horaria. Devuelve lista de strings de horas y mensaje.

- API: Agendar Cita (`POST /api/agendar-cita`):
  - Valida datos obligatorios, calcula rango horario de la nueva cita y verifica
    solapamientos con citas existentes del día (confirmadas o pendientes).
  - Crea/actualiza `Cliente`, crea `Cita` con duración del servicio y estado
    inicial `pendiente_confirmacion`. Genera token y envía correo de
    confirmación (`send_appointment_confirmation_email`). Responde JSON.

- Confirmar Cita (`GET /confirmar-cita/<token>`):
  - Verifica token y expira/valida. Doble verificación de conflicto: si el
    slot ya está tomado, marca la cita como cancelada por conflicto; si no, la
    confirma y persiste. Renderiza `templates/public/confirmation_status.html`.

Dependencias clave
- Modelos: `Producto`, `Categoria`, `Servicio`, `Barbero`, `DisponibilidadBarbero`,
  `Cliente`, `Mensaje`, `Cita`, `Pedido`, `PedidoItem`, `Slider` (opcional).
- Formularios: `CheckoutForm` (en `app/public/forms.py`).
- Utilidades: `send_appointment_confirmation_email`, `utils.format_cop`.
- Plantillas: `public/Home.html`, `public/productos.html`, `public/servicios.html`,
  `public/checkout.html`, `public/confirmacion_pedido.html`,
  `public/confirmation_status.html`, `contacto.html`, `about.html`.

Seguridad y notas
- Rutas públicas sin autenticación. La integridad se asegura con validaciones de
  servidor y verificación de solapamientos al agendar.
- El modelo `Slider` es opcional: si no está disponible, se procede con lista
  vacía. Existen logs/prints de depuración en `home()` y APIs para diagnóstico.
"""
from flask import render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from app.public import bp
from app.models.producto import Producto
from app.models.cliente import Cliente, Mensaje, Cita
from app.models.servicio import Servicio # Asegúrate de que este modelo existe
from app.models.barbero import Barbero, DisponibilidadBarbero
from app.models.categoria import Categoria # <<< IMPORT Categoria MODEL
from app.models.pedido import Pedido  # Necesario para confirmacion_pedido
try:
    from app.models.slider import Slider
except Exception as e:
    print(f"Warning: No se pudo importar el modelo Slider: {e}")
    Slider = None
from app.models.email import send_appointment_confirmation_email # Importar la función de envío
from app import db
from datetime import datetime, timedelta, time
from flask import send_from_directory

@bp.route('/')
def home():
    # Inicializar todas las variables al principio para evitar errores
    featured_products = []
    barberos = []
    servicios = []
    fechas_disponibles = []
    sliders = []
    
    # NUEVO: Cargar personalización comercial
    from app.utils.business_cookies import BusinessCookieManager, ConversionOptimizer
    from app.utils.cart_optimizer import CartOptimizer
    from flask import g
    
    personalization_data = getattr(g, 'personalization', BusinessCookieManager.get_personalization_data())
    smart_recommendations = getattr(g, 'smart_recommendations', ConversionOptimizer.get_smart_recommendations())
    conversion_probability = getattr(g, 'conversion_probability', BusinessCookieManager.calculate_conversion_probability())
    
    try:
        # Obtener sliders activos ordenados por orden
        if Slider is not None:
            sliders = Slider.get_active_slides_ordered()
        else:
            print("Warning: Modelo Slider no disponible, usando lista vacía")
            sliders = []
        
        # Productos destacados
        # CORREGIDO: Usar 'creado' en lugar de 'created_at'
        featured_products = Producto.query.order_by(Producto.creado.desc()).limit(3).all() 
        
        # --- START REFINED DEBUG ---
        print("--- DEBUG: Querying ALL Barberos ---")
        all_barberos = Barbero.query.all()
        print(f"Total barberos found (before filter): {len(all_barberos)}")
        for b in all_barberos:
            # Imprimir valor y tipo del campo activo
            print(f"  ID: {b.id}, Nombre: {b.nombre}, Activo (DB value): {b.activo}, Type: {type(b.activo)}")
            
        print("--- DEBUG: Querying ACTIVE Barberos ---")
        barberos = Barbero.query.filter_by(activo=True).all()
        print(f"Barberos found with filter_by(activo=True): {len(barberos)}")
        for b in barberos:
            print(f"  Active Barbero ID: {b.id}, Nombre: {b.nombre}")

        print("--- DEBUG: Querying ALL Servicios ---")
        all_servicios = Servicio.query.all()
        print(f"Total servicios found (before filter): {len(all_servicios)}")
        for s in all_servicios:
             # Imprimir valor y tipo del campo activo
             print(f"  ID: {s.id}, Nombre: {s.nombre}, Activo (DB value): {s.activo}, Type: {type(s.activo)}")

        print("--- DEBUG: Querying ACTIVE Servicios ---")
        servicios = Servicio.query.filter_by(activo=True).order_by(Servicio.orden.asc(), Servicio.nombre.asc()).all()
        print(f"Servicios found with filter_by(activo=True): {len(servicios)}")
        for s in servicios:
            print(f"  Active Servicio ID: {s.id}, Nombre: {s.nombre}")
        # --- END REFINED DEBUG ---
        
        # Generar fechas para el calendario
        hoy = datetime.now().date()
        fechas_disponibles = [hoy + timedelta(days=i) for i in range(14)]
        
    except Exception as e:
        print(f"Error in home(): {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Final check before rendering
    print(f"--- FINAL CHECK before render ---")
    print(f"Barberos to template: {len(barberos)}")
    print(f"Servicios to template: {len(servicios)}")
    
    # Eliminar los prints de depuración anteriores si aún existen
    # print(f"Enviando a template: {len(barberos)} barberos, {len(servicios)} servicios")
    # print("--- DEBUG HOME ---")
    # ... (eliminar bucles for anteriores) ...
    # print("--- FIN DEBUG HOME ---")
    
    # NUEVO: Personalizar contenido basado en cookies comerciales
    # Reorganizar barberos si hay preferencias
    if personalization_data.get('preferences', {}).get('barbero_favorito'):
        fav_barbero_id = personalization_data['preferences']['barbero_favorito']
        barbero_favorito = next((b for b in barberos if b.id == fav_barbero_id), None)
        if barbero_favorito:
            barberos = [barbero_favorito] + [b for b in barberos if b.id != fav_barbero_id]
    
    # Reorganizar servicios si hay preferencias
    if personalization_data.get('preferences', {}).get('servicio_favorito'):
        fav_servicio_id = personalization_data['preferences']['servicio_favorito']
        servicio_favorito = next((s for s in servicios if s.id == fav_servicio_id), None)
        if servicio_favorito:
            servicios = [servicio_favorito] + [s for s in servicios if s.id != fav_servicio_id]
    
    # Productos recomendados basados en visualizaciones
    productos_recomendados = []
    if smart_recommendations.get('show_quick_booking'):
        recommended_product_ids = CartOptimizer.get_smart_recommendations(limit=3)
        if recommended_product_ids:
            productos_recomendados = Producto.query.filter(
                Producto.id.in_(recommended_product_ids[:3])
            ).all()
    
    # Datos de personalización para el template
    personalization_context = {
        'is_returning_customer': personalization_data.get('client', {}).get('is_returning', False),
        'conversion_probability': conversion_probability,
        'show_quick_booking': smart_recommendations.get('show_quick_booking', False),
        'suggested_barbero_id': smart_recommendations.get('suggested_barbero'),
        'suggested_servicio_id': smart_recommendations.get('suggested_servicio'),
        'suggested_time_slots': smart_recommendations.get('suggested_time_slots', []),
        'total_reservas': personalization_data.get('preferences', {}).get('total_reservas', 0),
        'client_name': personalization_data.get('client', {}).get('nombre', ''),
    }

    return render_template('public/Home.html',
                          featured_products=featured_products,
                          barberos=barberos,
                          servicios=servicios,
                          fechas_disponibles=fechas_disponibles,
                          sliders=sliders,
                          productos_recomendados=productos_recomendados,
                          personalization=personalization_context)


@bp.route('/ads.txt')
def ads_txt():
    """Sirve el archivo ads.txt desde la carpeta static para verificación de AdSense."""
    try:
        return send_from_directory(current_app.static_folder, 'ads.txt', mimetype='text/plain')
    except Exception as e:
        current_app.logger.error(f"ads.txt no encontrado o error al servirlo: {e}")
        return ('Not Found', 404)

@bp.route('/about')
def about():
    return render_template("about.html")

@bp.route('/contacto', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # Guardar mensaje en la base de datos
        nuevo_cliente = Cliente(
            nombre=request.form.get('nombre'),
            email=request.form.get('email'),
            telefono=request.form.get('telefono')
        )
        
        db.session.add(nuevo_cliente)
        db.session.flush()  # Para obtener el ID antes del commit final
        
        nuevo_mensaje = Mensaje(
            cliente_id=nuevo_cliente.id,
            asunto=request.form.get('asunto'),
            mensaje=request.form.get('mensaje')
        )
        
        db.session.add(nuevo_mensaje)
        db.session.commit()
        
        return 'Formulario enviado correctamente', 201
    return render_template("contacto.html")

@bp.route('/productos')
def productos():
    """Página de productos agrupados por categoría."""
    
    categorias_con_productos = [] # Nueva estructura para pasar a la plantilla

    try:
        # Obtener todas las categorías ordenadas por nombre
        todas_categorias = Categoria.query.order_by(Categoria.nombre).all()
        
        for categoria in todas_categorias:
            # Obtener productos activos para esta categoría
            # Asumiendo que Producto tiene una relación llamada 'categoria_rel' y un campo 'activo'
            productos_activos = Producto.query.filter_by(
                categoria_id=categoria.id, 
                activo=True
            ).order_by(Producto.nombre).all()
            
            # Si la categoría tiene productos activos, añadirla a la lista
            if productos_activos:
                categorias_con_productos.append({
                    'categoria': categoria, # Pasamos el objeto categoría completo
                    'productos': productos_activos
                })
                
    except Exception as e:
        flash(f"Error al cargar productos: {str(e)}", "danger")
        # Log the error for debugging
        current_app.logger.error(f"Error in /productos route: {e}")

    return render_template(
        'public/productos.html',
        categorias_con_productos=categorias_con_productos # Pasamos la nueva estructura
    )

@bp.route('/checkout', methods=['GET', 'POST'])
def checkout():
    from app.public.forms import CheckoutForm
    from app.models.pedido import Pedido, PedidoItem
    from app.models.producto import Producto
    import json
    
    form = CheckoutForm()
    
    if request.method == 'POST':
        if form.validate_on_submit():
            try:
                # Obtener datos del carrito desde el formulario
                cart_data = request.form.get('cart_data')
                if not cart_data:
                    flash('El carrito está vacío', 'error')
                    return redirect(url_for('public.checkout'))
                
                cart_items = json.loads(cart_data)
                
                if not cart_items:
                    flash('El carrito está vacío', 'error')
                    return redirect(url_for('public.checkout'))
                
                # Crear el pedido
                nuevo_pedido = Pedido(
                    numero_pedido=f"PED{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    cliente_nombre=form.nombre.data,
                    cliente_email=form.email.data,
                    cliente_telefono=form.telefono.data,
                    notas=form.notas.data,
                    total=0  # Se calculará después
                )
                
                db.session.add(nuevo_pedido)
                db.session.flush()  # Para obtener el ID
                
                # Procesar items del carrito
                total_pedido = 0
                for item in cart_items:
                    producto = Producto.query.get(item['id'])
                    if producto:
                        cantidad = int(item['quantity'])
                        subtotal = float(producto.precio) * cantidad
                        
                        pedido_item = PedidoItem(
                            pedido_id=nuevo_pedido.id,
                            producto_id=producto.id,
                            producto_nombre=producto.nombre,
                            producto_precio=producto.precio,
                            cantidad=cantidad,
                            subtotal=subtotal
                        )
                        
                        db.session.add(pedido_item)
                        total_pedido += subtotal
                
                # Actualizar el total del pedido
                nuevo_pedido.total = total_pedido
                db.session.commit()
                
                # NUEVO: Procesar cookies comerciales para e-commerce
                response = make_response(redirect(url_for('public.confirmacion_pedido', pedido_id=nuevo_pedido.id)))
                
                from app.utils.cart_optimizer import CartOptimizer
                from app.utils.business_cookies import BusinessCookieManager
                
                # Limpiar carrito persistente después de compra exitosa
                response.set_cookie('persistent_cart', '', expires=0)
                
                # Guardar datos del cliente para futuras compras
                client_data = {
                    'nombre': form.nombre.data,
                    'email': form.email.data,
                    'telefono': form.telefono.data
                }
                BusinessCookieManager.save_client_data_smart(response, client_data)
                
                # Tracking de conversión de compra
                response = BusinessCookieManager.update_booking_step(
                    response, 'purchase_completed', {
                        'pedido_id': nuevo_pedido.id,
                        'total_compra': float(total_pedido),
                        'items_cantidad': len(cart_items),
                        'conversion_time': datetime.now().isoformat()
                    }
                )
                
                flash('¡Pedido creado exitosamente!', 'success')
                return response
                
            except Exception as e:
                db.session.rollback()
                flash('Error al procesar el pedido. Intenta de nuevo.', 'error')
                print(f"Error en checkout: {e}")
    
    return render_template('public/checkout.html', form=form)

@bp.route('/confirmacion-pedido/<int:pedido_id>')
def confirmacion_pedido(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    return render_template('public/confirmacion_pedido.html', pedido=pedido)

@bp.route('/servicios')
def servicios():
    try:
        # Inicializar servicios con una lista vacía por si acaso falla
        servicios_activos = []
        
        # Intentar verificar la conexión a la base de datos primero
        from sqlalchemy.sql import text
        from app import db
        db.session.execute(text("SELECT 1"))
        print("Conexión a la base de datos verificada correctamente")
        
        # Obtener solo los servicios marcados como activos
        print("Consultando servicios activos...")
        servicios_activos = Servicio.query.filter_by(activo=True).order_by(Servicio.nombre).all()
        print(f"Servicios encontrados: {len(servicios_activos)}")
        
        return render_template("public/servicios.html", 
                            servicios=servicios_activos)
    except Exception as e:
        print(f"Error al consultar servicios: {str(e)}")
        import traceback
        traceback.print_exc()
        # Devolver una lista vacía en caso de error para no romper la página
        return render_template("public/servicios.html", 
                            servicios=[], error_msg=f"No se pudieron cargar los servicios: {str(e)}")

@bp.route('/api/servicio/<int:servicio_id>')
def get_servicio_data(servicio_id):
    """API endpoint para obtener datos de un servicio específico"""
    try:
        servicio = Servicio.query.filter_by(id=servicio_id, activo=True).first()
        if not servicio:
            return jsonify({'error': 'Servicio no encontrado'}), 404
        
        # Formatear el precio usando la función format_cop
        from app.utils import format_cop
        
        # Obtener todas las imágenes del servicio
        imagenes_galeria = servicio.get_imagenes_activas()
        imagenes_urls = [img.ruta_imagen for img in imagenes_galeria] if imagenes_galeria else []
        
        # Si no hay imágenes en la galería, usar imagen_url como fallback
        if not imagenes_urls and servicio.imagen_url:
            imagenes_urls = [servicio.imagen_url]
        
        servicio_data = {
            'id': servicio.id,
            'nombre': servicio.nombre,
            'descripcion': servicio.descripcion or 'Sin descripción disponible',
            'precio_formateado': format_cop(servicio.precio),
            'precio_valor': float(servicio.precio),
            'duracion_estimada': servicio.duracion_estimada,
            'imagen_url': servicio.get_imagen_principal(),  # Imagen principal para compatibilidad
            'imagenes': imagenes_urls,  # Array de todas las imágenes
            'total_imagenes': len(imagenes_urls),
            'activo': servicio.activo
        }
        
        return jsonify(servicio_data)
        
    except Exception as e:
        current_app.logger.error(f"Error al obtener datos del servicio {servicio_id}: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

# @bp.route('/barberos/<int:id>/disponibilidad', methods=['GET', 'POST'])
# @login_required
# def gestionar_disponibilidad(id):
#     if not current_user.is_admin():
#         abort(403)
    
#     barbero = Barbero.query.get_or_404(id)
#     form = DisponibilidadForm()
    
#     if form.validate_on_submit():
#         # Convertir strings a objetos time
#         from datetime import datetime
#         hora_inicio = datetime.strptime(form.hora_inicio.data, '%H:%M').time()
#         hora_fin = datetime.strptime(form.hora_fin.data, '%H:%M').time()
        
#         disponibilidad = DisponibilidadBarbero(
#             barbero_id=barbero.id,
#             dia_semana=form.dia_semana.data,
#             hora_inicio=hora_inicio,
#             hora_fin=hora_fin,
#             activo=form.activo.data
#         )
        
#         db.session.add(disponibilidad)
#         try:
#             db.session.commit()
#             flash('Disponibilidad añadida correctamente', 'success')
#         except Exception as e:
#             db.session.rollback()
#             flash(f'Error al añadir disponibilidad: {str(e)}', 'danger')
            
#         return redirect(url_for('admin.gestionar_disponibilidad', id=barbero.id))
    
#     # Mostrar disponibilidad actual
#     disponibilidades = DisponibilidadBarbero.query.filter_by(barbero_id=barbero.id).order_by(DisponibilidadBarbero.dia_semana).all()
    
#     return render_template('admin/disponibilidad.html', 
#                            title=f'Disponibilidad de {barbero.nombre}',
#                            form=form,
#                            barbero=barbero,
#                            disponibilidades=disponibilidades)

@bp.route('/api/disponibilidad/<int:barbero_id>/<string:fecha>')
def disponibilidad_barbero(barbero_id, fecha):
    """
    Obtiene los horarios disponibles para un barbero en una fecha específica,
    considerando la duración de un servicio.

    Args:
        barbero_id (int): ID del barbero.
        fecha (str): Fecha en formato YYYY-MM-DD.

    Query Params:
        servicio_id (int): ID del servicio seleccionado.
    """
    try:
        fecha_dt = datetime.strptime(fecha, '%Y-%m-%d').date()
        barbero = Barbero.query.get_or_404(barbero_id)

        servicio_id = request.args.get('servicio_id', type=int)
        duracion_servicio = 30 

        if servicio_id:
            servicio = Servicio.query.get(servicio_id)
            if servicio:
                duracion_servicio = servicio.get_duracion_minutos()
                print(f"Servicio '{servicio.nombre}': {duracion_servicio} minutos")
            else:
                print(f"Warning: Servicio con ID {servicio_id} no encontrado. Usando duración por defecto.")
        else:
             print("Warning: No se proporcionó servicio_id. Usando duración por defecto.")

        horarios_obj_list = barbero.obtener_horarios_disponibles(fecha_dt, duracion_servicio)

        horarios_disponibles_str = []
        if horarios_obj_list:
            for slot in horarios_obj_list:
                if slot['disponible']:
                    horarios_disponibles_str.append(slot['hora'])
        
        mensaje_respuesta = f'Horarios disponibles para {barbero.nombre} el {fecha}'
        if not horarios_disponibles_str: # Comprobar la lista de strings filtrada
             disponibilidades_dia = barbero.get_disponibilidad_por_dia(fecha_dt.weekday())
             if not disponibilidades_dia:
                 mensaje_respuesta = f"{barbero.nombre} no tiene horario configurado para este día."
             else:
                 mensaje_respuesta = f"No hay horarios disponibles para {barbero.nombre} el {fecha} con duración de {duracion_servicio} min."


        return jsonify({
            'barbero': barbero.nombre,
            'fecha': fecha,
            'horarios': horarios_disponibles_str, # Usar la lista de strings de horas disponibles
            'mensaje': mensaje_respuesta 
        })

    except ValueError as ve:
         print(f"Error de formato en disponibilidad_barbero: {str(ve)}")
         return jsonify({'error': 'Formato de fecha inválido. Use YYYY-MM-DD.'}), 400
    except Exception as e:
        print(f"Error en disponibilidad_barbero: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Error interno al obtener disponibilidad.'}), 500

@bp.route('/api/agendar-cita', methods=['POST'])
def agendar_cita():
    try:
        data = request.json
        current_app.logger.info(f"Datos recibidos para agendar cita: {data}")

        required_fields = ['barbero_id', 'servicio_id', 'fecha', 'hora', 'nombre', 'email', 'telefono']
        for field in required_fields:
            if field not in data or not data[field]:
                current_app.logger.error(f"Campo faltante o vacío: {field}")
                return jsonify({'error': f'Falta el campo o está vacío: {field}'}), 400

        fecha_hora_str = f"{data['fecha']} {data['hora']}"
        fecha_hora = datetime.strptime(fecha_hora_str, '%Y-%m-%d %H:%M')

        # Obtener la duración del servicio para verificar conflictos
        servicio = Servicio.query.get(int(data['servicio_id']))
        duracion_servicio = servicio.get_duracion_minutos() if servicio else 30
        
        # Calcular el rango de tiempo que ocupará la nueva cita
        inicio_nueva_cita = fecha_hora
        fin_nueva_cita = inicio_nueva_cita + timedelta(minutes=duracion_servicio)
        
        # Obtener todas las citas del barbero para el día seleccionado
        fecha_inicio_dia = datetime.combine(fecha_hora.date(), datetime.min.time())
        fecha_fin_dia = fecha_inicio_dia + timedelta(days=1)
        
        citas_del_dia = Cita.query.filter(
            Cita.barbero_id == int(data['barbero_id']),
            Cita.estado.in_(['confirmada', 'pendiente_confirmacion']),
            Cita.fecha >= fecha_inicio_dia,
            Cita.fecha < fecha_fin_dia
        ).all()

        # Verificar solapamientos en Python
        hay_solapamiento = False
        for cita_existente in citas_del_dia:
            inicio_existente = cita_existente.fecha
            fin_existente = inicio_existente + timedelta(minutes=cita_existente.duracion or 30)
            
            # Verificar si hay solapamiento: la nueva cita no debe empezar antes de que termine una existente
            # ni terminar después de que empiece otra existente
            if not (fin_nueva_cita <= inicio_existente or inicio_nueva_cita >= fin_existente):
                hay_solapamiento = True
                current_app.logger.warning(f"Solapamiento detectado con cita ID {cita_existente.id}: "
                                         f"Existente: {inicio_existente} - {fin_existente}, "
                                         f"Nueva: {inicio_nueva_cita} - {fin_nueva_cita}")
                break

        if hay_solapamiento:
            current_app.logger.warning(f"Intento de agendar cita con solapamiento: Barbero {data['barbero_id']} desde {fecha_hora} hasta {fin_nueva_cita}")
            return jsonify({'error': 'Este horario se solapa con otra cita. Por favor, selecciona otro horario.'}), 409 # 409 Conflict

        cliente = Cliente.query.filter_by(email=data['email']).first()
        if not cliente:
            cliente = Cliente(
                nombre=data['nombre'],
                email=data['email'],
                telefono=data['telefono']
            )
            db.session.add(cliente)
            db.session.flush() # Para obtener el ID del cliente si es nuevo
        else: # Actualizar datos si el cliente existe
            cliente.nombre = data['nombre']
            cliente.telefono = data['telefono']
            # No es necesario db.session.add(cliente) si ya existe y solo se modifica

        # Obtener la duración del servicio
        servicio = Servicio.query.get(int(data['servicio_id']))
        duracion_servicio = servicio.get_duracion_minutos() if servicio else 30
        
        nueva_cita = Cita(
            cliente_id=cliente.id,
            barbero_id=int(data['barbero_id']),
            servicio_id=int(data['servicio_id']),
            fecha=fecha_hora,
            estado='pendiente_confirmacion', # Estado inicial
            duracion=duracion_servicio,  # Guardar la duración del servicio
            notas=data.get('notas', '')
        )
        db.session.add(nueva_cita)
        db.session.commit() # Commit para obtener el ID de nueva_cita

        token = nueva_cita.generate_confirmation_token()
        current_app.logger.info(f"Cita ID {nueva_cita.id} creada, token generado. Enviando correo a {cliente.email}")

        # Enviar correo de confirmación
        # Las relaciones barbero y servicio_rel se cargarán automáticamente al acceder a ellas
        # en la plantilla del correo si no son lazy='dynamic' o si se accede a ellas antes.
        # Para estar seguros, podemos precargarlas o pasar los nombres directamente.
        # Aquí, el modelo Cita ya tiene las relaciones, así que deberían funcionar.

        send_appointment_confirmation_email(
            cliente_email=cliente.email,
            cliente_nombre=cliente.nombre,
            cita=nueva_cita, # Pasamos el objeto cita completo
            token=token
        )

        # NUEVO: Crear respuesta con cookies comerciales optimizadas
        response_data = {
            'success': True,
            'mensaje': 'Solicitud de cita recibida. Por favor, revisa tu correo electrónico para confirmar la cita en la próxima hora.',
            'cita_id': nueva_cita.id
        }
        
        response = make_response(jsonify(response_data))
        
        # Actualizar cookies comerciales para maximizar futuras conversiones
        from app.utils.business_cookies import BusinessCookieManager
        
        # Guardar datos del cliente para auto-completar futuras reservas
        BusinessCookieManager.save_client_data_smart(response, data)
        
        # Guardar preferencias de barbero y servicio
        BusinessCookieManager.save_preferences_smart(
            response, 
            int(data['barbero_id']), 
            int(data['servicio_id']), 
            data['hora']
        )
        
        # Tracking de conversión exitosa
        response = BusinessCookieManager.update_booking_step(
            response, 'booking_completed', {
                'cita_id': nueva_cita.id,
                'conversion_time': datetime.now().isoformat(),
                'barbero_seleccionado': data['barbero_id'],
                'servicio_seleccionado': data['servicio_id']
            }
        )
        
        return response

    except ValueError as ve:
        current_app.logger.error(f"Error de formato en agendar_cita: {str(ve)}")
        return jsonify({'error': f'Formato de fecha u hora inválido: {str(ve)}'}), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error al agendar cita: {str(e)}", exc_info=True)
        return jsonify({'error': 'Ocurrió un error al procesar tu solicitud. Inténtalo de nuevo más tarde.'}), 500

@bp.route('/confirmar-cita/<token>', methods=['GET'])
def confirmar_cita_route(token):
    # Intentar obtener la cita desde el token sin imponer estado (manejo idempotente)
    cita_token = Cita.get_cita_from_token(token)
    if not cita_token:
        flash('El enlace de confirmación no es válido o ha expirado.', 'danger')
        return render_template('public/confirmation_status.html',
                               success=False,
                               message='El enlace de confirmación no es válido o ha expirado.')

    # Si ya está confirmada, mostrar éxito (posible prefetch del enlace por el proveedor de correo)
    if cita_token.estado == 'confirmada':
        return render_template('public/confirmation_status.html',
                               success=True,
                               message='¡Tu cita ya estaba confirmada!',
                               cita=cita_token)

    # Si está cancelada o expirada, informar claramente
    if cita_token.estado in ['cancelada', 'expirada', 'cancelada_conflicto']:
        return render_template('public/confirmation_status.html',
                               success=False,
                               message='Esta cita ya no puede ser confirmada (estado actual: {}).'.format(cita_token.estado))

    # En este punto, esperamos que esté pendiente de confirmación
    if cita_token.estado != 'pendiente_confirmacion':
        return render_template('public/confirmation_status.html',
                               success=False,
                               message='Esta cita no está en estado pendiente de confirmación.')

    # Doble verificación de conflicto antes de confirmar
    conflicting_cita = Cita.query.filter(
        Cita.barbero_id == cita_token.barbero_id,
        Cita.fecha == cita_token.fecha,
        Cita.id != cita_token.id,
        Cita.estado == 'confirmada'
    ).first()

    if conflicting_cita:
        cita_token.estado = 'cancelada_conflicto'
        db.session.commit()
        flash('Lo sentimos, este horario fue tomado justo antes de tu confirmación. Por favor, agenda de nuevo.', 'danger')
        return render_template('public/confirmation_status.html',
                               success=False,
                               message='Lo sentimos, este horario fue tomado justo antes de tu confirmación. Por favor, agenda de nuevo.')

    # Confirmar la cita
    cita_token.estado = 'confirmada'
    cita_token.confirmed_at = datetime.utcnow()
    db.session.commit()
    
    flash('¡Tu cita ha sido confirmada exitosamente!', 'success')
    return render_template('public/confirmation_status.html',
                           success=True,
                           message='¡Tu cita ha sido confirmada exitosamente!',
                           cita=cita_token)