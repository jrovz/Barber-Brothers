# -*- coding: utf-8 -*-
"""
Gestor de Cookies Comerciales para Barber Brothers
=================================================

Sistema optimizado para maximizar conversiones y retención de clientes.
Enfoque específico en ROI y métricas de negocio.

Author: AI Assistant
Version: 1.0
"""

from flask import request, make_response, current_app
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import hashlib

class BusinessCookieManager:
    """Gestor especializado en cookies que impactan directamente el negocio"""
    
    # Configuración optimizada para conversión
    BUSINESS_COOKIES = {
        # FASE 1: Fundación Comercial
        'client_booking_data': {
            'max_age': 180*24*60*60,  # 6 meses
            'secure': True, 
            'httponly': True,
            'business_value': 'HIGH',
            'conversion_impact': 45
        },
        'favorite_barber_service': {
            'max_age': 90*24*60*60,   # 3 meses
            'secure': True,
            'httponly': False,
            'business_value': 'HIGH',
            'conversion_impact': 35
        },
        'booking_session_tracker': {
            'max_age': 24*60*60,      # 24 horas
            'secure': True,
            'httponly': True,
            'business_value': 'HIGH',
            'conversion_impact': 30
        },
        
        # FASE 2: E-commerce Power
        'persistent_cart': {
            'max_age': 7*24*60*60,    # 7 días
            'secure': True,
            'httponly': False,
            'business_value': 'CRITICAL',
            'conversion_impact': 60
        },
        'viewed_products': {
            'max_age': 30*24*60*60,   # 30 días
            'secure': True,
            'httponly': False,
            'business_value': 'MEDIUM',
            'conversion_impact': 30
        },
        
        # FASE 3: Optimización Avanzada
        'quick_rebooking': {
            'max_age': 60*24*60*60,   # 2 meses
            'secure': True,
            'httponly': True,
            'business_value': 'HIGH',
            'conversion_impact': 40
        }
    }
    
    @staticmethod
    def set_business_cookie(response, name: str, value: Any, custom_config: Dict = None):
        """
        Establecer cookie comercial con tracking automático
        
        Args:
            response: Flask response object
            name: Nombre de la cookie
            value: Valor a almacenar
            custom_config: Configuración personalizada
            
        Returns:
            Response object con cookie establecida
        """
        config = BusinessCookieManager.BUSINESS_COOKIES.get(name, {})
        if custom_config:
            config.update(custom_config)
        
        # Serializar si es necesario
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False, separators=(',', ':'))
        
        # Establecer cookie con configuración optimizada
        response.set_cookie(
            name,
            value,
            max_age=config.get('max_age', 30*24*60*60),
            secure=config.get('secure', True),
            httponly=config.get('httponly', True),
            samesite='Lax'  # Optimizado para funcionalidad
        )
        
        # Log para métricas de negocio
        current_app.logger.info(
            f"Business Cookie Set: {name} | Impact: {config.get('conversion_impact', 0)}%"
        )
        
        return response
    
    @staticmethod
    def get_business_cookie(name: str, default=None):
        """
        Obtener cookie comercial con deserialización automática
        
        Args:
            name: Nombre de la cookie
            default: Valor por defecto
            
        Returns:
            Valor deserializado de la cookie
        """
        value = request.cookies.get(name, default)
        if value and value != default:
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        return default
    
    @staticmethod
    def track_booking_abandonment():
        """
        Rastrea abandono de reservas para optimización
        
        Returns:
            Dict con datos de abandono actual
        """
        session_data = BusinessCookieManager.get_business_cookie('booking_session_tracker', {})
        
        # Inicializar si es primera vez
        if not session_data:
            session_data = {
                'session_start': datetime.now().isoformat(),
                'steps_completed': [],
                'current_step': 'initial',
                'abandonment_points': []
            }
        
        return session_data
    
    @staticmethod
    def update_booking_step(response, step: str, data: Dict = None):
        """
        Actualiza progreso de reserva para análisis de abandono
        
        Args:
            response: Flask response
            step: Paso actual del booking
            data: Datos adicionales del paso
            
        Returns:
            Response con tracking actualizado
        """
        session_data = BusinessCookieManager.track_booking_abandonment()
        
        # Actualizar progreso
        session_data['current_step'] = step
        session_data['last_activity'] = datetime.now().isoformat()
        
        if step not in session_data['steps_completed']:
            session_data['steps_completed'].append(step)
        
        if data:
            session_data[f'{step}_data'] = data
        
        # Calcular score de intención de compra
        progress_score = len(session_data['steps_completed']) * 20
        session_data['intent_score'] = min(progress_score, 100)
        
        return BusinessCookieManager.set_business_cookie(
            response, 'booking_session_tracker', session_data
        )
    
    @staticmethod
    def save_client_data_smart(response, client_data: Dict):
        """
        Guarda datos del cliente de forma inteligente para auto-completar
        
        Args:
            response: Flask response
            client_data: Datos del cliente
            
        Returns:
            Response con datos guardados
        """
        # Filtrar datos sensibles y optimizar para auto-completar
        safe_data = {
            'nombre': client_data.get('nombre', '').strip(),
            'telefono': client_data.get('telefono', '').strip(),
            'email': client_data.get('email', '').strip().lower(),
            'last_update': datetime.now().isoformat(),
            'usage_count': BusinessCookieManager.get_business_cookie('client_booking_data', {}).get('usage_count', 0) + 1
        }
        
        # Validar datos antes de guardar
        if safe_data['nombre'] and safe_data['email'] and safe_data['telefono']:
            return BusinessCookieManager.set_business_cookie(
                response, 'client_booking_data', safe_data
            )
        
        return response
    
    @staticmethod
    def save_preferences_smart(response, barbero_id: int, servicio_id: int, hora: str):
        """
        Guarda preferencias de reserva de forma inteligente
        
        Args:
            response: Flask response
            barbero_id: ID del barbero seleccionado
            servicio_id: ID del servicio seleccionado
            hora: Hora de la reserva
            
        Returns:
            Response con preferencias guardadas
        """
        # Obtener preferencias existentes
        current_prefs = BusinessCookieManager.get_business_cookie('favorite_barber_service', {})
        
        # Actualizar con lógica de frecuencia
        barbero_count = current_prefs.get('barbero_stats', {}).get(str(barbero_id), 0) + 1
        servicio_count = current_prefs.get('servicio_stats', {}).get(str(servicio_id), 0) + 1
        
        # Determinar preferencia horaria
        hora_num = int(hora.split(':')[0])
        time_preference = 'morning' if hora_num < 12 else 'afternoon' if hora_num < 17 else 'evening'
        time_count = current_prefs.get('time_stats', {}).get(time_preference, 0) + 1
        
        updated_prefs = {
            'favorite_barbero': barbero_id if barbero_count >= 2 else current_prefs.get('favorite_barbero'),
            'favorite_servicio': servicio_id if servicio_count >= 2 else current_prefs.get('favorite_servicio'),
            'favorite_time': time_preference if time_count >= 2 else current_prefs.get('favorite_time'),
            'barbero_stats': {**current_prefs.get('barbero_stats', {}), str(barbero_id): barbero_count},
            'servicio_stats': {**current_prefs.get('servicio_stats', {}), str(servicio_id): servicio_count},
            'time_stats': {**current_prefs.get('time_stats', {}), time_preference: time_count},
            'last_booking': {
                'barbero_id': barbero_id,
                'servicio_id': servicio_id,
                'hora': hora,
                'fecha': datetime.now().isoformat()
            },
            'total_bookings': current_prefs.get('total_bookings', 0) + 1
        }
        
        return BusinessCookieManager.set_business_cookie(
            response, 'favorite_barber_service', updated_prefs
        )
    
    @staticmethod
    def get_personalization_data():
        """
        Obtiene todos los datos de personalización para la interfaz
        
        Returns:
            Dict con datos de personalización completos
        """
        client_data = BusinessCookieManager.get_business_cookie('client_booking_data', {})
        preferences = BusinessCookieManager.get_business_cookie('favorite_barber_service', {})
        session_data = BusinessCookieManager.get_business_cookie('booking_session_tracker', {})
        
        return {
            'client': {
                'nombre': client_data.get('nombre', ''),
                'email': client_data.get('email', ''),
                'telefono': client_data.get('telefono', ''),
                'is_returning': client_data.get('usage_count', 0) > 1
            },
            'preferences': {
                'barbero_favorito': preferences.get('favorite_barbero'),
                'servicio_favorito': preferences.get('favorite_servicio'),
                'horario_favorito': preferences.get('favorite_time'),
                'total_reservas': preferences.get('total_bookings', 0)
            },
            'session': {
                'current_step': session_data.get('current_step', 'initial'),
                'intent_score': session_data.get('intent_score', 0),
                'steps_completed': session_data.get('steps_completed', [])
            }
        }
    
    @staticmethod
    def calculate_conversion_probability():
        """
        Calcula probabilidad de conversión basada en cookies
        
        Returns:
            Float entre 0 y 1 indicando probabilidad de conversión
        """
        data = BusinessCookieManager.get_personalization_data()
        score = 0.1  # Base score
        
        # Cliente recurrente: +40%
        if data['client']['is_returning']:
            score += 0.4
        
        # Tiene preferencias definidas: +25%
        if data['preferences']['barbero_favorito'] or data['preferences']['servicio_favorito']:
            score += 0.25
        
        # Progreso en sesión actual: +35%
        if data['session']['intent_score'] > 60:
            score += 0.35
        elif data['session']['intent_score'] > 30:
            score += 0.20
        
        # Cliente frecuente: +20%
        if data['preferences']['total_reservas'] >= 3:
            score += 0.20
        
        return min(score, 1.0)
    
    @staticmethod
    def get_business_metrics():
        """
        Obtiene métricas de negocio basadas en cookies
        
        Returns:
            Dict con métricas calculadas
        """
        all_cookies = request.cookies
        metrics = {
            'returning_clients': 0,
            'high_intent_sessions': 0,
            'preference_completion': 0,
            'total_tracked_sessions': 0
        }
        
        # Analizar cookies para métricas
        for cookie_name, cookie_value in all_cookies.items():
            if cookie_name == 'client_booking_data':
                try:
                    data = json.loads(cookie_value)
                    if data.get('usage_count', 0) > 1:
                        metrics['returning_clients'] += 1
                except:
                    pass
            elif cookie_name == 'booking_session_tracker':
                try:
                    data = json.loads(cookie_value)
                    metrics['total_tracked_sessions'] += 1
                    if data.get('intent_score', 0) > 70:
                        metrics['high_intent_sessions'] += 1
                except:
                    pass
            elif cookie_name == 'favorite_barber_service':
                try:
                    data = json.loads(cookie_value)
                    if data.get('favorite_barbero') and data.get('favorite_servicio'):
                        metrics['preference_completion'] += 1
                except:
                    pass
        
        return metrics


class ConversionOptimizer:
    """Optimizador de conversiones basado en datos de cookies"""
    
    @staticmethod
    def get_smart_recommendations():
        """
        Genera recomendaciones inteligentes basadas en comportamiento
        
        Returns:
            Dict con recomendaciones personalizadas
        """
        data = BusinessCookieManager.get_personalization_data()
        recommendations = {
            'show_quick_booking': False,
            'suggested_barbero': None,
            'suggested_servicio': None,
            'suggested_time_slots': [],
            'discount_eligible': False,
            'priority_support': False
        }
        
        # Cliente recurrente: mostrar booking rápido
        if data['client']['is_returning']:
            recommendations['show_quick_booking'] = True
            recommendations['suggested_barbero'] = data['preferences']['barbero_favorito']
            recommendations['suggested_servicio'] = data['preferences']['servicio_favorito']
        
        # Cliente frecuente: beneficios especiales
        if data['preferences']['total_reservas'] >= 5:
            recommendations['discount_eligible'] = True
            recommendations['priority_support'] = True
        
        # Horarios sugeridos basados en preferencias
        fav_time = data['preferences']['horario_favorito']
        if fav_time == 'morning':
            recommendations['suggested_time_slots'] = ['09:00', '10:00', '11:00']
        elif fav_time == 'afternoon':
            recommendations['suggested_time_slots'] = ['14:00', '15:00', '16:00']
        elif fav_time == 'evening':
            recommendations['suggested_time_slots'] = ['17:00', '18:00', '19:00']
        
        return recommendations
    
    @staticmethod
    def should_show_exit_intent_popup():
        """
        Determina si mostrar popup de intención de salida
        
        Returns:
            Bool y dict con configuración del popup
        """
        probability = BusinessCookieManager.calculate_conversion_probability()
        session_data = BusinessCookieManager.get_personalization_data()['session']
        
        # Mostrar popup si:
        # - Probabilidad media-alta (0.3-0.7)
        # - Ha avanzado en el proceso pero no completó
        # - No es la primera visita
        
        show_popup = (
            0.3 <= probability <= 0.7 and
            session_data['intent_score'] > 40 and
            len(session_data['steps_completed']) > 1
        )
        
        popup_config = {
            'title': '¡Espera! ¿Necesitas ayuda?',
            'message': 'Vemos que estás interesado en agendar una cita. ¿Te ayudamos?',
            'offer': '10% de descuento en tu primera cita' if probability < 0.5 else 'Reserva prioritaria disponible',
            'urgency': probability > 0.6
        }
        
        return show_popup, popup_config
