#!/usr/bin/env python3
"""
Price History Data Collector

This script fetches historical price data from exchanges and stores it in Supabase.
"""

import os
import logging
import pandas as pd
import ccxt
import time
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from supabase import create_client
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('price_history.log')
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
except Exception as e:
    logger.error(f"Error initializing Supabase client: {e}")
    supabase = None

# Initialize exchange clients
try:
    binance = ccxt.binance({'enableRateLimit': True})
    hyperliquid = ccxt.hyperliquid({'enableRateLimit': True})
except Exception as e:
    logger.error(f"Error initializing exchange clients: {e}")
    binance = None
    hyperliquid = None

def get_symbols(exchange_name='binance', limit=50):
    """Get top symbols by volume from an exchange"""
    try:
        if exchange_name.lower() == 'binance' and binance:
            markets = binance.fetch_markets()
            # Filter for USDT perpetual futures
            perp_markets = [m for m in markets if m['quote'] == 'USDT' and m['type'] == 'swap']
            # Sort by volume if available
            if perp_markets and 'info' in perp_markets[0] and 'volume' in perp_markets[0]['info']:
                perp_markets.sort(key=lambda x: float(x['info'].get('volume', 0)), reverse=True)
            # Extract symbols
            symbols = [m['base'] for m in perp_markets[:limit]]
            return symbols
        elif exchange_name.lower() == 'hyperliquid' and hyperliquid:
            markets = hyperliquid.fetch_markets()
            # Filter for USD perpetual futures
            perp_markets = [m for m in markets if m['quote'] == 'USD' and m['type'] == 'swap']
            # Sort by volume if available
            if perp_markets and 'info' in perp_markets[0] and 'volume' in perp_markets[0]['info']:
                perp_markets.sort(key=lambda x: float(x['info'].get('volume', 0)), reverse=True)
            # Extract symbols
            symbols = [m['base'] for m in perp_markets[:limit]]
            return symbols
        else:
            logger.error(f"Exchange {exchange_name} not supported or not initialized")
            return []
    except Exception as e:
        logger.error(f"Error getting symbols from {exchange_name}: {e}")
        return []

def fetch_price_history(symbol, exchange_name, days=30, timeframe='1h'):
    """Fetch price history for a symbol from an exchange"""
    try:
        # Calculate time range
        end_time = int(time.time() * 1000)
        start_time = end_time - (days * 24 * 60 * 60 * 1000)
        
        # Select exchange
        if exchange_name.lower() == 'binance' and binance:
            exchange = binance
            symbol_with_quote = f"{symbol}/USDT"
        elif exchange_name.lower() == 'hyperliquid' and hyperliquid:
            exchange = hyperliquid
            symbol_with_quote = f"{symbol}/USD"
        else:
            logger.error(f"Exchange {exchange_name} not supported or not initialized")
            return pd.DataFrame()
        
        # Fetch OHLCV data
        ohlcv = exchange.fetch_ohlcv(
            symbol_with_quote,
            timeframe=timeframe,
            since=start_time,
            limit=1000  # Most exchanges limit to 1000 candles per request
        )
        
        if not ohlcv:
            logger.warning(f"No price data retrieved for {symbol} from {exchange_name}")
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
        df['symbol'] = symbol
        df['exchange'] = exchange_name
        
        logger.info(f"Retrieved {len(df)} candles for {symbol} from {exchange_name}")
        return df
    
    except Exception as e:
        logger.error(f"Error fetching price history for {symbol} from {exchange_name}: {e}")
        return pd.DataFrame()

def push_to_supabase(df, batch_size=100):
    """Push price history data to Supabase"""
    if df.empty:
        logger.warning("No data to push to Supabase")
        return False
    
    try:
        # Prepare data for Supabase
        records = []
        for _, row in df.iterrows():
            records.append({
                'symbol': row['symbol'],
                'exchange': row['exchange'],
                'datetime': row['datetime'].isoformat(),
                'price': float(row['close']),
                'volume': float(row['volume']),
                'high': float(row['high']),
                'low': float(row['low']),
                'open': float(row['open']),
                'created_at': datetime.now(timezone.utc).isoformat()
            })
        
        # Push data in batches
        success_count = 0
        for i in range(0, len(records), batch_size):
            batch = records[i:i+batch_size]
            try:
                response = supabase.table('crypto_price_history').insert(batch).execute()
                success_count += len(batch)
                logger.info(f"Pushed batch {i//batch_size + 1} with {len(batch)} records")
            except Exception as e:
                logger.error(f"Error pushing batch {i//batch_size + 1} to Supabase: {e}")
        
        logger.info(f"Successfully pushed {success_count}/{len(records)} records to Supabase")
        return success_count > 0
    
    except Exception as e:
        logger.error(f"Error pushing data to Supabase: {e}")
        return False

def process_symbol(symbol, exchange, days, timeframe):
    """Process a single symbol"""
    try:
        df = fetch_price_history(symbol, exchange, days, timeframe)
        if not df.empty:
            return df
        return None
    except Exception as e:
        logger.error(f"Error processing {symbol} from {exchange}: {e}")
        return None

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Fetch and store price history data')
    parser.add_argument('--days', type=int, default=30, help='Number of days of historical data to fetch')
    parser.add_argument('--symbols', type=str, nargs='+', help='Specific symbols to fetch (default: top by volume)')
    parser.add_argument('--exchange', type=str, default='binance', choices=['binance', 'hyperliquid', 'both'], 
                        help='Exchange to fetch data from')
    parser.add_argument('--limit', type=int, default=50, help='Limit number of symbols to fetch')
    parser.add_argument('--timeframe', type=str, default='1h', choices=['1m', '5m', '15m', '30m', '1h', '4h', '1d'],
                        help='Timeframe for price data')
    parser.add_argument('--workers', type=int, default=5, help='Number of worker threads')
    args = parser.parse_args()
    
    # Get symbols to process
    symbols_to_process = []
    if args.symbols:
        symbols_to_process = args.symbols
        logger.info(f"Using provided symbols: {symbols_to_process}")
    else:
        if args.exchange == 'binance' or args.exchange == 'both':
            binance_symbols = get_symbols('binance', args.limit)
            symbols_to_process.extend(binance_symbols)
            logger.info(f"Got {len(binance_symbols)} symbols from Binance")
        
        if args.exchange == 'hyperliquid' or args.exchange == 'both':
            hyperliquid_symbols = get_symbols('hyperliquid', args.limit)
            symbols_to_process.extend(hyperliquid_symbols)
            logger.info(f"Got {len(hyperliquid_symbols)} symbols from Hyperliquid")
        
        # Remove duplicates
        symbols_to_process = list(set(symbols_to_process))
        logger.info(f"Processing {len(symbols_to_process)} unique symbols")
    
    if not symbols_to_process:
        logger.error("No symbols to process")
        return
    
    # Determine exchanges to use
    exchanges = []
    if args.exchange == 'binance' or args.exchange == 'both':
        exchanges.append('binance')
    if args.exchange == 'hyperliquid' or args.exchange == 'both':
        exchanges.append('hyperliquid')
    
    # Process symbols in parallel
    all_data = pd.DataFrame()
    
    for exchange in exchanges:
        logger.info(f"Processing {len(symbols_to_process)} symbols from {exchange}")
        
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            # Create tasks
            futures = {
                executor.submit(process_symbol, symbol, exchange, args.days, args.timeframe): symbol 
                for symbol in symbols_to_process
            }
            
            # Process results as they complete
            for future in tqdm(as_completed(futures), total=len(futures), desc=f"Fetching {exchange} data"):
                symbol = futures[future]
                try:
                    result = future.result()
                    if result is not None and not result.empty:
                        all_data = pd.concat([all_data, result], ignore_index=True)
                except Exception as e:
                    logger.error(f"Error processing {symbol} from {exchange}: {e}")
    
    # Push data to Supabase
    if not all_data.empty:
        logger.info(f"Pushing {len(all_data)} records to Supabase")
        if push_to_supabase(all_data):
            logger.info("Successfully pushed data to Supabase")
        else:
            logger.error("Failed to push data to Supabase")
    else:
        logger.warning("No data to push to Supabase")

if __name__ == "__main__":
    main() 