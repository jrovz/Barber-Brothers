"""Vista principal del dashboard de administracion con metricas agregadas."""
from flask import render_template, flash, current_app
from flask_login import login_required
from app.admin import bp
from app.utils.decorators import admin_required
from app.models.producto import Producto
from app.models.cliente import Mensaje, Cliente, Cita
from app.models.servicio import Servicio
from app.models.barbero import Barbero, DisponibilidadBarbero
from app import db
from datetime import datetime, time, timedelta

import logging

logger = logging.getLogger(__name__)


@bp.route('/')
@login_required
@admin_required
def dashboard():

    try:
        # Verificar conexión a la base de datos primero
        from sqlalchemy.sql import text
        from app import db
        db.session.execute(text("SELECT 1"))
        print("Admin dashboard: Conexión a la base de datos verificada correctamente")
        
        # Estadísticas básicas
        product_count = Producto.query.count()
        barber_count = Barbero.query.count()
        unread_messages_count = Mensaje.query.filter_by(leido=False).count()
        recent_messages = Mensaje.query.order_by(Mensaje.creado.desc()).limit(5).all()
    
        # Estadísticas de clientes y segmentación
        cliente_count = Cliente.query.count()
        nuevos_clientes = Cliente.query.filter_by(segmento='nuevo').count()
        clientes_recurrentes = Cliente.query.filter_by(segmento='recurrente').count()
        clientes_vip = Cliente.query.filter_by(segmento='vip').count()
        clientes_inactivos = Cliente.query.filter_by(segmento='inactivo').count()
    except Exception as e:
        print(f"Error al consultar datos para el dashboard: {str(e)}")
        # Inicializar con valores predeterminados en caso de error
        product_count = 0
        barber_count = 0
        unread_messages_count = 0
        recent_messages = []
        cliente_count = 0
        nuevos_clientes = 0
        clientes_recurrentes = 0
        clientes_vip = 0
        clientes_inactivos = 0
    
    # Citas y ocupación
    today = datetime.today().date()
    tomorrow = today + timedelta(days=1)
    this_month_start = today.replace(day=1)
    next_month_start = (this_month_start + timedelta(days=32)).replace(day=1)
    
    # Citas próximas
    proximas_citas = Cita.query.filter(
        Cita.fecha >= datetime.now(),
        Cita.fecha <= datetime.now() + timedelta(days=7),
        Cita.estado != 'cancelada'
    ).order_by(Cita.fecha).limit(10).all()
    
    # Citas expiradas (para notificación)
    citas_expiradas = Cita.query.filter(
        Cita.estado == 'expirada'
    ).order_by(Cita.fecha.desc()).limit(10).all()
    
    # Citas pendientes de confirmación
    citas_pendientes = Cita.query.filter_by(estado='pendiente_confirmacion').count()
    
    # Ejecutar limpieza de citas expiradas (aquellas pendientes que pasaron el tiempo límite)
    try:
        citas_limpiadas = Cita.limpiar_citas_expiradas()
        if citas_limpiadas > 0:
            flash(f'Se han detectado {citas_limpiadas} citas expiradas sin confirmar', 'warning')
    except Exception as e:
        current_app.logger.error(f"Error al limpiar citas expiradas: {str(e)}")
        print(f"Error al limpiar citas expiradas: {str(e)}")
    
    # Citas de hoy
    citas_hoy = Cita.query.filter(
        Cita.fecha >= datetime.combine(today, time.min),
        Cita.fecha < datetime.combine(tomorrow, time.min)
    ).count()
    
    # Citas del mes
    citas_mes = Cita.query.filter(
        Cita.fecha >= datetime.combine(this_month_start, time.min),
        Cita.fecha < datetime.combine(next_month_start, time.min)
    ).count()
    
    # Estadísticas por barbero
    # Una sola query agregada por métrica en vez de 2 queries por barbero (evita N+1)
    barberos = Barbero.query.all()
    barbero_ids = [b.id for b in barberos]

    citas_por_barbero = dict(
        db.session.query(Cita.barbero_id, db.func.count(Cita.id))
        .filter(
            Cita.barbero_id.in_(barbero_ids),
            Cita.fecha >= datetime.combine(this_month_start, time.min),
            Cita.fecha < datetime.combine(next_month_start, time.min)
        )
        .group_by(Cita.barbero_id)
        .all()
    )

    horas_disponibles_por_barbero = {}
    for disp in DisponibilidadBarbero.query.filter(
        DisponibilidadBarbero.barbero_id.in_(barbero_ids),
        DisponibilidadBarbero.activo == True
    ).all():
        # Calculamos horas disponibles por día para ese bloque
        delta = datetime.combine(today, disp.hora_fin) - datetime.combine(today, disp.hora_inicio)
        horas_disponibles_por_barbero[disp.barbero_id] = (
            horas_disponibles_por_barbero.get(disp.barbero_id, 0) + delta.total_seconds() / 3600
        )

    stats_barberos = []
    for barbero in barberos:
        citas_barbero = citas_por_barbero.get(barbero.id, 0)
        horas_disponibles = horas_disponibles_por_barbero.get(barbero.id, 0)

        # La tasa sería un estimado (mejorable con datos reales de duración de citas)
        tasa_ocupacion = round((citas_barbero / (horas_disponibles * 4)) * 100) if horas_disponibles > 0 else 0

        stats_barberos.append({
            'id': barbero.id,
            'nombre': barbero.nombre,
            'citas': citas_barbero,
            'ocupacion': min(tasa_ocupacion, 100)  # Limitar a 100% máximo
        })
    
    # Servicios más solicitados
    top_servicios = db.session.query(
        Servicio.nombre, 
        db.func.count(Cita.id).label('total')
    ).join(Cita, Servicio.id == Cita.servicio_id)\
     .group_by(Servicio.nombre)\
     .order_by(db.desc('total'))\
     .limit(5).all()
      # Productos con bajo stock
    productos_bajo_stock = Producto.query.filter(Producto.cantidad <= 5).order_by(Producto.cantidad).all()
    
    # Datos para gráfico de segmentación de clientes
    segmentos_data = {
        'labels': ['Nuevos', 'Ocasionales', 'Recurrentes', 'VIP', 'Inactivos'],
        'data': [
            nuevos_clientes,
            Cliente.query.filter_by(segmento='ocasional').count(),
            clientes_recurrentes,
            clientes_vip,
            clientes_inactivos
        ]
    }

    # NUEVO: Usar configuraciones personalizadas del administrador
    from flask import g
    from app.middleware.admin_middleware import AdminDashboardOptimizer
    from app.utils.admin_cookies import AdminCookieManager
    
    # Obtener configuraciones personalizadas (cargadas por middleware)
    dashboard_config = getattr(g, 'admin_dashboard_config', AdminCookieManager.DEFAULT_DASHBOARD_CONFIG.copy())
    metrics_config = getattr(g, 'admin_metrics_config', {})
    interface_settings = getattr(g, 'admin_interface_settings', AdminCookieManager.DEFAULT_INTERFACE_SETTINGS.copy())
    productivity_metrics = getattr(g, 'admin_productivity_metrics', {})
    trending_data = getattr(g, 'admin_trending_data', {})
    
    # Personalizar widgets según configuración
    widgets_to_show = AdminDashboardOptimizer.get_personalized_widgets(dashboard_config)
    smart_kpis = AdminDashboardOptimizer.get_smart_kpis(metrics_config)
    
    # Configurar período de métricas según preferencias
    metrics_period = dashboard_config.get('metrics_period', 'month')
    
    return render_template(
        'admin/dashboard.html', 
        title='Dashboard Admin',
        product_count=product_count,
        barber_count=barber_count,
        cliente_count=cliente_count,
        nuevos_clientes=nuevos_clientes,
        clientes_recurrentes=clientes_recurrentes,
        clientes_vip=clientes_vip,
        segmentos_data=segmentos_data,
        unread_messages_count=unread_messages_count,
        recent_messages=recent_messages,
        proximas_citas=proximas_citas,
        citas_expiradas=citas_expiradas,
        citas_pendientes=citas_pendientes,
        citas_hoy=citas_hoy,
        citas_mes=citas_mes,
        stats_barberos=stats_barberos,
        top_servicios=top_servicios,
        productos_bajo_stock=productos_bajo_stock,
        # NUEVO: Variables de personalización
        dashboard_config=dashboard_config,
        metrics_config=metrics_config,
        interface_settings=interface_settings,
        widgets_to_show=widgets_to_show,
        smart_kpis=smart_kpis,
        metrics_period=metrics_period,
        productivity_metrics=productivity_metrics,
        trending_data=trending_data
    )

# --- Gestión de Productos (CRUD) ---

