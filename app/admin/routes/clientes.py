"""Listado, detalle y segmentacion de clientes."""
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.admin import bp
from app.utils.decorators import admin_required
from app.models.cliente import Cliente, Cita
from app import db
from app.admin.forms import ClienteFilterForm


@bp.route('/clientes', methods=['GET', 'POST'])
@login_required
@admin_required
def gestionar_clientes():
    
    form = ClienteFilterForm()
    
    # Si se envía el formulario, redirigir con los filtros como parámetros de URL
    if form.validate_on_submit():
        return redirect(url_for('admin.gestionar_clientes', 
                              segmento=form.segmento.data, 
                              ordenar_por=form.ordenar_por.data))
    
    # Obtener filtros de la URL
    segmento_filtro = request.args.get('segmento', '')
    ordenar_por = request.args.get('ordenar_por', 'nombre')
    
    # Preseleccionar los valores del formulario
    form.segmento.data = segmento_filtro
    form.ordenar_por.data = ordenar_por
    
    # Configurar la consulta base
    query = Cliente.query
    
    # Aplicar filtros si existen
    if segmento_filtro:
        query = query.filter_by(segmento=segmento_filtro)
    
    # Aplicar ordenamiento
    if ordenar_por == 'visitas':
        query = query.order_by(Cliente.total_visitas.desc())
    elif ordenar_por == 'ultima_visita':
        query = query.order_by(Cliente.ultima_visita.desc())
    else:  # Por defecto, ordenar por nombre
        query = query.order_by(Cliente.nombre)
    
    # Ejecutar consulta
    clientes = query.all()
    
    # Estadísticas de segmentación
    stats = {
        'total': Cliente.query.count(),
        'nuevos': Cliente.query.filter_by(segmento='nuevo').count(),
        'ocasionales': Cliente.query.filter_by(segmento='ocasional').count(),
        'recurrentes': Cliente.query.filter_by(segmento='recurrente').count(),
        'vip': Cliente.query.filter_by(segmento='vip').count(),
        'inactivos': Cliente.query.filter_by(segmento='inactivo').count(),
    }
    
    return render_template(
        'admin/clientes.html',
        title='Gestionar Clientes',
        clientes=clientes,
        stats=stats,
        segmento_actual=segmento_filtro,
        ordenar_por=ordenar_por,
        form=form
    )


@bp.route('/clientes/<int:id>')
@login_required
@admin_required
def detalle_cliente(id):
        
    cliente = Cliente.query.get_or_404(id)
    
    # Obtener historial de citas
    citas = Cita.query.filter_by(cliente_id=cliente.id).order_by(Cita.fecha.desc()).all()
    
    # Calcular métricas
    total_gastado = sum(cita.servicio_rel.precio for cita in citas if cita.servicio_rel and cita.estado == 'completada')
    promedio_gasto = total_gastado / len(citas) if citas else 0
    
    return render_template(
        'admin/detalle_cliente.html',
        title=f'Cliente: {cliente.nombre}',
        cliente=cliente,
        citas=citas,
        total_gastado=total_gastado,
        promedio_gasto=promedio_gasto
    )


@bp.route('/clientes/actualizar-segmentos', methods=['POST'])
@login_required
@admin_required
def actualizar_segmentos():
        
    # Obtener todos los clientes
    clientes = Cliente.query.all()
    count = 0
    
    try:
        for cliente in clientes:
            if cliente.clasificar_segmento() != cliente.segmento:
                count += 1
        
        db.session.commit()
        flash(f'Segmentación actualizada para {count} clientes.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al actualizar segmentación: {str(e)}', 'danger')
        
    return redirect(url_for('admin.gestionar_clientes'))

# ================================
# GESTIÓN DE SLIDERS
# ================================


