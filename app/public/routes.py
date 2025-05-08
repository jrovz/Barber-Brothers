from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.public import bp
from app.models.producto import Producto
from app.models.cliente import Cliente, Mensaje
from app.models.servicio import Servicio # Asegúrate de que este modelo existe
from app.models.barbero import Barbero, DisponibilidadBarbero
from app.models.categoria import Categoria # <<< IMPORT Categoria MODEL
from app import db
from datetime import datetime, timedelta, time

@bp.route('/')
def home():
    # Inicializar todas las variables al principio para evitar errores
    featured_products = []
    barberos = []
    servicios = []
    fechas_disponibles = []
    
    try:
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
        servicios = Servicio.query.filter_by(activo=True).all()
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

    return render_template('public/Home.html',
                          featured_products=featured_products,
                          barberos=barberos,
                          servicios=servicios,
                          fechas_disponibles=fechas_disponibles)

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
    
    productos_peinar = []
    productos_barba = []
    productos_accesorios = []

    try:
        categoria_peinar = Categoria.query.filter(Categoria.nombre.ilike('peinar')).first()
        if categoria_peinar:
            productos_peinar = Producto.query.filter_by(
                categoria_id=categoria_peinar.id, 
                activo=True
            ).order_by(Producto.nombre).all()

        categoria_barba = Categoria.query.filter(Categoria.nombre.ilike('barba')).first()
        if categoria_barba:
            productos_barba = Producto.query.filter_by(
                categoria_id=categoria_barba.id, 
                activo=True
            ).order_by(Producto.nombre).all()

        categoria_accesorios = Categoria.query.filter(Categoria.nombre.ilike('accesorios')).first()
        if categoria_accesorios:
            productos_accesorios = Producto.query.filter_by(
                categoria_id=categoria_accesorios.id, 
                activo=True
            ).order_by(Producto.nombre).all()
            
    except Exception as e:
        flash(f"Error al cargar productos: {str(e)}", "danger")
        # Log the error for debugging
        current_app.logger.error(f"Error in /productos route: {e}")


    return render_template(
        'public/productos.html',
        productos_peinar=productos_peinar,
        productos_barba=productos_barba,
        productos_accesorios=productos_accesorios
    )

@bp.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if request.method == 'POST':
        # Lógica para procesar el pedido
        return {'success': True}, 201
    return render_template("checkout.html")

@bp.route('/servicios')
def servicios():
    # Obtener solo los servicios marcados como activos
    servicios_activos = Servicio.query.filter_by(activo=True).order_by(Servicio.nombre).all()
    return render_template("public/servicios.html", 
                           servicios=servicios_activos)

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

        # Obtener servicio_id y duración del query param
        servicio_id = request.args.get('servicio_id', type=int)
        duracion_servicio = 30 # Duración por defecto si no se proporciona servicio

        if servicio_id:
            servicio = Servicio.query.get(servicio_id)
            if servicio and servicio.duracion_estimada:
                # Asumiendo que duracion_estimada es un string como "30 min" o solo "30"
                try:
                    # Extraer solo los dígitos
                    duracion_str = ''.join(filter(str.isdigit, str(servicio.duracion_estimada)))
                    if duracion_str:
                         duracion_servicio = int(duracion_str)
                    else: # Si no hay dígitos, usar defecto
                         print(f"Warning: No se pudo extraer duración numérica de '{servicio.duracion_estimada}'. Usando {duracion_servicio} min.")
                except (ValueError, TypeError):
                     print(f"Warning: Error al convertir duración '{servicio.duracion_estimada}'. Usando {duracion_servicio} min.")
                     # Mantener el valor por defecto
        else:
             print("Warning: No se proporcionó servicio_id. Usando duración por defecto.")


        # --- Lógica de Fallback Eliminada ---
        # Ya no generamos horarios predeterminados si no hay configuración.
        # El método obtener_horarios_disponibles debe manejar esto.

        # Llamar al método del modelo pasando la duración
        # ASUMIENDO que el método ahora acepta duracion_servicio
        horarios = barbero.obtener_horarios_disponibles(fecha_dt, duracion_servicio)

        mensaje_respuesta = f'Horarios disponibles para {barbero.nombre} el {fecha}'
        if not horarios:
             # Verificar si hay disponibilidad configurada para ese día
             disponibilidades_dia = barbero.get_disponibilidad_por_dia(fecha_dt.weekday())
             if not disponibilidades_dia:
                 mensaje_respuesta = f"{barbero.nombre} no tiene horario configurado para este día."
             else:
                 mensaje_respuesta = f"No hay horarios disponibles para {barbero.nombre} el {fecha} con duración de {duracion_servicio} min."


        return jsonify({
            'barbero': barbero.nombre,
            'fecha': fecha,
            'horarios': horarios,
            'mensaje': mensaje_respuesta # Mensaje informativo
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
        print(f"Datos recibidos para agendar cita: {data}")
        
        # Validar datos requeridos
        required_fields = ['barbero_id', 'servicio_id', 'fecha', 'hora', 'nombre', 'email', 'telefono']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Falta el campo: {field}'}), 400
                
        # Convertir fecha y hora a objeto datetime
        fecha_hora_str = f"{data['fecha']} {data['hora']}"
        fecha_hora = datetime.strptime(fecha_hora_str, '%Y-%m-%d %H:%M')
        
        # Crear o buscar cliente en la base de datos
        from app.models.cliente import Cliente, Cita
        cliente = Cliente.query.filter_by(email=data['email']).first()
        
        if not cliente:
            cliente = Cliente(
                nombre=data['nombre'],
                email=data['email'],
                telefono=data['telefono']
            )
            db.session.add(cliente)
            db.session.flush()  # Para obtener el ID generado
        
        # Crear la cita
        nueva_cita = Cita(
            cliente_id=cliente.id,
            barbero_id=int(data['barbero_id']),
            servicio_id=int(data['servicio_id']), 
            fecha=fecha_hora,
            estado='confirmada',
            notas=data.get('notas', '')
        )
        
        db.session.add(nueva_cita)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'mensaje': 'Cita agendada correctamente',
            'cita_id': nueva_cita.id
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error al agendar cita: {str(e)}")
        return jsonify({'error': str(e)}), 500