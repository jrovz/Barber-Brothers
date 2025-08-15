# -*- coding: utf-8 -*-
"""
Middleware de Negocio para Barber Brothers
=========================================

Middleware que procesa automáticamente cookies comerciales y
optimiza la experiencia del usuario para maximizar conversiones.

Author: AI Assistant
Version: 1.0
"""

from flask import request, g, current_app
import json
from datetime import datetime
from app.utils.business_cookies import BusinessCookieManager, ConversionOptimizer
from app.utils.cart_optimizer import CartOptimizer, PurchaseIncentiveManager

class BusinessMiddleware:
    """Middleware para procesamiento automático de lógica comercial"""
    
    def __init__(self, app=None):
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Inicializar middleware con la aplicación Flask"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        
        # Configurar logging específico para métricas de negocio
        if not app.logger.handlers:
            import logging
            handler = logging.StreamHandler()
            handler.setLevel(logging.INFO)
            formatter = logging.Formatter(
                '%(asctime)s - BUSINESS - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            app.logger.addHandler(handler)
    
    def before_request(self):
        """Procesar datos antes de cada request"""
        try:
            # 1. Cargar datos de personalización
            g.personalization = BusinessCookieManager.get_personalization_data()
            
            # 2. Calcular probabilidad de conversión
            g.conversion_probability = BusinessCookieManager.calculate_conversion_probability()
            
            # 3. Cargar recomendaciones inteligentes
            g.smart_recommendations = ConversionOptimizer.get_smart_recommendations()
            
            # 4. Datos del carrito persistente
            g.persistent_cart = CartOptimizer.load_persistent_cart()
            
            # 5. Calcular riesgo de abandono
            g.cart_abandonment_risk = CartOptimizer.calculate_cart_abandonment_risk()
            
            # 6. Incentivos de compra
            g.shipping_incentive = PurchaseIncentiveManager.should_show_shipping_incentive()
            
            # 7. Determinar estrategia de conversión
            g.conversion_strategy = self._determine_conversion_strategy()
            
            # 8. Tracking de sesión para analytics
            self._track_session_start()
            
            # Log para monitoreo
            current_app.logger.info(
                f"Request processed: User type: {g.conversion_strategy.get('user_type', 'unknown')}, "
                f"Conversion probability: {g.conversion_probability:.2f}, "
                f"Cart value: {g.persistent_cart.get('estimated_total', 0) if g.persistent_cart else 0}"
            )
            
        except Exception as e:
            # Fallar silenciosamente para no afectar la funcionalidad
            current_app.logger.error(f"Business middleware error: {str(e)}")
            g.personalization = {}
            g.conversion_probability = 0.0
            g.smart_recommendations = {}
    
    def after_request(self, response):
        """Procesar datos después de cada response"""
        try:
            # 1. Actualizar métricas de sesión
            self._update_session_metrics(response)
            
            # 2. Aplicar optimizaciones de conversión
            response = self._apply_conversion_optimizations(response)
            
            # 3. Headers para analytics
            response.headers['X-Conversion-Probability'] = str(g.get('conversion_probability', 0))
            response.headers['X-User-Segment'] = g.get('conversion_strategy', {}).get('user_type', 'unknown')
            
        except Exception as e:
            current_app.logger.error(f"Business middleware after_request error: {str(e)}")
        
        return response
    
    def _determine_conversion_strategy(self):
        """
        Determina estrategia de conversión basada en datos del usuario
        
        Returns:
            Dict con estrategia de conversión
        """
        personalization = g.get('personalization', {})
        probability = g.get('conversion_probability', 0)
        cart_risk = g.get('cart_abandonment_risk', 0)
        
        strategy = {
            'user_type': 'new_visitor',
            'priority_level': 'normal',
            'show_incentives': False,
            'personalization_level': 'basic',
            'urgency_messaging': False,
            'discount_eligible': False
        }
        
        # Clasificar tipo de usuario
        if personalization.get('client', {}).get('is_returning'):
            if personalization.get('preferences', {}).get('total_reservas', 0) >= 3:
                strategy['user_type'] = 'loyal_customer'
                strategy['priority_level'] = 'high'
                strategy['discount_eligible'] = True
            else:
                strategy['user_type'] = 'returning_visitor'
                strategy['priority_level'] = 'medium'
        
        # Ajustar estrategia por probabilidad de conversión
        if probability > 0.7:
            strategy['personalization_level'] = 'high'
            strategy['show_incentives'] = False  # No necesita incentivos
        elif probability > 0.4:
            strategy['personalization_level'] = 'medium'
            strategy['show_incentives'] = True
        else:
            strategy['show_incentives'] = True
            strategy['urgency_messaging'] = cart_risk > 0.6
        
        # Estrategia especial para carrito abandonado
        if cart_risk > 0.5:
            strategy['show_incentives'] = True
            strategy['urgency_messaging'] = True
            if cart_risk > 0.7:
                strategy['discount_eligible'] = True
        
        return strategy
    
    def _track_session_start(self):
        """Rastrea inicio de sesión para analytics"""
        session_cookie = request.cookies.get('booking_session_tracker')
        
        if not session_cookie:
            # Nueva sesión
            g.is_new_session = True
            g.session_start_time = datetime.now()
        else:
            try:
                session_data = json.loads(session_cookie)
                g.is_new_session = False
                g.session_start_time = datetime.fromisoformat(
                    session_data.get('session_start', datetime.now().isoformat())
                )
            except:
                g.is_new_session = True
                g.session_start_time = datetime.now()
    
    def _update_session_metrics(self, response):
        """Actualiza métricas de la sesión actual"""
        if not hasattr(g, 'is_new_session'):
            return response
        
        # Actualizar tiempo de sesión
        current_time = datetime.now()
        session_duration = (current_time - g.session_start_time).total_seconds()
        
        # Determinar tipo de página para tracking
        page_type = self._get_page_type(request.path)
        
        # Actualizar session tracker si es nueva sesión o página importante
        if g.is_new_session or page_type in ['booking', 'checkout', 'products']:
            response = BusinessCookieManager.update_booking_step(
                response, 
                page_type, 
                {
                    'session_duration': session_duration,
                    'page_path': request.path,
                    'user_agent': request.headers.get('User-Agent', '')[:100]
                }
            )
        
        return response
    
    def _apply_conversion_optimizations(self, response):
        """Aplica optimizaciones específicas de conversión"""
        strategy = g.get('conversion_strategy', {})
        
        # Headers para personalización en frontend
        if strategy.get('show_incentives'):
            response.headers['X-Show-Incentives'] = 'true'
        
        if strategy.get('urgency_messaging'):
            response.headers['X-Urgency-Level'] = 'high'
        
        if strategy.get('discount_eligible'):
            response.headers['X-Discount-Eligible'] = 'true'
        
        # Cookie de estrategia para JavaScript
        if strategy:
            response.set_cookie(
                'conversion_strategy',
                json.dumps({
                    'user_type': strategy['user_type'],
                    'show_incentives': strategy['show_incentives'],
                    'urgency_messaging': strategy['urgency_messaging'],
                    'discount_eligible': strategy['discount_eligible']
                }),
                max_age=3600,  # 1 hora
                secure=True,
                httponly=False,  # Accesible desde JS
                samesite='Lax'
            )
        
        return response
    
    def _get_page_type(self, path):
        """
        Determina el tipo de página basado en la ruta
        
        Args:
            path: Ruta de la request
            
        Returns:
            String con tipo de página
        """
        if path == '/':
            return 'home'
        elif 'booking' in path or 'agendar' in path:
            return 'booking'
        elif 'checkout' in path:
            return 'checkout'
        elif 'productos' in path:
            return 'products'
        elif 'servicios' in path:
            return 'services'
        elif 'admin' in path:
            return 'admin'
        elif 'barbero' in path:
            return 'barber_panel'
        else:
            return 'other'


class ConversionMetricsCollector:
    """Recolector de métricas de conversión en tiempo real"""
    
    @staticmethod
    def collect_page_metrics():
        """
        Recolecta métricas de la página actual
        
        Returns:
            Dict con métricas de la página
        """
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'path': request.path,
            'method': request.method,
            'user_agent': request.headers.get('User-Agent', '')[:50],
            'referrer': request.headers.get('Referer', ''),
            'conversion_probability': g.get('conversion_probability', 0),
            'user_type': g.get('conversion_strategy', {}).get('user_type', 'unknown'),
            'cart_value': 0,
            'session_duration': 0
        }
        
        # Añadir valor del carrito si existe
        if g.get('persistent_cart'):
            metrics['cart_value'] = g.persistent_cart.get('estimated_total', 0)
        
        # Calcular duración de sesión
        if hasattr(g, 'session_start_time'):
            duration = (datetime.now() - g.session_start_time).total_seconds()
            metrics['session_duration'] = duration
        
        return metrics
    
    @staticmethod
    def should_trigger_conversion_event():
        """
        Determina si se debe triggear un evento de conversión
        
        Returns:
            Tuple (should_trigger: bool, event_type: str)
        """
        probability = g.get('conversion_probability', 0)
        page_type = BusinessMiddleware()._get_page_type(request.path)
        cart_risk = g.get('cart_abandonment_risk', 0)
        
        # Evento de alta probabilidad de conversión
        if probability > 0.8 and page_type == 'booking':
            return True, 'high_intent_booking'
        
        # Evento de carrito en riesgo
        if cart_risk > 0.7 and page_type != 'checkout':
            return True, 'cart_abandonment_risk'
        
        # Evento de cliente VIP
        user_type = g.get('conversion_strategy', {}).get('user_type')
        if user_type == 'loyal_customer' and page_type in ['booking', 'products']:
            return True, 'vip_engagement'
        
        return False, None
