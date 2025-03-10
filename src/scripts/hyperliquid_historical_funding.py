#!/usr/bin/env python3
"""
Hyperliquid Historical Funding Rates Collector

This script fetches historical funding rates from Hyperliquid for all available assets
and stores them in a Supabase table for analysis.
"""

import os
import time
import logging
import argparse
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd
import requests
from dotenv import load_dotenv
from supabase import create_client
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('hyperliquid_historical_funding.log')
    ]
)
logger = logging.getLogger(__name__)
console = Console()

# Load environment variables
load_dotenv()

# Constants
HYPERLIQUID_API_URL = "https://api.hyperliquid.xyz/info"
SUPABASE_TABLE_NAME = "hyperliquid_historical_funding"
MAX_WORKERS = 5  # Number of parallel workers for fetching data
CHUNK_SIZE = 30  # Days per chunk when fetching historical data
RATE_LIMIT_DELAY = 0.5  # Seconds between API calls to avoid rate limiting

def get_supabase_client():
    """Initialize and return a Supabase client"""
    try:
        supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        supabase_key = os.getenv("NEXT_PUBLIC_SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            logger.error("Missing Supabase credentials")
            return None
            
        # Initialize Supabase client with minimal parameters
        return create_client(supabase_url, supabase_key)
    except Exception as e:
        logger.error(f"Error initializing Supabase client: {e}")
        return None

def get_all_hyperliquid_assets() -> List[str]:
    """Fetch all available assets from Hyperliquid"""
    try:
        # API endpoint for Hyperliquid
        url = HYPERLIQUID_API_URL
        
        # Request payload
        payload = {
            "type": "metaAndAssetCtxs"
        }
        
        # Headers
        headers = {
            "Content-Type": "application/json"
        }
        
        # Make the API call with timeout
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        # Check if the request was successful
        if response.status_code != 200:
            logger.error(f"Failed to fetch Hyperliquid assets: HTTP {response.status_code}")
            return []
        
        # Parse the response
        try:
            data = response.json()
        except Exception as json_error:
            logger.error(f"Failed to parse Hyperliquid API response: {str(json_error)}")
            return []
        
        # Extract universe (metadata)
        if not data or len(data) < 1 or not isinstance(data[0], dict) or 'universe' not in data[0]:
            logger.error("Invalid response format from Hyperliquid API")
            return []
            
        universe = data[0].get('universe', [])
        
        # Extract asset names
        assets = [asset.get('name') for asset in universe if asset.get('name')]
        
        logger.info(f"Found {len(assets)} assets on Hyperliquid")
        return assets

    except Exception as e:
        logger.error(f"Error fetching Hyperliquid assets: {e}")
        return []

def get_funding_history(coin: str, start_time: int, end_time: int) -> List[Dict]:
    """Fetch historical funding rates for a specific coin and time range"""
    try:
        # API endpoint for Hyperliquid
        url = HYPERLIQUID_API_URL
        
        # Request payload
        payload = {
            "type": "fundingHistory",
            "coin": coin,
            "startTime": start_time,
            "endTime": end_time
        }
        
        # Headers
        headers = {
            "Content-Type": "application/json"
        }
        
        # Make the API call with timeout
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        # Check if the request was successful
        if response.status_code != 200:
            logger.error(f"Failed to fetch funding history for {coin}: HTTP {response.status_code}")
            return []
        
        # Parse the response
        try:
            data = response.json()
            return data
        except Exception as json_error:
            logger.error(f"Failed to parse funding history for {coin}: {str(json_error)}")
            return []

    except Exception as e:
        logger.error(f"Error fetching funding history for {coin}: {e}")
        return []

def fetch_asset_history(asset: str, start_date: datetime, end_date: datetime) -> List[Dict]:
    """Fetch all historical funding rates for an asset in chunks"""
    all_history = []
    
    # Convert dates to milliseconds
    current_start = int(start_date.timestamp() * 1000)
    final_end = int(end_date.timestamp() * 1000)
    
    # Fetch data in chunks to avoid timeouts and large responses
    while current_start < final_end:
        # Calculate chunk end time
        chunk_end = min(current_start + (CHUNK_SIZE * 24 * 60 * 60 * 1000), final_end)
        
        # Fetch funding history for this chunk
        history = get_funding_history(asset, current_start, chunk_end)
        
        if history:
            all_history.extend(history)
            logger.info(f"Fetched {len(history)} funding rates for {asset} from {datetime.fromtimestamp(current_start/1000)} to {datetime.fromtimestamp(chunk_end/1000)}")
        else:
            logger.warning(f"No funding rates found for {asset} from {datetime.fromtimestamp(current_start/1000)} to {datetime.fromtimestamp(chunk_end/1000)}")
        
        # Move to next chunk
        current_start = chunk_end
        
        # Respect rate limits
        time.sleep(RATE_LIMIT_DELAY)
    
    return all_history

def process_asset(asset: str, start_date: datetime, end_date: datetime) -> List[Dict]:
    """Process a single asset and return its historical funding rates"""
    try:
        logger.info(f"Fetching historical funding rates for {asset}")
        history = fetch_asset_history(asset, start_date, end_date)
        
        # Process the data
        processed_data = []
        for entry in history:
            try:
                processed_entry = {
                    'asset': entry.get('coin', asset),
                    'funding_rate': float(entry.get('fundingRate', 0)),
                    'premium': float(entry.get('premium', 0)),
                    'timestamp': entry.get('time', 0),
                    'datetime': datetime.fromtimestamp(entry.get('time', 0) / 1000).isoformat(),
                    'exchange': 'Hyperliquid',
                    'created_at': datetime.now().isoformat()
                }
                processed_data.append(processed_entry)
            except Exception as e:
                logger.error(f"Error processing entry for {asset}: {e}")
                continue
        
        logger.info(f"Processed {len(processed_data)} funding rates for {asset}")
        return processed_data
    
    except Exception as e:
        logger.error(f"Error processing asset {asset}: {e}")
        return []

def push_to_supabase(data: List[Dict], batch_size: int = 100) -> bool:
    """Push data to Supabase in batches"""
    if not data:
        logger.warning("No data to push to Supabase")
        return False
    
    try:
        supabase = get_supabase_client()
        if not supabase:
            return False
        
        # Push data in batches to avoid payload size issues
        success = True
        for i in range(0, len(data), batch_size):
            batch = data[i:i+batch_size]
            try:
                response = supabase.table(SUPABASE_TABLE_NAME).insert(batch).execute()
                logger.info(f"Pushed batch {i//batch_size + 1} with {len(batch)} records")
            except Exception as e:
                logger.error(f"Error pushing batch {i//batch_size + 1} to Supabase: {e}")
                success = False
        
        return success
    
    except Exception as e:
        logger.error(f"Error pushing data to Supabase: {e}")
        return False

def ensure_table_exists() -> bool:
    """Ensure the Supabase table exists, create it if it doesn't"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return False
        
        # Check if table exists by querying it
        try:
            response = supabase.table(SUPABASE_TABLE_NAME).select("count", count="exact").limit(1).execute()
            logger.info(f"Table {SUPABASE_TABLE_NAME} exists")
            return True
        except Exception as e:
            # Table might not exist, let's create it by inserting a dummy record
            # This is a workaround since supabase-py doesn't have direct table creation
            logger.warning(f"Table {SUPABASE_TABLE_NAME} might not exist: {e}")
            
            try:
                # Create a dummy record to create the table
                dummy_record = {
                    'asset': 'DUMMY',
                    'funding_rate': 0.0,
                    'premium': 0.0,
                    'timestamp': int(time.time() * 1000),
                    'datetime': datetime.now().isoformat(),
                    'exchange': 'Hyperliquid'
                }
                
                # Insert the dummy record to create the table
                response = supabase.table(SUPABASE_TABLE_NAME).insert(dummy_record).execute()
                logger.info(f"Created table {SUPABASE_TABLE_NAME} with dummy record")
                
                # Delete the dummy record
                try:
                    supabase.table(SUPABASE_TABLE_NAME).delete().eq('asset', 'DUMMY').execute()
                    logger.info("Deleted dummy record")
                except Exception as del_error:
                    logger.warning(f"Could not delete dummy record: {del_error}")
                
                return True
            except Exception as create_error:
                logger.error(f"Error creating table: {create_error}")
                logger.error("Please create the table manually using the SQL script")
                create_table_manually()
                return False
    
    except Exception as e:
        logger.error(f"Error ensuring table exists: {e}")
        create_table_manually()
        return False

def create_table_manually():
    """Provide instructions for creating the table manually"""
    print("\n" + "="*80)
    print("TABLE CREATION REQUIRED")
    print("="*80)
    print("\nThe script needs a table in Supabase to store the historical funding rates.")
    print("Please create the table manually by following these steps:")
    print("\n1. Log in to your Supabase dashboard")
    print("2. Go to the SQL Editor")
    print("3. Run the following SQL:")
    print("\n```sql")
    print(f"""
CREATE TABLE IF NOT EXISTS {SUPABASE_TABLE_NAME} (
    id BIGSERIAL PRIMARY KEY,
    asset TEXT NOT NULL,
    funding_rate FLOAT NOT NULL,
    premium FLOAT,
    timestamp BIGINT NOT NULL,
    datetime TEXT NOT NULL,
    exchange TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(asset, timestamp, exchange)
);

CREATE INDEX IF NOT EXISTS idx_{SUPABASE_TABLE_NAME}_asset 
ON {SUPABASE_TABLE_NAME}(asset);

CREATE INDEX IF NOT EXISTS idx_{SUPABASE_TABLE_NAME}_timestamp 
ON {SUPABASE_TABLE_NAME}(timestamp);
    """)
    print("```")
    print("\n4. Run the script again after creating the table")
    print("="*80 + "\n")

def main():
    """Main function to fetch and store historical funding rates"""
    parser = argparse.ArgumentParser(description='Fetch historical funding rates from Hyperliquid')
    parser.add_argument('--days', type=int, default=90, help='Number of days of historical data to fetch')
    parser.add_argument('--assets', type=str, nargs='+', help='Specific assets to fetch (default: all assets)')
    parser.add_argument('--create-table', action='store_true', help='Show SQL to create the table and exit')
    args = parser.parse_args()
    
    # If --create-table is specified, show the SQL and exit
    if args.create_table:
        create_table_manually()
        return
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=args.days)
    
    logger.info(f"Fetching historical funding rates from {start_date} to {end_date}")
    
    # Ensure the Supabase table exists
    if not ensure_table_exists():
        logger.error("Failed to ensure Supabase table exists, exiting")
        return
    
    # Get assets to process
    if args.assets:
        assets = args.assets
        logger.info(f"Using provided assets: {assets}")
    else:
        assets = get_all_hyperliquid_assets()
        if not assets:
            logger.error("Failed to fetch assets from Hyperliquid, exiting")
            return
    
    # Process assets in parallel
    all_data = []
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
    ) as progress:
        task = progress.add_task("[cyan]Processing assets...", total=len(assets))
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # Submit all tasks
            future_to_asset = {
                executor.submit(process_asset, asset, start_date, end_date): asset 
                for asset in assets
            }
            
            # Process results as they complete
            for future in as_completed(future_to_asset):
                asset = future_to_asset[future]
                try:
                    data = future.result()
                    all_data.extend(data)
                    progress.update(task, advance=1)
                except Exception as e:
                    logger.error(f"Error processing {asset}: {e}")
                    progress.update(task, advance=1)
    
    # Push data to Supabase
    logger.info(f"Pushing {len(all_data)} records to Supabase")
    if push_to_supabase(all_data):
        logger.info("Successfully pushed data to Supabase")
    else:
        logger.error("Failed to push data to Supabase")

if __name__ == "__main__":
    main() 