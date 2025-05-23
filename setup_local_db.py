"""
Apply migrations to local SQLite database

This script will create a local SQLite database and apply all migrations.
"""
import os
import sys
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, upgrade

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_local_db():
    """Set up a local SQLite database for development"""
    try:
        print("Starting local database setup...")
        
        # Create a minimal Flask app
        app = Flask(__name__)
        
        # Set up SQLite configuration
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'app.db')
        db_dir = os.path.dirname(db_path)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
            print(f"Created directory: {db_dir}")
            
        print(f"Using SQLite database at: {db_path}")
        
        # Configure the app to use SQLite
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        # Initialize SQLAlchemy
        db = SQLAlchemy(app)
        
        # Initialize Flask-Migrate
        migrations_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'migrations')
        print(f"Using migrations directory: {migrations_dir}")
        migrate = Migrate(app, db, directory=migrations_dir)
        
        # Run migrations
        with app.app_context():
            print("Running database migrations...")
            upgrade(directory=migrations_dir)
            print("Migrations completed successfully")
        
        # Import initial data
        try:
            print("Attempting to import initial data...")
            # Import the create_app function to get the real app with all models
            from app import create_app
            real_app = create_app('development')
            
            with real_app.app_context():
                # Now import and run the initial data import
                from init_data import import_initial_data
                print("Importing initial data...")
                success = import_initial_data()
                if success:
                    print("Initial data imported successfully")
                else:
                    print("Initial data import returned False")
        except Exception as e:
            print(f"Error importing initial data: {e}")
            import traceback
            traceback.print_exc()
            
        print("Local database setup complete")
        return True
        
    except Exception as e:
        print(f"Error setting up local database: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = setup_local_db()
    sys.exit(0 if success else 1)
