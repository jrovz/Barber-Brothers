from flask import Blueprint

bp = Blueprint('api', __name__)

from app.api import routes
from app.api.health import register_health_routes

# Registrar rutas de health check
register_health_routes(bp)