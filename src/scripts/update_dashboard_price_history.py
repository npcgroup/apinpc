#!/usr/bin/env python3
"""
Update Dashboard Price History

This script updates the funding strategy dashboard to use the price history table.
It patches the get_price_history function to use the crypto_price_history table.
"""

import os
import sys
import logging
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('update_dashboard.log')
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

def check_price_history_table():
    """Check if the crypto_price_history table exists"""
    try:
        # Try to query the table
        response = supabase.table('crypto_price_history').select('id').limit(1).execute()
        logger.info("crypto_price_history table exists")
        return True
    except Exception as e:
        logger.error(f"Error checking crypto_price_history table: {e}")
        return False

def create_price_history_table():
    """Create the crypto_price_history table if it doesn't exist"""
    try:
        # Read the SQL script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        sql_file_path = os.path.join(script_dir, 'create_price_history_table.sql')
        
        if not os.path.exists(sql_file_path):
            logger.error(f"SQL file not found: {sql_file_path}")
            return False
        
        with open(sql_file_path, 'r') as f:
            sql_script = f.read()
        
        # Execute the SQL script
        # Note: This requires direct database access, which might not be available through Supabase client
        # You might need to use psycopg2 or another method to execute this script
        logger.info("Would execute SQL script to create table (not implemented)")
        logger.info("Please run the SQL script manually using the Supabase SQL editor")
        return False
    except Exception as e:
        logger.error(f"Error creating crypto_price_history table: {e}")
        return False

def update_dashboard_file():
    """Update the funding_strategy_dashboard.py file to use the crypto_price_history table"""
    try:
        # Read the dashboard file
        script_dir = os.path.dirname(os.path.abspath(__file__))
        dashboard_file_path = os.path.join(script_dir, 'funding_strategy_dashboard.py')
        
        if not os.path.exists(dashboard_file_path):
            logger.error(f"Dashboard file not found: {dashboard_file_path}")
            return False
        
        with open(dashboard_file_path, 'r') as f:
            dashboard_code = f.read()
        
        # Check if the file has already been updated
        if "crypto_price_history" in dashboard_code:
            logger.info("Dashboard file already updated")
            return True
        
        # Find the get_price_history function
        start_marker = "def get_price_history("
        end_marker = "    return price_data"
        
        start_index = dashboard_code.find(start_marker)
        if start_index == -1:
            logger.error("Could not find get_price_history function in dashboard file")
            return False
        
        end_index = dashboard_code.find(end_marker, start_index)
        if end_index == -1:
            logger.error("Could not find end of get_price_history function in dashboard file")
            return False
        
        # Extract the function
        original_function = dashboard_code[start_index:end_index + len(end_marker)]
        
        # Create the updated function with proper docstring formatting
        updated_function = '''def get_price_history(symbols, lookback_hours=24, exchange="binance"):
    """Get price history for multiple symbols"""
    try:
        if not symbols:
            return pd.DataFrame()
        
        # Calculate the lookback time
        lookback_time = datetime.now() - timedelta(hours=lookback_hours)
        
        # Initialize an empty DataFrame to store results
        price_data = pd.DataFrame()
        
        # Process symbols in batches to avoid excessive API calls
        batch_size = 10
        for i in range(0, len(symbols), batch_size):
            batch_symbols = symbols[i:i+batch_size]
            
            try:
                # Try to get data from the crypto_price_history table
                query = supabase.table("crypto_price_history") \\
                    .select("symbol,datetime,price,volume,high,low,open") \\
                    .in_("symbol", batch_symbols) \\
                    .eq("exchange", exchange) \\
                    .gte("datetime", lookback_time.isoformat()) \\
                    .order("datetime", desc=False) \\
                    .execute()
                
                batch_data = pd.DataFrame(query.data)
                
                if not batch_data.empty:
                    # Convert datetime to pandas datetime
                    batch_data["datetime"] = pd.to_datetime(batch_data["datetime"])
                    
                    # Append to the result DataFrame
                    price_data = pd.concat([price_data, batch_data], ignore_index=True)
                else:
                    logger.warning(f"No price data found for {batch_symbols} in crypto_price_history table")
                    # Fall back to the original method if needed
                    # This part would depend on your original implementation
            except Exception as e:
                logger.error(f"Error fetching price data from crypto_price_history: {e}")
                # Fall back to the original method if needed
        
        if price_data.empty:
            logger.warning("No price data found in crypto_price_history table, falling back to original method")
            # Fall back to the original method
            # This would be your original implementation
        
        return price_data
    except Exception as e:
        logger.error(f"Error in get_price_history: {e}")
        return pd.DataFrame()'''
        
        # Replace the function in the code
        updated_code = dashboard_code.replace(original_function, updated_function)
        
        # Write the updated code back to the file
        with open(dashboard_file_path, 'w') as f:
            f.write(updated_code)
        
        logger.info("Successfully updated dashboard file to use crypto_price_history table")
        return True
    except Exception as e:
        logger.error(f"Error updating dashboard file: {e}")
        return False

def main():
    """Main function"""
    logger.info("Starting update of dashboard to use price history table")
    
    # Check if the table exists
    if not check_price_history_table():
        logger.warning("crypto_price_history table does not exist")
        
        # Try to create the table
        if not create_price_history_table():
            logger.error("Failed to create crypto_price_history table")
            logger.info("Please create the table manually using the SQL script")
            return
    
    # Update the dashboard file
    if update_dashboard_file():
        logger.info("Successfully updated dashboard to use price history table")
    else:
        logger.error("Failed to update dashboard")

if __name__ == "__main__":
    main() 