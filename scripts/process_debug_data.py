#!/usr/bin/env python3
import sys
import json
import os
from datetime import datetime
import logging
from supabase import create_client
from dotenv import load_dotenv
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_environment():
    # Load environment variables from multiple potential locations
    env_files = ['.env', '.env.local', '../.env', '../.env.local']
    
    for env_file in env_files:
        env_path = Path(env_file)
        if env_path.exists():
            logger.info(f"Loading environment from {env_path.absolute()}")
            load_dotenv(env_path)
            break

    return {
        'SUPABASE_URL': os.getenv('NEXT_PUBLIC_SUPABASE_URL'),
        'SUPABASE_KEY': os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    }

def load_debug_file(filename):
    """Load a debug JSON file"""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading {filename}: {e}")
        return None

def process_and_combine_data():
    """Process debug files and combine data"""
    # Load debug files
    hyperliquid_file = "data/debug/hyperliquid_our_tokens_20241219_233747.json"
    dexscreener_file = "data/debug/dexscreener_readable_20241219_235217.json"
    
    hl_data = load_debug_file(hyperliquid_file)
    dex_data = load_debug_file(dexscreener_file)
    
    if not hl_data or not dex_data:
        logger.error("Failed to load debug files")
        return None
    
    # Combine data
    combined_data = []
    timestamp = datetime.utcnow()
    
    # Process all tokens from both sources
    all_tokens = set(list(dex_data.keys()) + list(hl_data.keys()))
    
    for token in all_tokens:
        dex_metrics = dex_data.get(token, {})
        hl_metrics = hl_data.get(token, {})
        
        metric = {
            "symbol": token,
            "timestamp": timestamp.isoformat(),
            # Hyperliquid data (default to 0 if not available)
            "funding_rate": float(hl_metrics.get('funding_rate', 0)),
            "perp_volume_24h": float(hl_metrics.get('volume_24h', 0)),
            "open_interest": float(hl_metrics.get('open_interest', 0)),
            "mark_price": float(hl_metrics.get('mark_price', 0)),
            # DexScreener data (default to 0 if not available)
            "spot_price": float(dex_metrics.get('spot_price', 0)),
            "spot_volume_24h": float(dex_metrics.get('spot_volume_24h', 0)),
            "liquidity": float(dex_metrics.get('liquidity', 0)),
            "market_cap": float(dex_metrics.get('market_cap', 0)),
            "total_supply": float(dex_metrics.get('total_supply', 0)),
            "price_change_24h": float(dex_metrics.get('price_change_24h', 0)),
            "txns_24h": int(dex_metrics.get('txns_24h', 0))
        }
        
        combined_data.append(metric)
        logger.info(f"Processed data for {token}")
    
    # Save to processed_metrics.json
    with open('data/processed_metrics.json', 'w') as f:
        json.dump(combined_data, f, indent=2)
    
    # Also save to perp_metrics.json for compatibility
    with open('data/perp_metrics.json', 'w') as f:
        json.dump(combined_data, f, indent=2)
    
    return combined_data

def update_supabase(supabase, data):
    """Update Supabase with the combined data"""
    try:
        # Upsert data into perpetual_metrics table
        result = supabase.table('perpetual_metrics').upsert(
            data,
            on_conflict='symbol,timestamp'  # Specify the unique constraint
        ).execute()
        
        logger.info(f"Successfully upserted {len(data)} records to Supabase")
        return result
    except Exception as e:
        logger.error(f"Error updating Supabase: {e}")
        raise

def process_data():
    try:
        # Setup environment
        env = setup_environment()
        if not env['SUPABASE_URL'] or not env['SUPABASE_KEY']:
            raise ValueError("Missing Supabase credentials")

        # Initialize Supabase client
        supabase = create_client(env['SUPABASE_URL'], env['SUPABASE_KEY'])

        # Process and combine data
        combined_data = process_and_combine_data()
        if not combined_data:
            raise ValueError("No data to process")

        # Update Supabase
        result = update_supabase(supabase, combined_data)
        
        return {
            "success": True,
            "message": "Data processed successfully",
            "records": len(combined_data)
        }

    except Exception as e:
        logger.error(f"Error processing data: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        result = process_data()
        print(json.dumps(result))
        sys.exit(0)
    except Exception as e:
        error_message = {"error": str(e)}
        print(json.dumps(error_message), file=sys.stderr)
        sys.exit(1) 