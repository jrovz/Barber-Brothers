# Script para actualizar la segmentación de clientes existentes
from app import create_app, db
from app.models.cliente import Cliente, Cita
from datetime import datetime

app = create_app()

with app.app_context():
    print("Actualizando segmentación de clientes...")
    clientes = Cliente.query.all()
    count = 0
    
    for cliente in clientes:
        # Verificar el total de visitas (citas completadas)
        total_citas = Cita.query.filter_by(
            cliente_id=cliente.id,
            estado='completada'
        ).count()
        
        # Encontrar la última visita del cliente
        ultima_cita = Cita.query.filter_by(
            cliente_id=cliente.id,
            estado='completada'
        ).order_by(Cita.fecha.desc()).first()
        
        # Actualizar los datos del cliente
        cliente.total_visitas = total_citas
        if ultima_cita:
            cliente.ultima_visita = ultima_cita.fecha
            
        # Clasificar al cliente según su patrón de visitas
        cliente.clasificar_segmento()
        count += 1
    
    # Guardar los cambios en la base de datos
    db.session.commit()
    print(f"Se actualizó la segmentación para {count} clientes.")
