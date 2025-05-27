#!/usr/bin/env python
"""
Database setup script for Barber-Brothers application on Azure

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
    db_host = os.environ.get("DB_HOST")
    db_port = os.environ.get("DB_PORT", "5432")
    
    if not all([db_user, db_pass, db_name, db_host]):
        logger.error("Missing required database environment variables")
        return False
    
    logger.info(f"Connection info: user=\"{db_user}\", db={db_name}, host={db_host}")
    
    # Construct database URI for PostgreSQL
    db_uri = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    logger.info(f"Database URI reference set: {db_uri.replace(db_pass, '***')}")
    
    # Set DATABASE_URL for Flask-SQLAlchemy
    os.environ["DATABASE_URL"] = db_uri
    logger.info(f"Config: Using DATABASE_URL for PostgreSQL: {os.environ['DATABASE_URL'].replace(db_pass, '***')}")
    
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
                logger.info("Migrations run successfully using Flask-Migrate")
                return True
        except Exception as e1:
            logger.warning(f"Error running migrations with Flask-Migrate: {e1}")
            
            # Second approach: Use flask db upgrade via subprocess
            import subprocess
            result = subprocess.run(["flask", "db", "upgrade"], 
                                  capture_output=True, 
                                  text=True)
            
            if result.returncode == 0:
                logger.info("Migrations run successfully using Flask CLI")
                return True
            else:
                logger.error(f"Error running migrations with Flask CLI: {result.stderr}")
                return False
    except Exception as e:
        logger.error(f"Failed to run migrations: {e}")
        return False

def seed_database():
    """Seed the database with initial data if needed"""
    logger.info("Checking if database needs seeding...")
    try:
        # Import the application
        from wsgi import app
        from app.models import User, Categoria, Producto, Servicio
        
        with app.app_context():
            # Check if we need to seed the database
            if User.query.count() == 0:
                logger.info("No users found. Seeding initial admin user...")
                # Create admin user
                from app.utils.db_init_handler import create_default_admin
                create_default_admin()
                
            if Categoria.query.count() == 0:
                logger.info("No categories found. Seeding initial categories...")
                # Create default categories
                from app.utils.db_init_handler import create_default_categories
                create_default_categories()
                
            if Servicio.query.count() == 0:
                logger.info("No services found. Seeding initial services...")
                # Create default services
                from app.utils.db_init_handler import create_default_services
                create_default_services()
                
            logger.info("Database seeding completed.")
            return True
    except Exception as e:
        logger.error(f"Error seeding database: {e}")
        return False

def main():
    """Main function to initialize database"""
    logger.info("Starting database initialization...")
    
    # Wait for database to be available
    if not wait_for_database():
        logger.error("Failed to connect to database. Exiting.")
        sys.exit(1)
    
    # Run migrations
    if not run_migrations():
        logger.error("Failed to run migrations. Continuing anyway...")
    
    # Seed database
    if not seed_database():
        logger.error("Failed to seed database. Continuing anyway...")
    
    logger.info("Database initialization completed.")

if __name__ == "__main__":
    main()
