# -*- coding: utf-8 -*-
"""
Optimizador de Carrito de Compras - Barber Brothers
=================================================

Sistema avanzado para maximizar conversiones en e-commerce
usando cookies inteligentes y algoritmos de recomendación.

Author: AI Assistant
Version: 1.0
"""

from flask import request, make_response, current_app
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from app.utils.business_cookies import BusinessCookieManager

class CartOptimizer:
    """Optimizador inteligente para carrito de compras"""
    
    @staticmethod
    def save_persistent_cart(response, cart_items: List[Dict]):
        """
        Guarda carrito de forma persistente con optimizaciones
        
        Args:
            response: Flask response
            cart_items: Lista de items del carrito
            
        Returns:
            Response con carrito optimizado guardado
        """
        # Optimizar estructura del carrito
        optimized_cart = {
            'items': cart_items,
            'timestamp': datetime.now().isoformat(),
            'session_id': request.cookies.get('session', 'anonymous'),
            'total_items': sum(item.get('quantity', 1) for item in cart_items),
            'estimated_total': sum(
                float(item.get('price', 0)) * int(item.get('quantity', 1)) 
                for item in cart_items
            ),
            'cart_hash': CartOptimizer._generate_cart_hash(cart_items)
        }
        
        # Guardar con mayor duración si el carrito tiene valor alto
        max_age = 7*24*60*60  # 7 días por defecto
        if optimized_cart['estimated_total'] > 100000:  # > 100k COP
            max_age = 14*24*60*60  # 14 días para carritos valiosos
        
        response.set_cookie(
            'persistent_cart',
            json.dumps(optimized_cart, separators=(',', ':')),
            max_age=max_age,
            secure=True,
            httponly=False,  # Necesario para JavaScript
            samesite='Lax'
        )
        
        # Log para métricas
        current_app.logger.info(
            f"Cart Saved: {optimized_cart['total_items']} items, "
            f"${optimized_cart['estimated_total']:,.0f} COP"
        )
        
        return response
    
    @staticmethod
    def load_persistent_cart():
        """
        Carga carrito persistente con validaciones
        
        Returns:
            Dict con datos del carrito o None si no existe/es inválido
        """
        cart_data = request.cookies.get('persistent_cart')
        if not cart_data:
            return None
        
        try:
            cart = json.loads(cart_data)
            
            # Validar que el carrito no sea muy antiguo
            cart_date = datetime.fromisoformat(cart.get('timestamp', ''))
            if datetime.now() - cart_date > timedelta(days=14):
                return None
            
            # Validar estructura
            if 'items' not in cart or not isinstance(cart['items'], list):
                return None
            
            return cart
            
        except (json.JSONDecodeError, ValueError, TypeError):
            return None
    
    @staticmethod
    def track_product_view(response, producto_id: int, producto_data: Dict):
        """
        Rastrea visualización de productos para recomendaciones
        
        Args:
            response: Flask response
            producto_id: ID del producto visto
            producto_data: Datos del producto (nombre, precio, categoría)
            
        Returns:
            Response con tracking actualizado
        """
        viewed_products = BusinessCookieManager.get_business_cookie('viewed_products', {})
        
        # Estructura optimizada para recomendaciones
        product_view = {
            'id': producto_id,
            'timestamp': datetime.now().isoformat(),
            'name': producto_data.get('nombre', ''),
            'price': float(producto_data.get('precio', 0)),
            'category': producto_data.get('categoria', ''),
            'view_count': viewed_products.get('products', {}).get(str(producto_id), {}).get('view_count', 0) + 1
        }
        
        # Mantener historial optimizado (últimos 50 productos)
        if 'products' not in viewed_products:
            viewed_products['products'] = {}
        if 'timeline' not in viewed_products:
            viewed_products['timeline'] = []
        
        # Actualizar producto específico
        viewed_products['products'][str(producto_id)] = product_view
        
        # Actualizar timeline (mantener últimos 50)
        viewed_products['timeline'] = [
            view for view in viewed_products['timeline'] 
            if view['id'] != producto_id
        ]
        viewed_products['timeline'].insert(0, {
            'id': producto_id, 
            'timestamp': product_view['timestamp']
        })
        viewed_products['timeline'] = viewed_products['timeline'][:50]
        
        # Estadísticas por categoría
        if 'category_stats' not in viewed_products:
            viewed_products['category_stats'] = {}
        
        category = product_view['category']
        if category:
            viewed_products['category_stats'][category] = \
                viewed_products['category_stats'].get(category, 0) + 1
        
        return BusinessCookieManager.set_business_cookie(
            response, 'viewed_products', viewed_products
        )
    
    @staticmethod
    def get_smart_recommendations(limit: int = 6):
        """
        Genera recomendaciones inteligentes basadas en comportamiento
        
        Args:
            limit: Número máximo de recomendaciones
            
        Returns:
            List de IDs de productos recomendados
        """
        viewed_data = BusinessCookieManager.get_business_cookie('viewed_products', {})
        cart_data = CartOptimizer.load_persistent_cart()
        
        recommendations = []
        
        # 1. Productos relacionados por categoría
        if viewed_data.get('category_stats'):
            favorite_category = max(
                viewed_data['category_stats'].items(), 
                key=lambda x: x[1]
            )[0]
            # Aquí se conectaría con la base de datos para obtener productos de la categoría
            
        # 2. Productos complementarios del carrito
        if cart_data and cart_data.get('items'):
            cart_product_ids = [item['id'] for item in cart_data['items']]
            # Lógica de productos complementarios
            
        # 3. Productos vistos recientemente pero no comprados
        if viewed_data.get('timeline'):
            recent_views = [
                view['id'] for view in viewed_data['timeline'][:10]
                if cart_data is None or 
                view['id'] not in [item['id'] for item in cart_data.get('items', [])]
            ]
            recommendations.extend(recent_views[:3])
        
        return recommendations[:limit]
    
    @staticmethod
    def calculate_cart_abandonment_risk():
        """
        Calcula riesgo de abandono del carrito
        
        Returns:
            Float entre 0 y 1 indicando riesgo de abandono
        """
        cart_data = CartOptimizer.load_persistent_cart()
        if not cart_data:
            return 0.0
        
        risk_score = 0.0
        
        # Tiempo desde última actividad
        last_activity = datetime.fromisoformat(cart_data['timestamp'])
        hours_since = (datetime.now() - last_activity).total_seconds() / 3600
        
        if hours_since > 24:
            risk_score += 0.4
        elif hours_since > 6:
            risk_score += 0.2
        
        # Valor del carrito (carritos más valiosos tienen menor abandono)
        cart_value = cart_data.get('estimated_total', 0)
        if cart_value < 50000:  # Menos de 50k COP
            risk_score += 0.3
        elif cart_value > 200000:  # Más de 200k COP
            risk_score -= 0.2
        
        # Número de items (pocos items = mayor riesgo)
        item_count = cart_data.get('total_items', 0)
        if item_count == 1:
            risk_score += 0.2
        elif item_count > 5:
            risk_score -= 0.1
        
        return max(0.0, min(1.0, risk_score))
    
    @staticmethod
    def get_cart_recovery_strategy():
        """
        Determina estrategia de recuperación de carrito
        
        Returns:
            Dict con estrategia recomendada
        """
        risk = CartOptimizer.calculate_cart_abandonment_risk()
        cart_data = CartOptimizer.load_persistent_cart()
        
        if risk < 0.3:
            return {'action': 'none', 'message': 'Low risk, no action needed'}
        
        strategy = {
            'risk_level': 'high' if risk > 0.7 else 'medium',
            'show_exit_intent': risk > 0.5,
            'offer_discount': risk > 0.6,
            'urgent_messaging': risk > 0.8,
            'discount_percentage': min(15, int(risk * 20)),  # Hasta 15%
            'message': '',
            'cta': ''
        }
        
        if cart_data:
            cart_value = cart_data.get('estimated_total', 0)
            
            if strategy['risk_level'] == 'high':
                strategy['message'] = f'¡Tu carrito de ${cart_value:,.0f} COP te está esperando!'
                strategy['cta'] = 'Finalizar Compra con Descuento'
            else:
                strategy['message'] = '¿Olvidaste algo en tu carrito?'
                strategy['cta'] = 'Ver Mi Carrito'
        
        return strategy
    
    @staticmethod
    def _generate_cart_hash(cart_items: List[Dict]) -> str:
        """
        Genera hash único del carrito para detectar cambios
        
        Args:
            cart_items: Items del carrito
            
        Returns:
            String hash del carrito
        """
        import hashlib
        
        # Crear string único basado en items y cantidades
        cart_string = ''.join(
            f"{item.get('id', '')}{item.get('quantity', 1)}"
            for item in sorted(cart_items, key=lambda x: x.get('id', ''))
        )
        
        return hashlib.md5(cart_string.encode()).hexdigest()[:8]


class PurchaseIncentiveManager:
    """Gestor de incentivos de compra basados en comportamiento"""
    
    @staticmethod
    def should_show_shipping_incentive():
        """
        Determina si mostrar incentivo de envío gratuito
        
        Returns:
            Tuple (should_show: bool, incentive_data: dict)
        """
        cart_data = CartOptimizer.load_persistent_cart()
        if not cart_data:
            return False, {}
        
        cart_value = cart_data.get('estimated_total', 0)
        free_shipping_threshold = 100000  # 100k COP
        
        if cart_value >= free_shipping_threshold:
            return False, {}  # Ya tiene envío gratis
        
        missing_amount = free_shipping_threshold - cart_value
        percentage_complete = (cart_value / free_shipping_threshold) * 100
        
        should_show = percentage_complete >= 50  # Mostrar cuando esté al 50%
        
        incentive_data = {
            'missing_amount': missing_amount,
            'percentage_complete': percentage_complete,
            'threshold': free_shipping_threshold,
            'message': f'¡Añade ${missing_amount:,.0f} COP más y obtén envío GRATIS!',
            'urgency_level': 'high' if percentage_complete >= 80 else 'medium'
        }
        
        return should_show, incentive_data
    
    @staticmethod
    def get_cross_sell_opportunities():
        """
        Identifica oportunidades de venta cruzada
        
        Returns:
            List de productos para venta cruzada
        """
        cart_data = CartOptimizer.load_persistent_cart()
        viewed_data = BusinessCookieManager.get_business_cookie('viewed_products', {})
        
        opportunities = []
        
        if cart_data and cart_data.get('items'):
            cart_categories = set()
            cart_product_ids = set()
            
            # Analizar categorías en el carrito
            for item in cart_data['items']:
                cart_product_ids.add(item.get('id'))
                # Aquí se obtendría la categoría del producto desde la BD
            
            # Productos vistos pero no en carrito
            if viewed_data.get('timeline'):
                for view in viewed_data['timeline'][:10]:
                    if view['id'] not in cart_product_ids:
                        opportunities.append({
                            'product_id': view['id'],
                            'reason': 'recently_viewed',
                            'confidence': 0.7
                        })
        
        return opportunities[:5]  # Máximo 5 oportunidades
    
    @staticmethod
    def calculate_customer_lifetime_value():
        """
        Estima valor de vida del cliente basado en cookies
        
        Returns:
            Dict con estimación de CLV
        """
        viewed_data = BusinessCookieManager.get_business_cookie('viewed_products', {})
        booking_prefs = BusinessCookieManager.get_business_cookie('favorite_barber_service', {})
        cart_data = CartOptimizer.load_persistent_cart()
        
        clv_indicators = {
            'engagement_score': 0,
            'purchase_intent': 0,
            'loyalty_indicators': 0,
            'estimated_clv': 0
        }
        
        # Engagement score basado en productos vistos
        if viewed_data.get('timeline'):
            view_count = len(viewed_data['timeline'])
            clv_indicators['engagement_score'] = min(view_count * 10, 100)
        
        # Purchase intent basado en carrito
        if cart_data:
            cart_value = cart_data.get('estimated_total', 0)
            clv_indicators['purchase_intent'] = min(cart_value / 1000, 100)
        
        # Loyalty indicators basado en reservas
        if booking_prefs.get('total_bookings', 0) > 0:
            bookings = booking_prefs['total_bookings']
            clv_indicators['loyalty_indicators'] = min(bookings * 20, 100)
        
        # Estimación simple de CLV
        avg_scores = sum(clv_indicators.values()) / 3
        clv_indicators['estimated_clv'] = avg_scores * 5000  # Base de 5k COP por punto
        
        return clv_indicators
