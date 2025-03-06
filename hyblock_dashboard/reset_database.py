#!/usr/bin/env python3
"""
Reset Database Script

This script drops and recreates the database with the updated schema.
"""

import os
import sys
import logging
import psycopg2
from psycopg2 import sql
import time
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("reset_database.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("reset_database")

def check_and_create_database():
    """Create the database if it doesn't exist."""
    try:
        # Get database connection parameters from environment variables
        db_host = os.environ.get("DB_HOST", "localhost")
        db_port = os.environ.get("DB_PORT", "5432")
        db_name = os.environ.get("DB_NAME", "hyblock_data")
        db_user = os.environ.get("DB_USER", "postgres")
        db_password = os.environ.get("DB_PASSWORD", "postgres")
        
        logger.info(f"Checking if database {db_name} exists")
        logger.info(f"Connection parameters: host={db_host}, port={db_port}, user={db_user}")
        
        # Connect to the default postgres database
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            dbname="postgres",
            user=db_user,
            password=db_password,
            connect_timeout=10
        )
        conn.autocommit = True
        
        # Check if the database exists
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
        exists = cur.fetchone()
        
        if not exists:
            logger.info(f"Database {db_name} does not exist, creating it")
            # Create the database
            cur.execute(f"CREATE DATABASE {db_name} WITH ENCODING 'UTF8'")
            logger.info(f"Database {db_name} created successfully")
        else:
            logger.info(f"Database {db_name} already exists")
        
        cur.close()
        conn.close()
        return True
    
    except psycopg2.OperationalError as e:
        logger.error(f"Database connection error: {e}")
        logger.error("Please ensure PostgreSQL is running and accessible with the provided credentials")
        logger.error(f"Attempted to connect to: postgresql://{db_user}:***@{db_host}:{db_port}/postgres")
        return False
    except Exception as e:
        logger.error(f"Error checking/creating database: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def reset_database():
    """Drop and recreate the database with the updated schema."""
    try:
        # Get database connection parameters from environment variables
        db_host = os.environ.get("DB_HOST", "localhost")
        db_port = os.environ.get("DB_PORT", "5432")
        db_name = os.environ.get("DB_NAME", "hyblock_data")
        db_user = os.environ.get("DB_USER", "postgres")
        db_password = os.environ.get("DB_PASSWORD", "postgres")
        
        logger.info("Starting database reset process")
        
        # First check if the database exists, create it if it doesn't
        if not check_and_create_database():
            logger.error("Failed to check/create database, aborting reset")
            return False
        
        # Connect to the database
        logger.info(f"Connecting to database {db_name}")
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            dbname=db_name,
            user=db_user,
            password=db_password,
            connect_timeout=10
        )
        conn.autocommit = True
        
        # Read the schema file
        schema_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")
        logger.info(f"Reading schema from {schema_file}")
        
        with open(schema_file, "r") as f:
            schema_sql = f.read()
        
        # Execute the schema SQL
        logger.info("Executing schema SQL")
        cur = conn.cursor()
        
        # Split the schema SQL into individual statements and execute them
        statements = schema_sql.split(';')
        for statement in statements:
            if statement.strip():
                try:
                    cur.execute(statement)
                    logger.debug(f"Executed: {statement[:50]}...")
                except Exception as e:
                    logger.error(f"Error executing statement: {statement[:100]}...")
                    logger.error(f"Error: {e}")
        
        logger.info("Schema SQL executed successfully")
        
        cur.close()
        conn.close()
        logger.info("Database reset completed successfully")
        return True
    
    except psycopg2.OperationalError as e:
        logger.error(f"Database connection error: {e}")
        logger.error("Please ensure PostgreSQL is running and accessible with the provided credentials")
        logger.error(f"Attempted to connect to: postgresql://{db_user}:***@{db_host}:{db_port}/{db_name}")
        return False
    except Exception as e:
        logger.error(f"Error resetting database: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    # Get database connection parameters from environment variables
    db_host = os.environ.get("DB_HOST", "localhost")
    db_port = os.environ.get("DB_PORT", "5432")
    db_name = os.environ.get("DB_NAME", "hyblock_data")
    db_user = os.environ.get("DB_USER", "postgres")
    db_password = os.environ.get("DB_PASSWORD", "postgres")
    
    logger.info(f"Database connection string: postgresql://{db_user}:***@{db_host}:{db_port}/{db_name}")
    
    # Try to reset the database with retries
    max_retries = 3
    retry_delay = 2  # seconds
    
    for attempt in range(1, max_retries + 1):
        logger.info(f"Reset attempt {attempt}/{max_retries}")
        if reset_database():
            logger.info("Database reset successful")
            sys.exit(0)
        else:
            if attempt < max_retries:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                logger.error("All reset attempts failed")
                sys.exit(1) 