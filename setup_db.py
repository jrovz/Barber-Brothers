#!/usr/bin/env python
"""
Database setup script for Barber-Brothers application

This script is called during container startup to initialize the database,
create tables if they don't exist, and run any pending migrations.
"""
import os
import sys
import logging
import time
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger("setup_db")

def wait_for_database():
    """Wait for the database to be available"""
    # Get database connection details from environment variables
    db_user = os.environ.get("DB_USER")
    db_pass = os.environ.get("DB_PASS")
    db_name = os.environ.get("DB_NAME")
    db_engine = os.environ.get("DB_ENGINE", "postgresql")
    instance_connection_name = os.environ.get("INSTANCE_CONNECTION_NAME")
    
    logger.info(f"INSTANCE_CONNECTION_NAME: {instance_connection_name}")
    
    if not all([db_user, db_pass, db_name]):
        logger.error("Missing required database environment variables")
        return False
    
    # Check if we need to construct the INSTANCE_CONNECTION_NAME
    if not instance_connection_name:
        logger.info("INSTANCE_CONNECTION_NAME not set, constructing it...")
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
        region = os.environ.get("REGION", "us-central1")
        instance_name = os.environ.get("INSTANCE_NAME", "barberia-db")
        
        if project_id and region and instance_name:
            instance_connection_name = f"{project_id}:{region}:{instance_name}"
            logger.info(f"INSTANCE_CONNECTION_NAME constructed: {instance_connection_name}")
            os.environ["INSTANCE_CONNECTION_NAME"] = instance_connection_name
    
    logger.info(f"Connection info: user=\"{db_user}\", db={db_name}, instance={instance_connection_name}")
    
    # Construct database URI for PostgreSQL with pg8000 (Cloud SQL connector)
    if instance_connection_name and ":" in instance_connection_name:
        # We're in Cloud Run with Cloud SQL
        db_socket_dir = os.environ.get("DB_SOCKET_DIR", "/cloudsql")
        
        # Using pg8000 adapter which is recommended for Cloud SQL
        db_uri = f"postgresql+pg8000://{db_user}:{db_pass}@/{db_name}?unix_socket={db_socket_dir}/{instance_connection_name}"
        logger.info(f"Database URI reference set: {db_uri.replace(db_pass, '***')}")
        
        # Set DATABASE_URL for Flask-SQLAlchemy
        os.environ["DATABASE_URL"] = db_uri
        logger.info(f"Config: Using DATABASE_URL for PostgreSQL: {os.environ['DATABASE_URL'].replace(db_pass, '***')}")
    else:
        # Local development with direct connection
        db_host = os.environ.get("DB_HOST", "localhost")
        db_port = os.environ.get("DB_PORT", "5432")
        db_uri = f"{db_engine}://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
        logger.info(f"Connecting to database at: {db_host}:{db_port}")
    
      # Try to connect to the database
    engine = create_engine(db_uri)
    max_retries = 5
    retry_interval = 3  # seconds
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Database connection attempt {attempt + 1}/{max_retries}")
            connection = engine.connect()
            connection.close()
            logger.info("Successfully connected to the database")
            return True
        except OperationalError as e:
            logger.warning(f"Database connection failed: {e}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_interval} seconds...")
                time.sleep(retry_interval)
            else:
                logger.error("Maximum connection attempts reached. Could not connect to the database.")
                return False
    return False

def run_migrations():
    """Run database migrations using Flask-Migrate"""
    logger.info("Attempting to run database migrations...")
    try:
        # First approach: Try direct Flask-Migrate import
        try:
            from flask_migrate import upgrade as flask_migrate_upgrade
            from wsgi import app
            
            with app.app_context():
                flask_migrate_upgrade()
                logger.info("Database migrations completed successfully using flask_migrate.upgrade()")
                return True
        except Exception as e:
            logger.warning(f"Could not run migrations using direct flask_migrate import: {e}")
            
        # Second approach: Try Flask CLI
        try:
            from flask.cli import FlaskGroup
            from wsgi import app
            
            # Create Flask CLI context
            cli = FlaskGroup(create_app=lambda: app)
            
            # Run migrations
            with app.app_context():
                from flask_migrate import upgrade
                upgrade()
                
            logger.info("Database migrations completed successfully using Flask CLI")
            return True
        except Exception as e:
            logger.warning(f"Could not run migrations using Flask CLI: {e}")
        
        # If we reached here, both approaches failed
        logger.warning("Could not run migrations automatically. App will try at startup.")
        return False
    except Exception as e:
        logger.error(f"Error running migrations: {e}")
        return False

def init_database():
    """Initialize the database with required tables and data"""
    if not wait_for_database():
        logger.error("Could not connect to the database. Initialization failed.")
        # Don't exit, let the app try to run anyway
        return False
    
    try:
        # Try to run database migrations if possible
        logger.info("Database connection established. Attempting to run migrations...")
        try:
            result = run_migrations()
            if result:
                logger.info("Database migrations completed successfully")
            else:
                logger.warning("Database migrations may not have completed successfully")
                # Still return True to allow app to continue
                return True
        except Exception as e:
            logger.warning(f"Could not run migrations directly: {e}")
            logger.info("The application will attempt to run migrations at startup.")
        
        return True
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting database setup...")
    
    # Check if the database is configured with Cloud SQL
    instance_connection_name = os.environ.get("INSTANCE_CONNECTION_NAME")
    if not instance_connection_name:
        logger.warning("INSTANCE_CONNECTION_NAME not set, constructing it...")
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
        region = os.environ.get("REGION", "us-east1")
        instance_name = os.environ.get("INSTANCE_NAME", "barberia-db")
        
        if project_id:
            instance_connection_name = f"{project_id}:{region}:{instance_name}"
            logger.info(f"INSTANCE_CONNECTION_NAME constructed: {instance_connection_name}")
            os.environ["INSTANCE_CONNECTION_NAME"] = instance_connection_name
        else:
            logger.warning("GOOGLE_CLOUD_PROJECT not set, can't construct INSTANCE_CONNECTION_NAME")
    
    # Log database connection info (without password)
    db_user = os.environ.get("DB_USER", "")
    db_name = os.environ.get("DB_NAME", "")
    logger.info(f"Connection info: user=\"{db_user}\", db={db_name}, instance={instance_connection_name}")
    
    # Initialize database
    success = init_database()
    
    if not success:
        logger.warning("Database initialization completed with warnings.")
        # Exit with success anyway to let the app try to start
        sys.exit(0)
    else:
        logger.info("Database initialization completed successfully.")
        sys.exit(0)
