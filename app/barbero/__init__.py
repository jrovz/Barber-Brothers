from flask import Blueprint

bp = Blueprint('barbero', __name__, url_prefix='/barbero')

from app.barbero import routes 