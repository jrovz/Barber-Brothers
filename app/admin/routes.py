from flask import render_template, request, redirect, url_for
from app.admin import bp
from app.models.producto import Producto
from app import db

@bp.route('/productos', methods=['GET', 'POST'])
def productos():
    if request.method == 'POST':
        # Añadir nuevo producto
        nuevo_producto = Producto(
            nombre=request.form.get('nombre'),
            descripcion=request.form.get('descripcion'),
            precio=float(request.form.get('precio')),
            imagen_url=request.form.get('imagen_url'),
            categoria=request.form.get('categoria', 'peinar')
        )
        db.session.add(nuevo_producto)
        db.session.commit()
        
    productos_lista = Producto.query.all()
    return render_template("productos.html", productos=productos_lista)