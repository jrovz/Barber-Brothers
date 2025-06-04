"""
Health Check Route for Barber Brothers Application
This module provides health check endpoints for monitoring
"""

from flask import Blueprint, jsonify
from app import db
import os
import sys
from datetime import datetime

health_bp = Blueprint('health', __name__)

@health_bp.route('/health')
def health_check():
    """Basic health check endpoint"""
    try:
        # Check database connection
        db.session.execute('SELECT 1')
        db_status = 'healthy'
    except Exception as e:
        db_status = f'unhealthy: {str(e)}'
    
    # Check application status
    app_status = 'healthy'
    
    # Get basic system info
    system_info = {
        'timestamp': datetime.utcnow().isoformat(),
        'python_version': sys.version,
        'environment': os.getenv('FLASK_ENV', 'production'),
        'database': db_status,
        'application': app_status
    }
    
    # Return appropriate status code
    status_code = 200 if db_status == 'healthy' else 503
    
    return jsonify(system_info), status_code

@health_bp.route('/health/detailed')
def detailed_health_check():
    """Detailed health check with more information"""
    try:
        # Database checks
        db.session.execute('SELECT 1')
        db_connection = 'ok'
        
        # Count some basic tables (adjust based on your models)
        try:
            from app.models import User
            user_count = User.query.count()
            db_data = 'ok'
        except Exception as e:
            user_count = 0
            db_data = f'error: {str(e)}'
        
    except Exception as e:
        db_connection = f'error: {str(e)}'
        db_data = 'unavailable'
        user_count = 0
    
    # Check file system
    try:
        upload_dir = os.path.join(os.getcwd(), 'app', 'static', 'uploads')
        fs_writable = os.access(upload_dir, os.W_OK) if os.path.exists(upload_dir) else False
        fs_status = 'ok' if fs_writable else 'readonly'
    except Exception as e:
        fs_status = f'error: {str(e)}'
    
    # Memory usage (basic check)
    try:
        import psutil
        memory_percent = psutil.virtual_memory().percent
        memory_status = 'ok' if memory_percent < 85 else 'high'
    except ImportError:
        memory_percent = 'unknown'
        memory_status = 'unknown'
    
    health_data = {
        'timestamp': datetime.utcnow().isoformat(),
        'environment': os.getenv('FLASK_ENV', 'production'),
        'database': {
            'connection': db_connection,
            'data_access': db_data,
            'user_count': user_count
        },
        'filesystem': {
            'status': fs_status,
            'upload_directory': upload_dir if 'upload_dir' in locals() else 'unknown'
        },
        'memory': {
            'usage_percent': memory_percent,
            'status': memory_status
        },
        'application': {
            'status': 'running',
            'python_version': sys.version.split()[0],
            'flask_env': os.getenv('FLASK_ENV', 'production')
        }
    }
    
    # Determine overall status
    critical_issues = [
        db_connection != 'ok',
        db_data.startswith('error'),
        memory_status == 'high'
    ]
    
    status_code = 503 if any(critical_issues) else 200
    
    return jsonify(health_data), status_code

@health_bp.route('/health/ready')
def readiness_check():
    """Readiness check for load balancers"""
    try:
        # Quick database check
        db.session.execute('SELECT 1')
        return jsonify({'status': 'ready'}), 200
    except Exception as e:
        return jsonify({'status': 'not ready', 'error': str(e)}), 503

@health_bp.route('/health/live')
def liveness_check():
    """Liveness check for container orchestration"""
    return jsonify({
        'status': 'alive',
        'timestamp': datetime.utcnow().isoformat()
    }), 200
