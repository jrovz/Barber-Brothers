"""
Verify the database structure

This script will check if the database has the required tables.
"""
import os
import sys
import sqlite3

def verify_db():
    """Check if the database has the required tables"""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'app.db')
    
    print(f"Checking SQLite database at: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"ERROR: Database file not found at {db_path}")
        return False
        
    print(f"Database file exists: {os.path.getsize(db_path)} bytes")
    
    try:
        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"Found {len(tables)} tables in database:")
        for table in tables:
            print(f"  - {table[0]}")
            
        # Check specifically for 'categorias' table
        if ('categorias',) in tables:
            print("\nTable 'categorias' exists. Checking structure:")
            cursor.execute("PRAGMA table_info(categorias);")
            columns = cursor.fetchall()
            
            print("\nColumns in 'categorias' table:")
            for col in columns:
                print(f"  - {col[1]}: {col[2]}")
        else:
            print("\nERROR: Table 'categorias' does not exist!")
            
        # Check for data in the categorias table
        if ('categorias',) in tables:
            cursor.execute("SELECT COUNT(*) FROM categorias;")
            count = cursor.fetchone()[0]
            print(f"\nFound {count} records in 'categorias' table")
            
            if count > 0:
                cursor.execute("SELECT * FROM categorias LIMIT 5;")
                rows = cursor.fetchall()
                print("\nSample data from 'categorias' table:")
                for row in rows:
                    print(f"  - {row}")
        
        conn.close()
        return True
    except Exception as e:
        print(f"Error verifying database: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = verify_db()
    sys.exit(0 if success else 1)
