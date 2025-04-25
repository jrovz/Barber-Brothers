from flask import render_template, request, redirect, url_for
from app.public import bp
from app.models.producto import Producto
from app.models.cliente import Cliente, Mensaje
from app.models.servicio import Servicio # Asegúrate de que este modelo existe
from app import db

@bp.route('/')
def home():
    try:
        featured_products = Producto.query.order_by(Producto.created_at.desc()).limit(3).all() 
    except AttributeError as e:
        print(f"Error querying products: {e}")
        print(f"Type of 'Product' variable: {type(Producto)}")
        featured_products = [] # Assign empty list on error
    
    return render_template('public/Home.html', featured_products=featured_products)

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
    # Obtener productos y agruparlos por categoría
    productos_peinar = Producto.query.filter_by(categoria='peinar').all()
    productos_barba = Producto.query.filter_by(categoria='barba').all()
    productos_accesorios = Producto.query.filter_by(categoria='accesorios').all()
    
    return render_template(
        "productos.html", 
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
    """Renders the services page, fetching services from the database."""
    try:
        # Query all services from the database
        # You might want to add ordering, e.g., .order_by(Servicio.nombre)
        lista_servicios = Servicio.query.all()
    except Exception as e:
        # Handle potential database errors gracefully
        print(f"Error fetching services: {e}")
        lista_servicios = [] # Pass an empty list if there's an error

    return render_template("public/servicios.html", servicios=lista_servicios)
