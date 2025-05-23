"""
Add example categories to the database
"""
import os
import sys
import sqlite3
from datetime import datetime

def add_categories():
    """Add default categories to the database"""
    categories = [
        'peinar',
        'barba',
        'accesorios'
    ]
    
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'app.db')
    print(f"Adding categories to database at: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"ERROR: Database file not found at {db_path}")
        return False
    
    try:
        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if categories already exist
        cursor.execute("SELECT COUNT(*) FROM categorias;")
        count = cursor.fetchone()[0]
        
        if count > 0:
            print(f"Database already has {count} categories. Skipping.")
            conn.close()
            return True
        
        # Add categories
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        for category in categories:
            cursor.execute(
                "INSERT INTO categorias (nombre, creado, actualizado) VALUES (?, ?, ?)",
                (category, now, now)
            )
        
        conn.commit()
        
        # Verify categories were added
        cursor.execute("SELECT * FROM categorias;")
        added_categories = cursor.fetchall()
        
        print(f"Added {len(added_categories)} categories:")
        for category in added_categories:
            print(f"  - ID: {category[0]}, Name: {category[1]}")
        
        conn.close()
        return True
    except Exception as e:
        print(f"Error adding categories: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = add_categories()
    sys.exit(0 if success else 1)
