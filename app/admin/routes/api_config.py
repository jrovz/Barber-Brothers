"""Endpoints AJAX internos para preferencias y metricas del dashboard."""
from flask import request, jsonify
from flask_login import login_required, current_user
from app.admin import bp
from app.utils.decorators import admin_required
from datetime import datetime

import logging

logger = logging.getLogger(__name__)


@bp.route('/api/save-dashboard-config', methods=['POST'])
@login_required
@admin_required
def save_dashboard_config():
    """Guarda la configuración del dashboard en cookies"""
    
    try:
        from flask import request, make_response, jsonify
        from app.utils.admin_cookies import AdminCookieManager
        
        config_data = request.get_json()
        if not config_data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        response = make_response(jsonify({'success': True, 'message': 'Configuración guardada'}))
        AdminCookieManager.save_dashboard_config(response, config_data)
        
        logger.info(f"Dashboard config saved for admin {current_user.id}")
        return response
        
    except Exception as e:
        logger.error(f"Error saving dashboard config: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/save-interface-setting', methods=['POST'])
@login_required
@admin_required
def save_interface_setting():
    """Guarda una configuración específica de interfaz"""
    
    try:
        from flask import request, make_response, jsonify
        from app.utils.admin_cookies import AdminCookieManager
        
        setting_data = request.get_json()
        if not setting_data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        response = make_response(jsonify({'success': True, 'message': 'Configuración guardada'}))
        
        # Guardar cada configuración
        for key, value in setting_data.items():
            AdminCookieManager.save_interface_setting(response, key, value)
        
        return response
        
    except Exception as e:
        logger.error(f"Error saving interface setting: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/refresh-metrics', methods=['POST'])
@login_required
@admin_required
def refresh_metrics():
    """Actualiza las métricas del dashboard"""
    
    try:
        from app.utils.admin_cookies import AdminMetricsCalculator
        
        metrics = AdminMetricsCalculator.calculate_productivity_metrics()
        trending = AdminMetricsCalculator.get_trending_data()
        
        return jsonify({
            'success': True,
            'metrics': metrics,
            'trending': trending,
            'updated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error refreshing metrics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/get-quick-access', methods=['GET'])
@login_required
@admin_required
def get_quick_access():
    """Obtiene datos de acceso rápido"""
    
    try:
        from app.utils.admin_cookies import AdminCookieManager
        
        quick_access = AdminCookieManager.get_quick_access_data()
        
        return jsonify({
            'success': True,
            'data': quick_access
        })
        
    except Exception as e:
        logger.error(f"Error getting quick access data: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
