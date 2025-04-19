from app import app, db
from models import Producto

# Productos de muestra
productos = [
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

# Insertar datos
with app.app_context():
    # Limpiar datos existentes (opcional)
    db.session.query(Producto).delete()
    
    for p in productos:
        producto = Producto(
            nombre=p['nombre'],
            descripcion=p['descripcion'],
            precio=p['precio'],
            imagen_url=p['imagen_url'],
            categoria=p['categoria']
        )
        db.session.add(producto)
    
    db.session.commit()
    print("Datos de muestra agregados correctamente!")