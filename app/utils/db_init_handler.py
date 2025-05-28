import os
import logging
from flask import current_app
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

def init_database_if_needed():
    """
    Verifica si la base de datos necesita ser inicializada
    y realiza las operaciones necesarias.
    """
    try:
        # Verificar si la base de datos está disponible
        from app import db
        try:
            # Intentar ejecutar una consulta simple para verificar conexión
            db.session.execute(text("SELECT 1"))
            current_app.logger.info("Conexión a la base de datos exitosa.")
        except SQLAlchemyError as e:
            current_app.logger.error(f"Error al conectar a la base de datos: {str(e)}")
            return
            
        # Aquí puedes agregar lógica adicional para inicialización si es necesario
        # Por ejemplo, verificar si las tablas existen y crearlas si no
        
    except Exception as e:
        current_app.logger.error(f"Error en la inicialización de la base de datos: {str(e)}")
