#!/usr/bin/env python3
import sys
import json
import os
from datetime import datetime, UTC
import logging
from supabase import create_client
from dotenv import load_dotenv
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_environment():
    env_files = ['.env', '.env.local', '../.env', '../.env.local']
    
    for env_file in env_files:
        env_path = Path(env_file)
        if env_path.exists():
            load_dotenv(env_path)
            break

    return {
        'SUPABASE_URL': os.getenv('NEXT_PUBLIC_SUPABASE_URL'),
        'SUPABASE_KEY': os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    }

def load_hyperliquid_data():
    """Load the latest hyperliquid data"""
    try:
        with open('data/debug/hyperliquid_our_tokens_20241219_233747.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading hyperliquid data: {e}")
        return {}

def create_metric_record(symbol, timestamp, hl_metrics=None, perp_metric=None):
    """Create a standardized metric record"""
    metric = {
        'symbol': symbol,
        'timestamp': timestamp,
        'funding_rate': 0,
        'perp_volume_24h': 0,
        'open_interest': 0,
        'mark_price': 0,
        'spot_price': 0,
        'spot_volume_24h': 0,
        'liquidity': 0,
        'market_cap': 0,
        'total_supply': 0,
        'price_change_24h': 0,
        'txns_24h': 0
    }

    # Update with Hyperliquid data if available
    if hl_metrics:
        metric.update({
            'funding_rate': float(hl_metrics.get('funding_rate', 0)),
            'perp_volume_24h': float(hl_metrics.get('volume_24h', 0)),
            'open_interest': float(hl_metrics.get('open_interest', 0)),
            'mark_price': float(hl_metrics.get('mark_price', 0))
        })

    # Update with perp metrics if available
    if perp_metric:
        metric.update({
            'spot_price': float(perp_metric.get('spot_price', 0)),
            'spot_volume_24h': float(perp_metric.get('spot_volume_24h', 0)),
            'liquidity': float(perp_metric.get('liquidity', 0)),
            'market_cap': float(perp_metric.get('market_cap', 0)),
            'total_supply': float(perp_metric.get('total_supply', 0)),
            'price_change_24h': float(perp_metric.get('price_change_24h', 0)),
            'txns_24h': int(perp_metric.get('txns_24h', 0))
        })

    return metric

def process_instant_data():
    try:
        # Setup environment
        env = setup_environment()
        if not env['SUPABASE_URL'] or not env['SUPABASE_KEY']:
            raise ValueError("Missing Supabase credentials")

        # Initialize Supabase client
        supabase = create_client(env['SUPABASE_URL'], env['SUPABASE_KEY'])

        # Load both data sources
        with open('data/perp_metrics.json', 'r') as f:
            perp_metrics = json.load(f)
        
        hl_data = load_hyperliquid_data()
        
        # Create a map of existing metrics by symbol
        metrics_map = {metric['symbol']: metric for metric in perp_metrics}
        
        # Update timestamp to current UTC time
        current_time = datetime.now(UTC)
        
        # Process all metrics including Brett from Hyperliquid
        combined_metrics = []
        
        # First, process all perp metrics
        for metric in perp_metrics:
            symbol = metric['symbol']
            hl_metrics = hl_data.get(symbol, {})
            new_metric = create_metric_record(
                symbol=symbol,
                timestamp=current_time.isoformat(),
                hl_metrics=hl_metrics,
                perp_metric=metric
            )
            combined_metrics.append(new_metric)
        
        # Then add any tokens that are only in Hyperliquid (like Brett)
        for symbol, hl_metrics in hl_data.items():
            if symbol not in metrics_map:
                new_metric = create_metric_record(
                    symbol=symbol,
                    timestamp=current_time.isoformat(),
                    hl_metrics=hl_metrics
                )
                combined_metrics.append(new_metric)
                logger.info(f"Added Hyperliquid-only token: {symbol}")

        # Update Supabase
        result = supabase.table('perpetual_metrics').upsert(
            combined_metrics,
            on_conflict='symbol,timestamp'
        ).execute()

        logger.info(f"Successfully processed {len(combined_metrics)} metrics including Hyperliquid data")
        
        return {
            "success": True,
            "message": "Data processed and updated successfully",
            "records": len(combined_metrics),
            "timestamp": current_time.isoformat()
        }

    except Exception as e:
        logger.error(f"Error in instant processing: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        result = process_instant_data()
        print(json.dumps(result))
        sys.exit(0)
    except Exception as e:
        error_message = {"error": str(e)}
        print(json.dumps(error_message), file=sys.stderr)
        sys.exit(1) 