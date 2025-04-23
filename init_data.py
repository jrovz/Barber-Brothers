from app import create_app, db
# 1. Importar TODOS los modelos necesarios
from app.models import Producto, Barbero, User 

app = create_app()

# --- Datos de Muestra ---

# 2. Datos de muestra para Barberos
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

# Datos de muestra para Productos (ya existente)
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

# Usa el contexto de aplicación para operaciones con la base de datos
with app.app_context():
    print("Iniciando carga de datos iniciales...")
    
    # 3. Limpiar datos existentes (opcional, pero recomendado para scripts de prueba)
    # ¡CUIDADO! Esto borrará todos los datos de estas tablas.
    print("Limpiando datos existentes (Productos, Barberos, Usuarios)...")
    db.session.query(Producto).delete()
    db.session.query(Barbero).delete()
    # No borres todos los usuarios si quieres mantener otros, filtra por rol si es necesario
    # db.session.query(User).delete() 
    # O borra solo los no-admin si quieres mantener el admin entre ejecuciones
    # db.session.query(User).filter(User.role != 'admin').delete()
    
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