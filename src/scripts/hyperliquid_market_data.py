import ccxt
import pandas as pd
from datetime import datetime
import time
import json
from pathlib import Path
from supabase import create_client
import os
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase = create_client(
    os.getenv('NEXT_PUBLIC_SUPABASE_URL'),
    os.getenv('NEXT_PUBLIC_SUPABASE_KEY')
)

def push_to_supabase(df):
    """
    Push market data to Supabase
    """
    if df is None or df.empty:
        return
    
    try:
        records = df.to_dict('records')
        
        # Convert datetime strings to proper timestamp format
        for record in records:
            if isinstance(record['datetime'], str):
                record['datetime'] = pd.to_datetime(record['datetime'])
        
        result = supabase.table('hyperliquid_market_data').upsert(
            records,
            on_conflict='symbol,timestamp'
        ).execute()
        
        logger.info(f"Successfully pushed {len(records)} records to Supabase")
        return result
        
    except Exception as e:
        logger.error(f"Error pushing to Supabase: {e}")
        return None

def fetch_market_data():
    """
    Fetch comprehensive market data for all perpetual contracts from Hyperliquid
    Returns a pandas DataFrame with the market data
    """
    try:
        # Initialize Hyperliquid client with correct settings
        exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {
                'defaultType': 'swap',
                'adjustForTimeDifference': True,
                'recvWindow': 60000
            },
            'timeout': 30000,
        })

        logger.info("Initializing market data fetch...")
        
        # Get all markets first
        markets = exchange.load_markets()
        
        # Filter for perpetual contracts only
        perp_markets = [symbol for symbol, market in markets.items() if 
                       market.get('swap', False) and not market.get('spot', False)]
        
        if not perp_markets:
            logger.error("No perpetual markets found")
            return None
            
        logger.info(f"Found {len(perp_markets)} perpetual markets")
        
        # Fetch all data in parallel
        tickers = exchange.fetch_tickers(perp_markets)
        funding_rates = exchange.fetch_funding_rates(perp_markets)
        
        records = []
        current_timestamp = int(datetime.now().timestamp() * 1000)
        
        for symbol in perp_markets:
            try:
                market = exchange.market(symbol)
                ticker = tickers.get(symbol, {})
                funding_rate = funding_rates.get(symbol, {})
                
                if not market:
                    logger.warning(f"Missing market data for {symbol}")
                    continue
                
                # Get mark price with fallbacks
                mark_price = (
                    ticker.get('last') or 
                    ticker.get('close') or 
                    ticker.get('mark') or 
                    ticker.get('price') or 
                    0
                )
                
                # Retry mark price fetch if needed
                if mark_price == 0:
                    try:
                        single_ticker = exchange.fetch_ticker(symbol)
                        mark_price = single_ticker.get('last', 0)
                    except Exception as e:
                        logger.warning(f"Failed to fetch individual ticker for {symbol}: {e}")
                
                if mark_price <= 0:
                    logger.warning(f"Invalid mark price for {symbol}")
                    continue
                
                # Fetch open interest with retry
                try:
                    oi_data = exchange.fetch_open_interest(symbol)
                    if not oi_data:
                        logger.warning(f"No open interest data for {symbol}")
                        oi_data = {'openInterest': 0}
                except Exception as e:
                    logger.warning(f"Failed to fetch open interest for {symbol}: {e}")
                    oi_data = {'openInterest': 0}
                
                open_interest = float(oi_data.get('openInterest', 0))
                open_interest_usd = open_interest * mark_price
                
                # Get volume with fallbacks
                volume_24h = float(ticker.get('quoteVolume') or ticker.get('volumeUsd') or ticker.get('volume', 0))
                volume_base_24h = float(ticker.get('baseVolume') or ticker.get('volume', 0))
                
                record = {
                    'symbol': symbol,
                    'base': market['base'],
                    'quote': market['quote'],
                    'open_interest': open_interest,
                    'open_interest_usd': open_interest_usd,
                    'mark_price': float(mark_price),
                    'index_price': float(ticker.get('index', mark_price) or mark_price),
                    'volume_24h': volume_24h,
                    'volume_base_24h': volume_base_24h,
                    'price_change_24h': float(ticker.get('percentage', 0) or ticker.get('change', 0) or 0),
                    'funding_rate': float(funding_rate.get('fundingRate', 0) or 0),
                    'next_funding_time': funding_rate.get('nextFundingTime'),
                    'contract_size': float(market.get('contractSize', 1) or 1),
                    'leverage_max': float(market.get('maxLeverage', 0) or 0),
                    'timestamp': current_timestamp,
                    'datetime': datetime.now().isoformat(),
                    'type': 'linear_perpetual'
                }
                
                records.append(record)
                logger.debug(f"Successfully processed {symbol}")
                
                # Reduced rate limiting since we're using bulk fetches
                time.sleep(0.05)
                
            except Exception as e:
                logger.error(f"Error processing {symbol}: {str(e)}")
                continue
        
        # Create DataFrame
        df = pd.DataFrame(records)
        
        if not df.empty:
            # Sort by USD value
            df = df.sort_values('volume_24h', ascending=False)
            logger.info(f"Successfully fetched data for {len(df)} markets")
            
            # Convert timestamp columns to proper format for Supabase
            df['datetime'] = pd.to_datetime(df['datetime'])
            if 'next_funding_time' in df.columns:
                df['next_funding_time'] = pd.to_datetime(df['next_funding_time'], unit='ms')
            
            return df
        else:
            logger.error("No valid market data found")
            return None

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return None

def save_market_data_json(df):
    """
    Save market data to a nicely formatted JSON file
    """
    if df is None or df.empty:
        logger.error("No data to save")
        return
    
    try:
        # Create output directory
        output_dir = Path('hyperliquid_market_data')
        output_dir.mkdir(exist_ok=True)
        
        # Current timestamp for filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Calculate statistics
        total_volume = df['volume_24h'].sum()
        total_oi = df['open_interest_usd'].sum()
        mean_funding = df['funding_rate'].mean()
        
        # Get largest market by open interest
        largest_oi_row = df.loc[df['open_interest_usd'].idxmax()]
        
        # Convert DataFrame to dictionary
        market_data = {
            'timestamp': timestamp,
            'datetime': datetime.now().isoformat(),
            'total_markets': len(df),
            'statistics': {
                'total_oi_usd': float(total_oi),
                'total_volume_24h': float(total_volume),
                'mean_funding_rate': float(mean_funding),
                'mean_oi_usd': float(df['open_interest_usd'].mean()),
                'median_oi_usd': float(df['open_interest_usd'].median()),
                'largest_oi': {
                    'symbol': largest_oi_row['symbol'],
                    'open_interest_usd': float(largest_oi_row['open_interest_usd'])
                }
            },
            'markets': df.to_dict('records')
        }
        
        # Save to JSON file
        output_file = output_dir / f'market_data_{timestamp}.json'
        with open(output_file, 'w') as f:
            json.dump(market_data, f, indent=2)
        
        logger.info(f"Saved market data to {output_file}")
        
        # Also save to latest.json
        latest_file = output_dir / 'latest.json'
        with open(latest_file, 'w') as f:
            json.dump(market_data, f, indent=2)
        
        return market_data

    except Exception as e:
        logger.error(f"Error saving market data: {e}", exc_info=True)
        return None

def display_market_data(df, market_data):
    """
    Display market data in a formatted way
    """
    if df is None or df.empty:
        logger.error("No data to display")
        return
    
    try:
        print("\nCurrent Hyperliquid Market Data:")
        print("=" * 120)
        
        # Format for display
        pd.set_option('display.float_format', lambda x: '%.2f' % x)
        display_df = df[[
            'symbol', 'mark_price', 'open_interest', 'open_interest_usd', 
            'volume_24h', 'price_change_24h', 'funding_rate'
        ]]
        display_df.columns = [
            'Symbol', 'Mark Price', 'Open Interest', 'Open Interest (USD)', 
            '24h Volume', '24h Change %', 'Funding Rate %'
        ]
        
        print(display_df)
        
        # Print some statistics
        print("\nSummary Statistics:")
        print("-" * 60)
        print(f"Total number of perpetual markets: {market_data['total_markets']}")
        print(f"Total open interest: ${market_data['statistics']['total_oi_usd']:,.2f}")
        print(f"Total 24h volume: ${market_data['statistics']['total_volume_24h']:,.2f}")
        print(f"Average funding rate: {market_data['statistics']['mean_funding_rate']*100:.4f}%")
        print(f"Largest market by OI: {market_data['statistics']['largest_oi']['symbol']} "
              f"(${market_data['statistics']['largest_oi']['open_interest_usd']:,.2f})")

    except Exception as e:
        logger.error(f"Error displaying market data: {e}", exc_info=True)

if __name__ == "__main__":
    logger.info("Starting Hyperliquid market data collection")
    
    while True:
        try:
            logger.info(f"Fetching market data at {datetime.now()}")
            df = fetch_market_data()
            
            if df is not None and not df.empty:
                # Push to Supabase
                push_to_supabase(df)
                
                # Save to local JSON and display
                market_data = save_market_data_json(df)
                display_market_data(df, market_data)
            else:
                logger.error("Failed to fetch market data")
            
            # Wait for next update
            logger.info("Waiting 60 seconds for next update...")
            time.sleep(60)
            
        except Exception as e:
            logger.error(f"Error in main loop: {e}", exc_info=True)
            time.sleep(60)  # Still wait before retrying 