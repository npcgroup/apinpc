import os
import sys
import logging

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.database import connect_to_database, execute_query, get_logger

# Set up logger
logger = get_logger("update_schema")

def update_database_schema():
    """Update the database schema to include market cap category"""
    logger.info("Updating database schema to include market cap category")
    
    try:
        # Connect to database
        conn = connect_to_database()
        if not conn:
            logger.error("Failed to connect to database")
            return False
        
        # Check if the column already exists
        check_query = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'hyblock_data' AND column_name = 'market_cap_category'
        """
        
        result = execute_query(conn, check_query)
        
        if not result:
            # Add the market_cap_category column to the hyblock_data table
            alter_query = """
                ALTER TABLE hyblock_data 
                ADD COLUMN IF NOT EXISTS market_cap_category VARCHAR(20) DEFAULT 'unknown'
            """
            
            success = execute_query(conn, alter_query, fetch=False)
            
            if success:
                logger.info("Successfully added market_cap_category column to hyblock_data table")
            else:
                logger.error("Failed to add market_cap_category column to hyblock_data table")
                return False
            
            # Add the column to specialized tables if they exist
            specialized_tables = [
                'market_data', 'liquidity_data', 'funding_data', 
                'open_interest_data', 'asks_increase_decrease_data'
            ]
            
            for table in specialized_tables:
                # Check if the table exists
                table_check_query = f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = '{table}'
                    )
                """
                
                table_exists = execute_query(conn, table_check_query)
                
                if table_exists and table_exists[0][0]:
                    # Add the column to the table
                    alter_table_query = f"""
                        ALTER TABLE {table} 
                        ADD COLUMN IF NOT EXISTS market_cap_category VARCHAR(20) DEFAULT 'unknown'
                    """
                    
                    success = execute_query(conn, alter_table_query, fetch=False)
                    
                    if success:
                        logger.info(f"Successfully added market_cap_category column to {table} table")
                    else:
                        logger.error(f"Failed to add market_cap_category column to {table} table")
        else:
            logger.info("market_cap_category column already exists in hyblock_data table")
        
        # Create indexes for faster querying
        index_query = """
            CREATE INDEX IF NOT EXISTS idx_hyblock_data_market_cap_category 
            ON hyblock_data (market_cap_category);
        """
        
        success = execute_query(conn, index_query, fetch=False)
        
        if success:
            logger.info("Successfully created index on market_cap_category column")
        else:
            logger.error("Failed to create index on market_cap_category column")
        
        conn.close()
        logger.info("Database schema update completed")
        return True
    
    except Exception as e:
        logger.error(f"Error updating database schema: {e}")
        return False

if __name__ == "__main__":
    update_database_schema() 