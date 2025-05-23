"""
Módulo para la importación de datos iniciales a la base de datos.
Este módulo está diseñado para ser ejecutado dentro de un contexto de aplicación Flask.
"""
from app.models import Producto, Barbero, User
from flask import current_app
import logging

# --- Datos de Muestra ---

# Datos de muestra para Barberos
barberos_data = [
    {
        'nombre': 'Carlos "El Navaja" Pérez',
        'especialidad': 'Cortes clásicos y afeitado tradicional',
        'imagen_url': 'https://images.unsplash.com/photo-1595476108111-78411bf2c4a3' # URL de ejemplo
    },
    {
        'nombre': 'Sofía "La Estilista" Gómez',
        'especialidad': 'Cortes modernos y coloración',
        'imagen_url': 'https://images.unsplash.com/photo-1621607512022-6aecc4fed814' # URL de ejemplo
    },
    {
        'nombre': 'Andrés "El Preciso" Martínez',
        'especialidad': 'Diseños de barba y fade',
        'imagen_url': 'https://images.unsplash.com/photo-1605497788044-5a32c7078486' # URL de ejemplo
    }
]

# Datos de muestra para Productos
productos_data = [
    # Productos para Peinar
    {
        'nombre': 'Pomada Fijadora Premium',
        'descripcion': 'Pomada de alta fijación con acabado mate natural.',
        'precio': 15.99,
        'imagen_url': 'https://images.unsplash.com/photo-1581071562441-17d6347050bc',
        'categoria': 'peinar'
    },
    # Productos para Barba
    {
        'nombre': 'Aceite Nutritivo',
        'descripcion': 'Aceite 100% natural para hidratar y dar brillo a tu barba.',
        'precio': 18.50,
        'imagen_url': 'https://images.unsplash.com/photo-1598528738936-c50861cc5306',
        'categoria': 'barba'
    },
    {
        'nombre': 'Bálsamo Modelador',
        'descripcion': 'Bálsamo de fijación media para dar forma y controlar la barba rebelde.',
        'precio': 14.95,
        'imagen_url': 'https://images.unsplash.com/photo-1567263361389-c218cf7b1c3e',
        'categoria': 'barba'
    },
    {
        'nombre': 'Champú Especializado',
        'descripcion': 'Champú especial para limpiar y acondicionar la barba sin resecarla.',
        'precio': 12.99,
        'imagen_url': 'https://images.unsplash.com/photo-1585751119414-ef2636f8aede',
        'categoria': 'barba'
    },
    
    # Accesorios
    {
        'nombre': 'Cepillo de Cerdas Naturales',
        'descripcion': 'Cepillo artesanal con cerdas de jabalí para un peinado perfecto de la barba.',
        'precio': 22.75,
        'imagen_url': 'https://images.unsplash.com/photo-1518531933037-91b2f5f229cc',
        'categoria': 'accesorios'
    },
    {
        'nombre': 'Kit de Afeitado Clásico',
        'descripcion': 'Set completo con navaja, brocha y jabón para un afeitado tradicional.',
        'precio': 45.00,
        'imagen_url': 'https://images.unsplash.com/photo-1621607751499-46e8d2d4264f',
        'categoria': 'accesorios'
    }
]


# --- Lógica de Carga de Datos ---

def import_initial_data():
    """
    Importa datos iniciales a la base de datos.
    Debe ser ejecutada dentro de un contexto de aplicación Flask.
    
    Returns:
        bool: True si la operación fue exitosa, False en caso contrario.
    """
    from app import db
    from app.models.producto import Producto
    from app.models.barbero import Barbero
    from app.models.admin import User
    from app.models.categoria import Categoria
    from app.models.servicio import Servicio
    
    try:
        # Verificar si ya hay datos
        num_productos = Producto.query.count()
        num_barberos = Barbero.query.count()
        num_servicios = Servicio.query.count()
        
        print(f"Estado actual de la BD: {num_productos} productos, {num_barberos} barberos, {num_servicios} servicios")
        
        if num_productos > 0 and num_barberos > 0 and num_servicios > 0:
            print("La base de datos ya contiene datos. Saltando importación.")
            return True
        
        print("Iniciando carga de datos iniciales...")
        
        # Primero creamos categorías
        categorias = {}
        for cat_name in ['peinar', 'barba', 'accesorios']:
            categoria = Categoria(nombre=cat_name)
            db.session.add(categoria)
            db.session.flush()  # Para obtener el ID
            categorias[cat_name] = categoria.id
            
        print(f"Categorías creadas: {categorias}")
        
        # Ahora añadimos servicios básicos
        servicios = [
            {
                'nombre': 'Corte de Cabello',
                'descripcion': 'Corte básico de cabello con tijera y/o máquina',
                'precio': 15000,
                'duracion_estimada': '30 min',
                'activo': True
            },
            {
                'nombre': 'Afeitado Tradicional',
                'descripcion': 'Afeitado con navaja y toalla caliente',
                'precio': 12000,
                'duracion_estimada': '20 min',
                'activo': True
            },
            {
                'nombre': 'Corte + Barba',
                'descripcion': 'Combo de corte de cabello y arreglo de barba',
                'precio': 25000,
                'duracion_estimada': '45 min',
                'activo': True
            }
        ]
        
        for servicio_data in servicios:
            servicio = Servicio(**servicio_data)
            db.session.add(servicio)
        
        # Añadimos barberos solo si no existen
        if num_barberos == 0:
    
    # 4. Cargar Barberos
    print(f"Cargando {len(barberos_data)} barberos...")
    for b_data in barberos_data:
        barbero = Barbero(
            nombre=b_data['nombre'],
            especialidad=b_data['especialidad'],
            imagen_url=b_data['imagen_url']
            # 'activo' es True por defecto
        )
        db.session.add(barbero)

    # 5. Cargar Productos
    print(f"Cargando {len(productos_data)} productos...")
    for p_data in productos_data:
        producto = Producto(
            nombre=p_data['nombre'],
            descripcion=p_data['descripcion'],
            precio=p_data['precio'],
            imagen_url=p_data['imagen_url'],
            categoria=p_data['categoria']
        )
        db.session.add(producto)

    # 6. Crear usuario administrador si no existe
    admin_username = 'admin'
    admin_email = 'admin@barberbrothers.com'
    admin_password = 'admin123456' # ¡Cambia esto por una contraseña segura!

    if User.query.filter_by(username=admin_username).first() is None:
        print(f"Creando usuario administrador: {admin_username}")
        admin_user = User(
            username=admin_username, 
            email=admin_email, 
            role='admin' # Asegúrate que el rol coincide con tu lógica de autorización
        )
        admin_user.set_password(admin_password) # Hashea la contraseña
        db.session.add(admin_user)
    else:
        print(f"Usuario administrador '{admin_username}' ya existe.")

    # 7. Guardar todos los cambios en la base de datos
    try:
        db.session.commit()
        print("\n¡Datos iniciales cargados y guardados correctamente!")
    except Exception as e:
        db.session.rollback() # Deshacer cambios si hay un error
        print(f"\nError al guardar datos: {e}")

def import_initial_data():
    """
    Importa los datos iniciales a la base de datos.
    Esta función se puede llamar desde otros scripts.
    """
    with app.app_context():
        print("Importando barberos...")
        for barbero_info in barberos_data:
            barbero = Barbero.query.filter_by(nombre=barbero_info['nombre']).first()
            if not barbero:
                barbero = Barbero(
                    nombre=barbero_info['nombre'],
                    especialidad=barbero_info['especialidad'],
                    imagen_url=barbero_info['imagen_url']
                )
                db.session.add(barbero)
        
        print("Importando productos...")
        for producto_info in productos_data:
            producto = Producto.query.filter_by(nombre=producto_info['nombre']).first()
            if not producto:
                producto = Producto(
                    nombre=producto_info['nombre'],
                    descripcion=producto_info['descripcion'],
                    precio=producto_info['precio'],
                    imagen_url=producto_info['imagen_url'],
                    categoria=producto_info['categoria']
                )
                db.session.add(producto)
        
        db.session.commit()
        print("Datos iniciales importados correctamente.")

# Si se ejecuta este script directamente
if __name__ == "__main__":
    with app.app_context():
        import_initial_data()