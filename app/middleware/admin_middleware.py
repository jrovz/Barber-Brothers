# filepath: app/middleware/admin_middleware.py
"""
Middleware especializado para administradores.

Este middleware carga automáticamente las preferencias y configuraciones
de los administradores desde cookies para mejorar su experiencia de uso.
"""

from flask import g, request, current_app
from flask_login import current_user
from app.utils.admin_cookies import AdminCookieManager, AdminMetricsCalculator
import logging

logger = logging.getLogger('app.middleware.admin_middleware')

class AdminMiddleware:
    """Middleware para cargar preferencias de administradores"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Inicializa el middleware con la aplicación Flask"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        
        # Registrar funciones de contexto para templates
        app.jinja_env.globals['get_admin_dashboard_config'] = AdminCookieManager.get_dashboard_config
        app.jinja_env.globals['get_admin_table_preferences'] = AdminCookieManager.get_table_preferences
        app.jinja_env.globals['get_admin_quick_access'] = AdminCookieManager.get_quick_access_data
        app.jinja_env.globals['get_admin_interface_settings'] = AdminCookieManager.get_interface_settings
        
        logger.info("Admin middleware initialized")
    
    def before_request(self):
        """Procesa cookies y configuraciones antes de cada request de admin"""
        
        # Solo aplicar en rutas de administración
        if not request.endpoint or not request.endpoint.startswith('admin.'):
            return
        
        # Solo para usuarios autenticados que sean administradores
        if not current_user.is_authenticated:
            return
            
        try:
            if not hasattr(current_user, 'is_admin') or not current_user.is_admin():
                return
        except:
            return
        
        try:
            # Cargar configuraciones del administrador
            g.admin_dashboard_config = AdminCookieManager.get_dashboard_config() or {}
            g.admin_interface_settings = AdminCookieManager.get_interface_settings() or {}
            g.admin_metrics_config = AdminCookieManager.get_metrics_config() or {}
            g.admin_quick_access = AdminCookieManager.get_quick_access_data() or {}
            
            # Cargar preferencias de tabla específica según la ruta
            table_name = self._get_table_name_from_endpoint(request.endpoint)
            if table_name:
                g.admin_table_preferences = AdminCookieManager.get_table_preferences(table_name)
            
            # Cargar historial de filtros según la sección
            section = self._get_section_from_endpoint(request.endpoint)
            if section:
                g.admin_filter_history = AdminCookieManager.get_filter_history(section)
            
            # Calcular métricas si es el dashboard
            if request.endpoint == 'admin.dashboard':
                try:
                    g.admin_productivity_metrics = AdminMetricsCalculator.calculate_productivity_metrics()
                    g.admin_trending_data = AdminMetricsCalculator.get_trending_data()
                except Exception as e:
                    logger.error(f"Error calculating dashboard metrics: {e}")
                    g.admin_productivity_metrics = {'error': str(e)}
                    g.admin_trending_data = {'error': str(e)}
            
            # Información de contexto para templates
            g.admin_context = {
                'current_section': section,
                'current_table': table_name,
                'is_dashboard': request.endpoint == 'admin.dashboard',
                'preferences_loaded': True
            }
            
            logger.debug(f"Admin preferences loaded for user {current_user.id} on {request.endpoint}")
            
        except Exception as e:
            logger.error(f"Error loading admin preferences: {e}")
            # Establecer valores por defecto en caso de error
            g.admin_dashboard_config = AdminCookieManager.DEFAULT_DASHBOARD_CONFIG.copy()
            g.admin_interface_settings = AdminCookieManager.DEFAULT_INTERFACE_SETTINGS.copy()
            g.admin_table_preferences = AdminCookieManager.DEFAULT_TABLE_PREFERENCES.copy()
            g.admin_metrics_config = {}
            g.admin_quick_access = {}
            g.admin_productivity_metrics = {}
            g.admin_trending_data = {}
            g.admin_filter_history = []
            g.admin_context = {'preferences_loaded': False, 'error': str(e)}
    
    def after_request(self, response):
        """Procesa y guarda configuraciones después del request"""
        
        # Solo en rutas de administración
        if not request.endpoint or not request.endpoint.startswith('admin.'):
            return response
        
        # Solo para administradores autenticados
        if not current_user.is_authenticated:
            return response
            
        try:
            if not hasattr(current_user, 'is_admin') or not current_user.is_admin():
                return response
        except:
            return response
        
        try:
            # Rastrear acceso a entidades para acceso rápido
            self._track_entity_access(response)
            
            # Guardar filtros utilizados
            self._save_filter_usage(response)
            
            # Actualizar métricas de uso de la interfaz
            self._update_interface_metrics(response)
            
        except Exception as e:
            logger.error(f"Error in admin after_request: {e}")
        
        return response
    
    def _get_table_name_from_endpoint(self, endpoint: str) -> str:
        """Determina el nombre de la tabla según el endpoint"""
        endpoint_table_map = {
            'admin.gestionar_productos': 'productos',
            'admin.editar_producto': 'productos',
            'admin.gestionar_barberos': 'barberos',
            'admin.editar_barbero': 'barberos',
            'admin.gestionar_servicios': 'servicios',
            'admin.editar_servicio': 'servicios',
            'admin.gestionar_citas': 'citas',
            'admin.editar_cita': 'citas',
            'admin.gestionar_clientes': 'clientes',
            'admin.detalle_cliente': 'clientes',
            'admin.gestionar_categorias': 'categorias',
            'admin.editar_categoria': 'categorias',
            'admin.gestionar_sliders': 'sliders',
            'admin.editar_slider': 'sliders'
        }
        
        return endpoint_table_map.get(endpoint, '')
    
    def _get_section_from_endpoint(self, endpoint: str) -> str:
        """Determina la sección según el endpoint"""
        if 'producto' in endpoint:
            return 'productos'
        elif 'barbero' in endpoint:
            return 'barberos'
        elif 'servicio' in endpoint:
            return 'servicios'
        elif 'cita' in endpoint:
            return 'citas'
        elif 'cliente' in endpoint:
            return 'clientes'
        elif 'categoria' in endpoint:
            return 'categorias'
        elif 'slider' in endpoint:
            return 'sliders'
        elif 'dashboard' in endpoint:
            return 'dashboard'
        
        return 'general'
    
    def _track_entity_access(self, response):
        """Rastrea el acceso a entidades para construir acceso rápido"""
        
        # Solo rastrear en páginas de detalle/edición
        if request.endpoint in ['admin.editar_producto', 'admin.editar_barbero', 
                               'admin.editar_servicio', 'admin.detalle_cliente']:
            
            # Obtener ID de la URL
            entity_id = request.view_args.get('id')
            if not entity_id:
                return
            
            # Determinar tipo de entidad y nombre
            entity_type = None
            entity_name = None
            
            if 'producto' in request.endpoint:
                entity_type = 'producto'
                # Intentar obtener el nombre del producto (requeriría query adicional)
                entity_name = f"Producto #{entity_id}"
                
            elif 'barbero' in request.endpoint:
                entity_type = 'barbero'
                entity_name = f"Barbero #{entity_id}"
                
            elif 'servicio' in request.endpoint:
                entity_type = 'servicio'
                entity_name = f"Servicio #{entity_id}"
                
            elif 'cliente' in request.endpoint:
                entity_type = 'cliente'
                entity_name = f"Cliente #{entity_id}"
            
            if entity_type and entity_name:
                AdminCookieManager.track_entity_access(
                    response, entity_type, entity_id, entity_name
                )
    
    def _save_filter_usage(self, response):
        """Guarda el uso de filtros automáticamente"""
        
        # Solo en páginas de listado con filtros
        if request.method == 'GET' and any(param in request.args for param in 
                                         ['estado', 'fecha', 'barbero_id', 'servicio_id', 'segmento', 'ordenar_por']):
            
            section = self._get_section_from_endpoint(request.endpoint)
            if section:
                filter_data = {}
                
                # Capturar filtros comunes
                for param in ['estado', 'fecha', 'barbero_id', 'servicio_id', 'segmento', 'ordenar_por']:
                    if param in request.args and request.args[param]:
                        filter_data[param] = request.args[param]
                
                if filter_data:
                    AdminCookieManager.save_filter_use(response, section, filter_data)
    
    def _update_interface_metrics(self, response):
        """Actualiza métricas de uso de la interfaz"""
        
        # Rastrear tiempo en páginas (se podría hacer con JavaScript)
        # Por ahora, solo contar visitas a páginas
        if hasattr(g, 'admin_interface_settings'):
            # Incrementar contador de uso de páginas (podría expandirse)
            pass


class AdminDashboardOptimizer:
    """Optimizador del dashboard de administradores basado en patrones de uso"""
    
    @staticmethod
    def get_personalized_widgets(admin_preferences: dict) -> list:
        """Retorna widgets personalizados según el uso del administrador"""
        
        default_widgets = ['stats', 'recent_messages', 'upcoming_appointments']
        configured_widgets = admin_preferences.get('widgets', default_widgets)
        
        # Agregar widgets inteligentes según métricas
        try:
            metrics = AdminMetricsCalculator.calculate_productivity_metrics()
            
            # Si hay productos con bajo stock, priorizar widget de inventario
            if metrics.get('low_stock_products', 0) > 0:
                if 'low_stock' not in configured_widgets:
                    configured_widgets.insert(1, 'low_stock')
            
            # Si hay muchas citas nuevas, priorizar widget de citas
            if metrics.get('week_appointments', 0) > 10:
                if 'upcoming_appointments' not in configured_widgets:
                    configured_widgets.append('upcoming_appointments')
                    
        except Exception as e:
            logger.warning(f"Error optimizing dashboard widgets: {e}")
        
        return configured_widgets
    
    @staticmethod
    def get_smart_kpis(admin_metrics_config: dict) -> dict:
        """Retorna KPIs inteligentes según configuración y contexto"""
        
        favorite_kpis = admin_metrics_config.get('favorite_kpis', [])
        
        try:
            metrics = AdminMetricsCalculator.calculate_productivity_metrics()
            trending = AdminMetricsCalculator.get_trending_data()
            
            smart_kpis = {}
            
            # KPIs basados en preferencias
            if 'revenue' in favorite_kpis:
                # Calcular ingresos estimados (se podría implementar)
                smart_kpis['revenue'] = {
                    'value': 'N/A', 
                    'label': 'Ingresos del Mes',
                    'trend': 'stable'
                }
            
            if 'appointments' in favorite_kpis:
                smart_kpis['appointments'] = {
                    'value': metrics.get('week_appointments', 0),
                    'label': 'Citas Esta Semana',
                    'trend': 'up' if metrics.get('week_appointments', 0) > 5 else 'stable'
                }
            
            if 'client_growth' in favorite_kpis:
                smart_kpis['client_growth'] = {
                    'value': metrics.get('new_clients_week', 0),
                    'label': 'Nuevos Clientes',
                    'trend': 'up' if metrics.get('new_clients_week', 0) > 2 else 'stable'
                }
            
            # KPI automático para alertas críticas
            if metrics.get('low_stock_products', 0) > 0:
                smart_kpis['inventory_alert'] = {
                    'value': metrics['low_stock_products'],
                    'label': 'Productos Bajo Stock',
                    'trend': 'down',
                    'alert': True
                }
            
            return smart_kpis
            
        except Exception as e:
            logger.error(f"Error calculating smart KPIs: {e}")
            return {}
