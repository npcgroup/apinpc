import sys
import os
import json
from datetime import datetime

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.database import connect_to_database, execute_query, get_logger

# Set up logger
logger = get_logger("test_db_connection")

def test_connection():
    """Test the connection to the TimescaleDB database"""
    logger.info("Testing database connection...")
    
    # Connect to database
    conn = connect_to_database()
    if not conn:
        logger.error("Failed to connect to database")
        return False
    
    logger.info("Connected to database successfully")
    
    # Test query execution
    try:
        # Check if the hyblock_data table exists
        query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public'
                AND table_name = 'hyblock_data'
            );
        """
        
        result = execute_query(conn, query)
        
        if result and result[0][0]:
            logger.info("hyblock_data table exists")
            
            # Check if there's any data in the table
            count_query = "SELECT COUNT(*) FROM hyblock_data;"
            count_result = execute_query(conn, count_query)
            
            if count_result:
                count = count_result[0][0]
                logger.info(f"hyblock_data table contains {count} records")
                
                if count > 0:
                    # Get the most recent record
                    recent_query = """
                        SELECT timestamp, endpoint, coin, exchange, timeframe
                        FROM hyblock_data
                        ORDER BY timestamp DESC
                        LIMIT 1;
                    """
                    
                    recent_result = execute_query(conn, recent_query)
                    
                    if recent_result:
                        timestamp, endpoint, coin, exchange, timeframe = recent_result[0]
                        logger.info(f"Most recent record: {timestamp} - {endpoint} - {coin} - {exchange} - {timeframe}")
        else:
            logger.warning("hyblock_data table does not exist. Database may not be initialized.")
            logger.info("Run 'python database/init_database.py' to initialize the database.")
        
        # Close connection
        conn.close()
        logger.info("Database connection test completed successfully")
        return True
    
    except Exception as e:
        logger.error(f"Error testing database: {e}")
        if conn:
            conn.close()
        return False

if __name__ == "__main__":
    if test_connection():
        print("Database connection test passed!")
        sys.exit(0)
    else:
        print("Database connection test failed!")
        sys.exit(1) 