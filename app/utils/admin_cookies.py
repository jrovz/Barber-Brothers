# filepath: app/utils/admin_cookies.py
"""
Gestor de cookies específicas para administradores.

Este módulo maneja las cookies que mejoran la productividad de los administradores:
- Configuraciones del dashboard personalizadas
- Filtros y vistas guardadas automáticamente
- Acceso rápido a datos frecuentes
- Métricas y KPIs personalizados
- Configuraciones de interfaz
"""

import json
from datetime import datetime, timedelta
from flask import request, current_app
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class AdminCookieManager:
    """Gestor especializado de cookies para administradores"""
    
    # Configuración de cookies
    COOKIE_NAMES = {
        'dashboard_config': 'admin_dashboard_config',
        'table_preferences': 'admin_table_prefs',
        'filter_history': 'admin_filter_history', 
        'quick_access': 'admin_quick_access',
        'interface_settings': 'admin_ui_settings',
        'metrics_config': 'admin_metrics_config'
    }
    
    # Configuración por defecto
    DEFAULT_DASHBOARD_CONFIG = {
        'widgets': ['stats', 'recent_messages', 'upcoming_appointments', 'low_stock'],
        'metrics_period': 'month',
        'chart_types': {
            'client_segmentation': 'doughnut',
            'barber_performance': 'bar',
            'service_popularity': 'bar'
        },
        'refresh_interval': 300,  # 5 minutos
        'compact_mode': False
    }
    
    DEFAULT_TABLE_PREFERENCES = {
        'rows_per_page': 10,
        'sort_column': 'id',
        'sort_direction': 'desc',
        'visible_columns': {},
        'compact_tables': False
    }
    
    DEFAULT_INTERFACE_SETTINGS = {
        'sidebar_collapsed': False,
        'theme': 'default',
        'notifications_enabled': True,
        'auto_refresh': True,
        'quick_actions_visible': True
    }
    
    @classmethod
    def get_dashboard_config(cls, admin_id: Optional[int] = None) -> Dict[str, Any]:
        """Obtiene la configuración del dashboard del administrador"""
        try:
            cookie_data = request.cookies.get(cls.COOKIE_NAMES['dashboard_config'])
            if cookie_data:
                config = json.loads(cookie_data)
                # Validar que tenga las claves necesarias
                for key in cls.DEFAULT_DASHBOARD_CONFIG:
                    if key not in config:
                        config[key] = cls.DEFAULT_DASHBOARD_CONFIG[key]
                return config
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Error al leer configuración del dashboard: {e}")
        
        return cls.DEFAULT_DASHBOARD_CONFIG.copy()
    
    @classmethod
    def save_dashboard_config(cls, response, config: Dict[str, Any]) -> None:
        """Guarda la configuración del dashboard"""
        try:
            # Validar configuración
            validated_config = cls._validate_dashboard_config(config)
            
            cookie_value = json.dumps(validated_config)
            expires = datetime.now() + timedelta(days=365)
            
            response.set_cookie(
                cls.COOKIE_NAMES['dashboard_config'],
                cookie_value,
                expires=expires,
                httponly=True,
                samesite='Lax'
            )
            
            logger.info(f"Dashboard config saved for admin")
            
        except Exception as e:
            logger.error(f"Error al guardar configuración del dashboard: {e}")
    
    @classmethod
    def get_table_preferences(cls, table_name: str) -> Dict[str, Any]:
        """Obtiene las preferencias de tabla específica"""
        try:
            cookie_data = request.cookies.get(cls.COOKIE_NAMES['table_preferences'])
            if cookie_data:
                all_prefs = json.loads(cookie_data)
                table_prefs = all_prefs.get(table_name, {})
                
                # Combinar con valores por defecto
                result = cls.DEFAULT_TABLE_PREFERENCES.copy()
                result.update(table_prefs)
                return result
                
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Error al leer preferencias de tabla {table_name}: {e}")
        
        return cls.DEFAULT_TABLE_PREFERENCES.copy()
    
    @classmethod
    def save_table_preferences(cls, response, table_name: str, preferences: Dict[str, Any]) -> None:
        """Guarda las preferencias de una tabla específica"""
        try:
            # Obtener preferencias existentes
            existing_prefs = {}
            cookie_data = request.cookies.get(cls.COOKIE_NAMES['table_preferences'])
            if cookie_data:
                existing_prefs = json.loads(cookie_data)
            
            # Actualizar con nuevas preferencias
            existing_prefs[table_name] = preferences
            
            cookie_value = json.dumps(existing_prefs)
            expires = datetime.now() + timedelta(days=365)
            
            response.set_cookie(
                cls.COOKIE_NAMES['table_preferences'],
                cookie_value,
                expires=expires,
                httponly=True,
                samesite='Lax'
            )
            
            logger.info(f"Table preferences saved for {table_name}")
            
        except Exception as e:
            logger.error(f"Error al guardar preferencias de tabla {table_name}: {e}")
    
    @classmethod
    def get_filter_history(cls, section: str) -> List[Dict[str, Any]]:
        """Obtiene el historial de filtros de una sección"""
        try:
            cookie_data = request.cookies.get(cls.COOKIE_NAMES['filter_history'])
            if cookie_data:
                all_history = json.loads(cookie_data)
                return all_history.get(section, [])
                
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Error al leer historial de filtros {section}: {e}")
        
        return []
    
    @classmethod
    def save_filter_use(cls, response, section: str, filter_data: Dict[str, Any]) -> None:
        """Guarda el uso de un filtro en el historial"""
        try:
            # Obtener historial existente
            existing_history = {}
            cookie_data = request.cookies.get(cls.COOKIE_NAMES['filter_history'])
            if cookie_data:
                existing_history = json.loads(cookie_data)
            
            # Inicializar sección si no existe
            if section not in existing_history:
                existing_history[section] = []
            
            # Agregar timestamp al filtro
            filter_entry = {
                **filter_data,
                'used_at': datetime.now().isoformat(),
                'count': 1
            }
            
            # Verificar si el filtro ya existe
            section_history = existing_history[section]
            existing_filter = None
            for i, item in enumerate(section_history):
                if cls._filters_match(item, filter_data):
                    existing_filter = i
                    break
            
            if existing_filter is not None:
                # Actualizar filtro existente
                section_history[existing_filter]['used_at'] = filter_entry['used_at']
                section_history[existing_filter]['count'] += 1
                # Mover al principio
                section_history.insert(0, section_history.pop(existing_filter))
            else:
                # Agregar nuevo filtro al principio
                section_history.insert(0, filter_entry)
            
            # Mantener solo los últimos 10 filtros
            existing_history[section] = section_history[:10]
            
            cookie_value = json.dumps(existing_history)
            expires = datetime.now() + timedelta(days=90)
            
            response.set_cookie(
                cls.COOKIE_NAMES['filter_history'],
                cookie_value,
                expires=expires,
                httponly=True,
                samesite='Lax'
            )
            
            logger.info(f"Filter history updated for {section}")
            
        except Exception as e:
            logger.error(f"Error al guardar historial de filtros {section}: {e}")
    
    @classmethod
    def get_quick_access_data(cls) -> Dict[str, Any]:
        """Obtiene los datos de acceso rápido"""
        try:
            cookie_data = request.cookies.get(cls.COOKIE_NAMES['quick_access'])
            if cookie_data:
                return json.loads(cookie_data)
                
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Error al leer datos de acceso rápido: {e}")
        
        return {
            'frequent_products': [],
            'frequent_clients': [],
            'frequent_barbers': [],
            'recent_searches': [],
            'bookmarked_reports': []
        }
    
    @classmethod
    def track_entity_access(cls, response, entity_type: str, entity_id: int, entity_name: str) -> None:
        """Rastrea el acceso a entidades para acceso rápido"""
        try:
            quick_access = cls.get_quick_access_data()
            
            # Determinar la lista correcta
            list_key = f'frequent_{entity_type}s'
            if list_key not in quick_access:
                quick_access[list_key] = []
            
            entity_list = quick_access[list_key]
            
            # Buscar si ya existe
            existing_index = None
            for i, item in enumerate(entity_list):
                if item['id'] == entity_id:
                    existing_index = i
                    break
            
            entity_data = {
                'id': entity_id,
                'name': entity_name,
                'last_accessed': datetime.now().isoformat(),
                'access_count': 1
            }
            
            if existing_index is not None:
                # Actualizar existente
                entity_list[existing_index]['last_accessed'] = entity_data['last_accessed']
                entity_list[existing_index]['access_count'] += 1
                # Mover al principio
                entity_list.insert(0, entity_list.pop(existing_index))
            else:
                # Agregar nuevo al principio
                entity_list.insert(0, entity_data)
            
            # Mantener solo los primeros 5
            quick_access[list_key] = entity_list[:5]
            
            cookie_value = json.dumps(quick_access)
            expires = datetime.now() + timedelta(days=30)
            
            response.set_cookie(
                cls.COOKIE_NAMES['quick_access'],
                cookie_value,
                expires=expires,
                httponly=True,
                samesite='Lax'
            )
            
        except Exception as e:
            logger.error(f"Error al rastrear acceso a {entity_type} {entity_id}: {e}")
    
    @classmethod
    def get_interface_settings(cls) -> Dict[str, Any]:
        """Obtiene la configuración de interfaz"""
        try:
            cookie_data = request.cookies.get(cls.COOKIE_NAMES['interface_settings'])
            if cookie_data:
                settings = json.loads(cookie_data)
                # Combinar con valores por defecto
                result = cls.DEFAULT_INTERFACE_SETTINGS.copy()
                result.update(settings)
                return result
                
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Error al leer configuración de interfaz: {e}")
        
        return cls.DEFAULT_INTERFACE_SETTINGS.copy()
    
    @classmethod
    def save_interface_setting(cls, response, setting_key: str, setting_value: Any) -> None:
        """Guarda una configuración específica de interfaz"""
        try:
            settings = cls.get_interface_settings()
            settings[setting_key] = setting_value
            
            cookie_value = json.dumps(settings)
            expires = datetime.now() + timedelta(days=365)
            
            response.set_cookie(
                cls.COOKIE_NAMES['interface_settings'],
                cookie_value,
                expires=expires,
                httponly=True,
                samesite='Lax'
            )
            
            logger.info(f"Interface setting saved: {setting_key} = {setting_value}")
            
        except Exception as e:
            logger.error(f"Error al guardar configuración de interfaz: {e}")
    
    @classmethod
    def get_metrics_config(cls) -> Dict[str, Any]:
        """Obtiene la configuración de métricas personalizadas"""
        try:
            cookie_data = request.cookies.get(cls.COOKIE_NAMES['metrics_config'])
            if cookie_data:
                return json.loads(cookie_data)
                
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Error al leer configuración de métricas: {e}")
        
        return {
            'favorite_kpis': ['revenue', 'appointments', 'client_growth'],
            'date_ranges': ['today', 'week', 'month'],
            'comparison_enabled': True,
            'alerts_enabled': True,
            'alert_thresholds': {
                'low_stock': 5,
                'appointment_cancellation_rate': 0.15,
                'revenue_drop': 0.20
            }
        }
    
    @classmethod
    def save_metrics_config(cls, response, config: Dict[str, Any]) -> None:
        """Guarda la configuración de métricas"""
        try:
            cookie_value = json.dumps(config)
            expires = datetime.now() + timedelta(days=365)
            
            response.set_cookie(
                cls.COOKIE_NAMES['metrics_config'],
                cookie_value,
                expires=expires,
                httponly=True,
                samesite='Lax'
            )
            
            logger.info("Metrics config saved")
            
        except Exception as e:
            logger.error(f"Error al guardar configuración de métricas: {e}")
    
    # Métodos auxiliares privados
    
    @classmethod
    def _validate_dashboard_config(cls, config: Dict[str, Any]) -> Dict[str, Any]:
        """Valida y sanea la configuración del dashboard"""
        validated = cls.DEFAULT_DASHBOARD_CONFIG.copy()
        
        # Validar widgets
        if 'widgets' in config and isinstance(config['widgets'], list):
            allowed_widgets = ['stats', 'recent_messages', 'upcoming_appointments', 'low_stock', 'charts']
            validated['widgets'] = [w for w in config['widgets'] if w in allowed_widgets]
        
        # Validar período de métricas
        if 'metrics_period' in config and config['metrics_period'] in ['day', 'week', 'month', 'quarter']:
            validated['metrics_period'] = config['metrics_period']
        
        # Validar tipos de gráficos
        if 'chart_types' in config and isinstance(config['chart_types'], dict):
            validated['chart_types'].update(config['chart_types'])
        
        # Validar intervalo de actualización
        if 'refresh_interval' in config and isinstance(config['refresh_interval'], int):
            if 60 <= config['refresh_interval'] <= 3600:  # Entre 1 minuto y 1 hora
                validated['refresh_interval'] = config['refresh_interval']
        
        # Validar modo compacto
        if 'compact_mode' in config and isinstance(config['compact_mode'], bool):
            validated['compact_mode'] = config['compact_mode']
        
        return validated
    
    @classmethod
    def _filters_match(cls, filter1: Dict[str, Any], filter2: Dict[str, Any]) -> bool:
        """Compara si dos filtros son equivalentes"""
        # Comparar solo los campos de filtro, no metadata como timestamp
        filter_keys = ['estado', 'fecha', 'barbero_id', 'servicio_id', 'segmento', 'ordenar_por']
        
        for key in filter_keys:
            if filter1.get(key) != filter2.get(key):
                return False
        return True


class AdminMetricsCalculator:
    """Calculador de métricas especializadas para administradores"""
    
    @staticmethod
    def calculate_productivity_metrics() -> Dict[str, Any]:
        """Calcula métricas de productividad del sistema"""
        try:
            from app.models.cliente import Cita, Cliente
            from app.models.producto import Producto 
            from app.models.barbero import Barbero
            from sqlalchemy import func
            from datetime import datetime, timedelta
        except ImportError as e:
            logger.error(f"Error importing models for metrics: {e}")
            return {'error': 'Could not import required models'}
        
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        metrics = {}
        
        try:
            # Métricas de citas
            total_appointments = Cita.query.count()
            week_appointments = Cita.query.filter(Cita.fecha >= week_ago).count()
            
            # Tasa de confirmación
            confirmed_week = Cita.query.filter(
                Cita.fecha >= week_ago,
                Cita.estado == 'confirmada'
            ).count()
            
            confirmation_rate = (confirmed_week / week_appointments) * 100 if week_appointments > 0 else 0
            
            # Métricas de clientes
            total_clients = Cliente.query.count()
            new_clients_week = Cliente.query.filter(Cliente.creado >= week_ago).count()
            
            # Productos con bajo stock
            low_stock_products = Producto.query.filter(Producto.cantidad <= 5).count()
            
            # Barberos activos
            active_barbers = Barbero.query.filter_by(activo=True).count()
            
            metrics = {
                'total_appointments': total_appointments,
                'week_appointments': week_appointments,
                'confirmation_rate': round(confirmation_rate, 1),
                'total_clients': total_clients,
                'new_clients_week': new_clients_week,
                'low_stock_products': low_stock_products,
                'active_barbers': active_barbers,
                'calculated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculando métricas de productividad: {e}")
            metrics = {'error': 'No se pudieron calcular las métricas'}
        
        return metrics
    
    @staticmethod
    def get_trending_data() -> Dict[str, Any]:
        """Obtiene datos de tendencias para el dashboard"""
        try:
            from app.models.cliente import Cita
            from app.models.servicio import Servicio
            from app.models.barbero import Barbero
            from sqlalchemy import func, desc
            from datetime import datetime, timedelta
        except ImportError as e:
            logger.error(f"Error importing models for trending data: {e}")
            return {'error': 'Could not import required models'}
        
        month_ago = datetime.now().date() - timedelta(days=30)
        
        try:
            # Servicios más populares del mes
            popular_services = (
                Cita.query
                .join(Servicio)
                .filter(Cita.fecha >= month_ago)
                .with_entities(Servicio.nombre, func.count(Cita.id).label('count'))
                .group_by(Servicio.nombre)
                .order_by(desc('count'))
                .limit(5)
                .all()
            )
            
            # Barberos con más citas
            top_barbers = (
                Cita.query
                .join(Barbero)
                .filter(Cita.fecha >= month_ago)
                .with_entities(Barbero.nombre, func.count(Cita.id).label('count'))
                .group_by(Barbero.nombre)
                .order_by(desc('count'))
                .limit(5)
                .all()
            )
            
            return {
                'popular_services': [{'name': s[0], 'count': s[1]} for s in popular_services],
                'top_barbers': [{'name': b[0], 'count': b[1]} for b in top_barbers],
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo datos de tendencias: {e}")
            return {'error': 'No se pudieron obtener las tendencias'}
