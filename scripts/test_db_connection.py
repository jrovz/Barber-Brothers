"""
Database connection tester script for Barber Brothers application.

This script tests the database connection logic in isolation to make sure
it works properly before deploying to Cloud Run.
"""
import os
import sys
import logging
import time
import argparse
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger("db_tester")

def parse_args():
    parser = argparse.ArgumentParser(description='Test database connection for Barber Brothers application')
    parser.add_argument('--socket-dir', default='/cloudsql', help='Socket directory for Cloud SQL')
    parser.add_argument('--user', default='postgres', help='Database user')
    parser.add_argument('--password', default='y3WhoYFS', help='Database password')
    parser.add_argument('--name', default='barberia-db', help='Database name')
    parser.add_argument('--instance', default='barber-brothers-460514:us-central1:barberia-db', 
                        help='Cloud SQL instance connection name')
    return parser.parse_args()

def test_connection(db_user, db_pass, db_name, instance_connection_name, socket_dir):
    """Test direct connection to PostgreSQL using pg8000"""
    try:
        import pg8000
        logger.info("Testing connection with pg8000 (recommended for Cloud SQL)")
        
        # Using pg8000 adapter which is recommended for Cloud SQL
        db_uri = f"postgresql+pg8000://{db_user}:{db_pass}@/{db_name}?unix_socket={socket_dir}/{instance_connection_name}"
        logger.info(f"Database URI: {db_uri.replace(db_pass, '***')}")
        
        # Create engine
        engine = create_engine(db_uri)
        
        # Try connection
        try:
            logger.info("Attempting connection...")
            with engine.connect() as conn:
                # Execute a simple query
                result = conn.execute(text("SELECT 1"))
                logger.info(f"Connection successful: {result.scalar()}")
                return True
        except OperationalError as e:
            logger.error(f"pg8000 connection failed: {e}")
            return False
    except ImportError:
        logger.warning("pg8000 not installed, skipping this test")
        return False

def test_cloud_sql_connector(db_user, db_pass, db_name, instance_connection_name):
    """Test connection using Cloud SQL Python Connector"""
    try:
        from google.cloud.sql.connector import Connector
        
        logger.info("Testing connection with Cloud SQL Python Connector")
        
        # Initialize the connector
        connector = Connector()
        
        # Function to create connection
        def getconn():
            return connector.connect(
                instance_connection_name,
                "pg8000",
                user=db_user,
                password=db_pass,
                db=db_name
            )
        
        # Create engine with the connector
        engine = create_engine(
            "postgresql+pg8000://",
            creator=getconn
        )
        
        # Try connection
        try:
            logger.info("Attempting connection with connector...")
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                logger.info(f"Connector connection successful: {result.scalar()}")
                return True
        except Exception as e:
            logger.error(f"Cloud SQL Connector connection failed: {e}")
            return False
    except ImportError:
        logger.warning("Cloud SQL Connector not installed, skipping this test")
        return False

def test_direct_connection(db_user, db_pass, db_name, db_host='localhost', db_port='5432'):
    """Test direct connection to PostgreSQL"""
    logger.info("Testing direct PostgreSQL connection")
    
    # Construct database URI for direct connection
    db_uri = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    logger.info(f"Database URI: {db_uri.replace(db_pass, '***')}")
    
    # Create engine
    engine = create_engine(db_uri)
    
    # Try connection
    try:
        logger.info("Attempting direct connection...")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info(f"Direct connection successful: {result.scalar()}")
            return True
    except OperationalError as e:
        logger.error(f"Direct connection failed: {e}")
        return False

def main():
    args = parse_args()
    
    # Set environment variables for testing
    os.environ["DB_USER"] = args.user
    os.environ["DB_PASS"] = args.password
    os.environ["DB_NAME"] = args.name
    os.environ["INSTANCE_CONNECTION_NAME"] = args.instance
    
    logger.info("=== Starting Database Connection Tests ===")
    logger.info(f"Using: user={args.user}, db={args.name}, instance={args.instance}")
    
    # Test Cloud SQL connector
    cloud_sql_result = test_cloud_sql_connector(args.user, args.password, args.name, args.instance)
    
    # Test pg8000 socket connection
    socket_result = test_connection(args.user, args.password, args.name, args.instance, args.socket_dir)
    
    # Test direct connection (will only work locally)
    direct_result = test_direct_connection(args.user, args.password, args.name)
    
    # Print summary
    logger.info("\n=== Test Results ===")
    logger.info(f"Cloud SQL Connector: {'✅ Success' if cloud_sql_result else '❌ Failed'}")
    logger.info(f"pg8000 Socket: {'✅ Success' if socket_result else '❌ Failed'}")
    logger.info(f"Direct Connection: {'✅ Success' if direct_result else '❌ Failed'}")
    
    # Determine overall status
    if cloud_sql_result or socket_result:
        logger.info("\n✅ Cloud SQL connection methods working!")
        return 0
    elif direct_result:
        logger.info("\n⚠️ Only direct connection working - this won't work in Cloud Run!")
        return 1
    else:
        logger.info("\n❌ All connection methods failed!")
        return 2

if __name__ == "__main__":
    sys.exit(main())
