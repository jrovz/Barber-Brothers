"""
Quick script to reset the database

This script will:
1. Set up a local SQLite database
2. Run all migrations
3. Import initial data

Usage:
    python reset_db.py
"""
import os
import sys
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, upgrade

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set up environment for SQLite
os.environ['DATABASE_URL'] = 'sqlite:///instance/app.db'
logger.info(f"Setting DATABASE_URL to: {os.environ['DATABASE_URL']}")

# Create a minimal app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
logger.info(f"Using database: {app.config['SQLALCHEMY_DATABASE_URI']}")

db = SQLAlchemy(app)
migrate = Migrate(app, db, directory='migrations')

def main():
    logger.info("Starting database reset...")
    try:
        with app.app_context():
            # Create SQLite database directory if it doesn't exist
            os.makedirs('instance', exist_ok=True)
            logger.info("Created instance directory if it didn't exist")
            
            # Run migrations
            logger.info("Running migrations...")
            from alembic.config import Config
            from alembic import command
            
            # Create Alembic config
            alembic_cfg = Config("migrations/alembic.ini")
            alembic_cfg.set_main_option("script_location", "migrations")
            alembic_cfg.set_main_option("sqlalchemy.url", app.config['SQLALCHEMY_DATABASE_URI'])
            
            # Run the migrations
            command.upgrade(alembic_cfg, "head")
            
            logger.info("Migrations applied successfully!")
            logger.info("Database reset complete!")
            return True
    except Exception as e:
        logger.error(f"Error resetting database: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    if success:
        sys.exit(0)
    else:
        sys.exit(1)
