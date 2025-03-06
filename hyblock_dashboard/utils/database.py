import os
import logging
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get log level from environment variable
log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
log_level = getattr(logging, log_level_str, logging.INFO)

# Configure logging
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("hyblock_data.log"),
        logging.StreamHandler()
    ]
)

def get_logger(name):
    """Get a logger with the given name"""
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    return logger

def connect_to_database():
    """Connect to the TimescaleDB database"""
    logger = get_logger("database")
    
    try:
        # Get database connection parameters from environment variables
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME", "hyblock_data")
        db_user = os.getenv("DB_USER", "postgres")
        db_password = os.getenv("DB_PASSWORD", "postgres")
        
        logger.info(f"Connecting to database at {db_host}:{db_port}/{db_name} as {db_user}")
        
        # Connect to the database
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            dbname=db_name,
            user=db_user,
            password=db_password,
            sslmode='prefer'
        )
        
        logger.info("Successfully connected to TimescaleDB")
        return conn
    
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        return None

def execute_query(conn, query, params=None, fetch=True):
    """Execute a SQL query and return the results"""
    logger = get_logger("database")
    
    try:
        logger.debug(f"Executing query: {query}")
        if params:
            logger.debug(f"Query parameters: {params}")
            
        # Process parameters to handle array parameters correctly
        if params and isinstance(params, list):
            processed_params = []
            for param in params:
                if isinstance(param, list):
                    # Convert list parameters to a string for the IN clause
                    # This prevents the "operator does not exist: character varying = text[]" error
                    if len(param) == 1:
                        processed_params.append(param[0])
                    else:
                        # For multiple values, we'll need to modify the query to use IN instead of =
                        # This should be handled in the calling code
                        processed_params.append(tuple(param))
                else:
                    processed_params.append(param)
            params = processed_params
        
        with conn.cursor() as cur:
            cur.execute(query, params)
            
            if fetch:
                # Check if the query is a SELECT query by looking for SELECT at the beginning
                # or if it's a query that returns results like SHOW, EXPLAIN, etc.
                if query.strip().upper().startswith(("SELECT", "SHOW", "EXPLAIN", "WITH")):
                    try:
                        results = cur.fetchall()
                        logger.debug(f"Query returned {len(results)} rows")
                        return results
                    except psycopg2.ProgrammingError as e:
                        if "no results to fetch" in str(e):
                            # This is not an error for non-SELECT queries
                            logger.debug("Query did not return any results (normal for non-SELECT queries)")
                            conn.commit()
                            return True
                        else:
                            # This is an actual error
                            raise
                else:
                    # For non-SELECT queries, just commit and return True
                    conn.commit()
                    logger.debug("Query executed successfully and changes committed")
                    return True
            else:
                conn.commit()
                logger.debug("Query executed successfully and changes committed")
                return True
    
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        conn.rollback()
        return None 