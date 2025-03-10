#!/usr/bin/env python3
"""
Fix Database Schema

This script fixes the database schema by creating the crypto_price_history table
and ensuring all required tables exist.
"""

import os
import sys
import logging
import pandas as pd
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from supabase import create_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('fix_database_schema.log')
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Supabase client
try:
    supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    supabase_key = os.getenv("NEXT_PUBLIC_SUPABASE_KEY")
    supabase = create_client(supabase_url, supabase_key)
    logger.info("Supabase client initialized successfully")
except Exception as e:
    logger.error(f"Error initializing Supabase client: {e}")
    supabase = None
    sys.exit(1)

def check_table_exists(table_name):
    """Check if a table exists in the database"""
    try:
        # Try to query the table
        response = supabase.table(table_name).select('*').limit(1).execute()
        logger.info(f"Table {table_name} exists")
        return True
    except Exception as e:
        logger.warning(f"Table {table_name} does not exist: {e}")
        return False

def create_crypto_price_history_table():
    """Create the crypto_price_history table"""
    try:
        # SQL to create the table
        sql = """
        CREATE TABLE IF NOT EXISTS crypto_price_history (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(20) NOT NULL,
            exchange VARCHAR(20) NOT NULL,
            datetime TIMESTAMP WITH TIME ZONE NOT NULL,
            price NUMERIC(20, 8) NOT NULL,
            volume NUMERIC(30, 8),
            high NUMERIC(20, 8),
            low NUMERIC(20, 8),
            open NUMERIC(20, 8),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
        );

        -- Add unique constraint to prevent duplicate entries
        ALTER TABLE crypto_price_history 
        DROP CONSTRAINT IF EXISTS unique_price_entry;
        
        ALTER TABLE crypto_price_history 
        ADD CONSTRAINT unique_price_entry UNIQUE (symbol, exchange, datetime);

        -- Create indexes for faster queries
        CREATE INDEX IF NOT EXISTS idx_price_history_symbol ON crypto_price_history (symbol);
        CREATE INDEX IF NOT EXISTS idx_price_history_exchange ON crypto_price_history (exchange);
        CREATE INDEX IF NOT EXISTS idx_price_history_datetime ON crypto_price_history (datetime);
        CREATE INDEX IF NOT EXISTS idx_price_history_symbol_exchange ON crypto_price_history (symbol, exchange);

        -- Add row level security
        ALTER TABLE crypto_price_history ENABLE ROW LEVEL SECURITY;

        -- Create policies
        DROP POLICY IF EXISTS "Allow public read access" ON crypto_price_history;
        CREATE POLICY "Allow public read access" 
        ON crypto_price_history FOR SELECT 
        USING (true);

        DROP POLICY IF EXISTS "Allow authenticated insert" ON crypto_price_history;
        CREATE POLICY "Allow authenticated insert" 
        ON crypto_price_history FOR INSERT 
        TO authenticated 
        WITH CHECK (true);

        -- Add table comment
        COMMENT ON TABLE crypto_price_history IS 'Historical price data for cryptocurrencies';
        """
        
        # Execute the SQL
        response = supabase.rpc('exec_sql', {'sql': sql}).execute()
        logger.info("Created crypto_price_history table")
        return True
    except Exception as e:
        logger.error(f"Error creating crypto_price_history table: {e}")
        return False

def create_crypto_price_view():
    """Create a view for the crypto_price_history table"""
    try:
        # SQL to create the view
        sql = """
        CREATE OR REPLACE VIEW crypto_price_view AS
        SELECT 
            symbol,
            exchange,
            datetime,
            price,
            volume,
            high,
            low,
            open
        FROM crypto_price_history
        ORDER BY datetime DESC;
        """
        
        # Execute the SQL
        response = supabase.rpc('exec_sql', {'sql': sql}).execute()
        logger.info("Created crypto_price_view")
        return True
    except Exception as e:
        logger.error(f"Error creating crypto_price_view: {e}")
        return False

def main():
    """Main function"""
    logger.info("Starting database schema fix")
    
    # Check if the crypto_price_history table exists
    if not check_table_exists('crypto_price_history'):
        # Create the table
        if create_crypto_price_history_table():
            logger.info("Successfully created crypto_price_history table")
            
            # Create the view
            if create_crypto_price_view():
                logger.info("Successfully created crypto_price_view")
            else:
                logger.error("Failed to create crypto_price_view")
        else:
            logger.error("Failed to create crypto_price_history table")
    else:
        logger.info("crypto_price_history table already exists")
    
    logger.info("Database schema fix completed")

if __name__ == "__main__":
    main() 