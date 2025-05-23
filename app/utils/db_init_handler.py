"""
Database initialization handler

This module provides database initialization functions that will be called 
at the application startup to ensure the database is properly set up.
"""
import os
import logging
from flask import current_app
from sqlalchemy.exc import SQLAlchemyError, ProgrammingError
from .. import db

logger = logging.getLogger(__name__)

def init_database_if_needed():
    """
    Check if the database needs to be initialized and run migrations if needed.
    This is called during app startup.
    """
    try:
        # Try to check if the database has been initialized
        logger.info("Checking database initialization status...")
        
        try:
            # Try to query a table that should exist if the database is initialized
            # This will fail with ProgrammingError if the table doesn't exist
            with current_app.app_context():
                # Usar text() para crear consultas SQL textuales
                from sqlalchemy.sql import text
                db.session.execute(text('SELECT 1 FROM producto LIMIT 1'))
                logger.info("Database appears to be already initialized.")
                return True
        except ProgrammingError as e:
            # Table doesn't exist, need to run migrations
            logger.info(f"Database tables don't exist ({str(e)}). Running migrations...")
            from flask_migrate import upgrade
            
            # Run migrations
            with current_app.app_context():
                upgrade()
                logger.info("Database migrations applied successfully.")
            
            # Import initial data
            try:
                from init_data import import_initial_data
                with current_app.app_context():
                    import_initial_data()
                    logger.info("Initial data imported successfully.")
            except Exception as e:
                logger.error(f"Failed to import initial data: {e}")
                # Continue even if initial data import fails
            
            return True
            
    except SQLAlchemyError as e:
        logger.error(f"Database initialization error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during database initialization: {e}")
        return False
