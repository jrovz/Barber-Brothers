"""
Database Setup Script

This script initializes the database for the barberia application.
It creates all tables and imports initial data.
"""

import os
import sys
import time
from flask_migrate import Migrate, upgrade
from app import create_app, db

def setup_database():
    """
    Set up the database for the application
    """
    try:
        print("Starting database setup...")
        app = create_app('production')
        
        with app.app_context():
            # Wait a bit for database connection to be ready
            time.sleep(2)
            
            print("Running migrations...")
            # Run migrations
            migrate = Migrate(app, db)
            upgrade()
            
            print("Migrations completed successfully.")
            
            # Import initial data if specified
            try:
                print("Importing initial data...")
                from init_data import import_initial_data
                success = import_initial_data()
                if success:
                    print("Initial data imported successfully.")
                else:
                    print("Failed to import initial data.")
            except Exception as e:
                print(f"Error importing initial data: {e}")
                
            print("Database setup completed.")
            return True
    except Exception as e:
        print(f"Error setting up database: {e}")
        return False

if __name__ == "__main__":
    setup_database()
