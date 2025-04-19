from flask import render_template, request, redirect, url_for
from app.public import bp
from app.models.producto import Producto
from app.models.cliente import Cliente, Mensaje
from app import db

@bp.route('/')
def home():
    return render_template("home.html")

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