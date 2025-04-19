from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Importar modelos después de crear la instancia db
from models import Producto, Cliente, Cita

@app.route('/')
def home():
    return render_template("Home.html")

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/contacto', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # Guardar mensaje en la base de datos
        nuevo_cliente = Cliente(
            nombre=request.form.get('nombre'),
            email=request.form.get('email'),
            telefono=request.form.get('telefono')
        )
        
        nuevo_mensaje = Mensaje(
            cliente_id=nuevo_cliente.id,
            asunto=request.form.get('asunto'),
            mensaje=request.form.get('mensaje')
        )
        
        db.session.add(nuevo_cliente)
        db.session.add(nuevo_mensaje)
        db.session.commit()
        
        return 'Formulario enviado correctamente', 201
    return render_template("contacto.html")
    
@app.route('/api/info')
def api_info():
    return {
        'nombre': 'Barberia',
        'direccion': 'Calle Falsa 123',
        'telefono': '123456789'
    }, 200

@app.route('/productos')
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

# Nueva ruta para administrar productos
@app.route('/admin/productos', methods=['GET', 'POST'])
def admin_productos():
    if request.method == 'POST':
        # Añadir nuevo producto
        nuevo_producto = Producto(
            nombre=request.form.get('nombre'),
            descripcion=request.form.get('descripcion'),
            precio=float(request.form.get('precio')),
            imagen_url=request.form.get('imagen_url')
        )
        db.session.add(nuevo_producto)
        db.session.commit()
        
    productos_lista = Producto.query.all()
    return render_template("admin/productos.html", productos=productos_lista)

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if request.method == 'POST':
        # Aquí implementarías la lógica para procesar el pedido
        # como guardar en la base de datos, conectar con pasarela de pago, etc.
        return jsonify({'success': True})
    return render_template("checkout.html")

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
