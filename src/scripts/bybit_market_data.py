import ccxt
import pandas as pd
from datetime import datetime
import time
import json
from pathlib import Path
from supabase import create_client
import os
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

# Setup
load_dotenv()
console = Console()

# Initialize Supabase client
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

def push_to_supabase(df):
    """Push market data to Supabase"""
    if df is None or df.empty:
        return False
    
    try:
        records = []
        for _, row in df.iterrows():
            # Calculate USD values
            mark_price = float(row['mark_price'])
            open_interest = float(row['open_interest'])
            open_interest_usd = open_interest * mark_price
            
            # Create base record with required fields
            record = {
                'symbol': row['symbol'],
                'base': row['base'],
                'quote': row['quote'],
                'open_interest': open_interest,
                'open_interest_usd': open_interest_usd,
                'mark_price': mark_price,
                'volume_24h': float(row.get('volume_24h', 0)),
                'volume_base_24h': float(row.get('volume_base_24h', 0)),
                'price_change_24h': float(row.get('price_change_24h', 0)),
                'funding_rate': float(row.get('funding_rate', 0)),
                'timestamp': int(row['timestamp']),
                'datetime': pd.to_datetime(row['datetime']).isoformat()
            }
            
            # Add optional fields if they exist
            optional_fields = {
                'index_price': 'mark_price',  # fallback to mark_price if index_price not available
                'high_24h': None,
                'low_24h': None,
                'next_funding_time': None,
                'contract_size': None,
                'leverage_max': None
            }
            
            for field, fallback in optional_fields.items():
                try:
                    if field in row and pd.notna(row[field]):
                        record[field] = float(row[field])
                    elif fallback and fallback in row:
                        record[field] = float(row[fallback])
                    else:
                        record[field] = None
                except (ValueError, TypeError):
                    record[field] = None
            
            records.append(record)
            
            # Log sample of processed records
            if len(records) <= 5:
                console.print(f"[dim]Processing {record['symbol']}: "
                          f"OI=${record['open_interest_usd']:,.2f}, "
                          f"Price=${record['mark_price']:,.2f}[/dim]")
        
        # Insert new records
        result = supabase.table('bybit_market_data').insert(records).execute()
        
        console.print(Panel(
            f"✅ Successfully pushed {len(records)} records to Supabase\n"
            f"Sample markets:\n" + "\n".join(
                f"{r['symbol']}: ${r['open_interest_usd']:,.2f} OI" 
                for r in records[:5]
            ),
            style="bold green"
        ))
        return True
        
    except Exception as e:
        if 'duplicate key value violates unique constraint' in str(e):
            console.print("[yellow]Some records already exist (skipped duplicates)[/yellow]")
            return True
        else:
            console.print(Panel(
                f"❌ Error pushing to Supabase: {str(e)}",
                style="bold red"
            ))
            return False

def fetch_market_data():
    """
    Fetch comprehensive market data for all perpetual contracts from Bybit
    Returns a pandas DataFrame with the market data
    """
    # Initialize Bybit client
    exchange = ccxt.bybit({
        'enableRateLimit': True,
        'options': {
            'defaultType': 'linear',  # USDT perpetuals
        }
    })

    try:
        # Fetch all markets first to get proper symbols
        markets = exchange.load_markets()
        
        # Filter for USDT perpetual markets
        perp_markets = [symbol for symbol, market in markets.items() 
                       if market.get('linear') and 
                       market.get('quote') == 'USDT' and
                       not market.get('expiry')]
        
        if not perp_markets:
            print("No perpetual markets found")
            return None
            
        print(f"\nFound {len(perp_markets)} perpetual markets")
        for symbol in perp_markets[:5]:  # Print first 5 markets as sample
            print(f"Sample market: {symbol}")
        
        # Fetch all tickers
        tickers = exchange.fetch_tickers(perp_markets)
        
        # Fetch all funding rates
        funding_rates = {}
        for symbol in perp_markets:
            try:
                funding_rate = exchange.fetch_funding_rate(symbol)
                funding_rates[symbol] = funding_rate
                time.sleep(0.1)  # Rate limiting
            except Exception as e:
                print(f"Error fetching funding rate for {symbol}: {e}")
                continue
        
        # Convert to more usable format
        records = []
        
        for symbol in perp_markets:
            try:
                market = exchange.market(symbol)
                ticker = tickers.get(symbol, {})
                funding_rate = funding_rates.get(symbol, {})
                
                if not market or not ticker:
                    continue
                
                # Get mark price
                mark_price = ticker.get('last')
                if mark_price is None or mark_price == 0:
                    continue
                
                # Fetch open interest
                try:
                    oi_data = exchange.fetch_open_interest(symbol)
                    if oi_data is None:
                        continue
                    
                    open_interest = float(oi_data.get('openInterestAmount', 0) or 0)
                    open_interest_usd = float(oi_data.get('openInterestValue', open_interest * mark_price) or 0)
                    
                    records.append({
                        'symbol': symbol,
                        'base': market['base'],
                        'quote': market['quote'],
                        'open_interest': open_interest,
                        'open_interest_usd': open_interest_usd,
                        'mark_price': float(mark_price),
                        'volume_24h': float(ticker.get('quoteVolume', 0) or 0),
                        'volume_base_24h': float(ticker.get('baseVolume', 0) or 0),
                        'price_change_24h': float(ticker.get('percentage', 0) or 0),
                        'funding_rate': float(funding_rate.get('fundingRate', 0) or 0),
                        'next_funding_time': funding_rate.get('nextFundingTime'),
                        'timestamp': int(datetime.now().timestamp() * 1000),
                        'datetime': datetime.now().isoformat()
                    })
                    
                    print(f"Successfully processed {symbol}")
                    
                except Exception as e:
                    print(f"Error processing open interest for {symbol}: {e}")
                    continue
                
            except Exception as e:
                print(f"Error processing {symbol}: {e}")
                continue
            
            time.sleep(0.1)  # Rate limiting
        
        return pd.DataFrame(records)
    
    except Exception as e:
        print(f"Error fetching market data: {e}")
        return None

def save_market_data_json(df):
    """Save market data to a nicely formatted JSON file"""
    if df is None or df.empty:
        print("No data to save")
        return
    
    output_dir = Path('bybit_market_data')
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Calculate statistics
    total_volume = df['volume_24h'].sum()
    total_oi = df['open_interest_usd'].sum()
    mean_funding = df['funding_rate'].mean()
    
    # Get largest market by open interest
    largest_oi_row = df.loc[df['open_interest_usd'].idxmax()]
    
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
    
    # Save to files
    output_file = output_dir / f'market_data_{timestamp}.json'
    with open(output_file, 'w') as f:
        json.dump(market_data, f, indent=2)
    
    latest_file = output_dir / 'latest.json'
    with open(latest_file, 'w') as f:
        json.dump(market_data, f, indent=2)
    
    return market_data

def display_market_data(df, market_data):
    """Display market data in a formatted way"""
    if df is None or df.empty:
        print("No data to display")
        return
    
    print("\nCurrent Perpetual Market Data:")
    print("=" * 120)
    
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
    
    print("\nSummary Statistics:")
    print("-" * 60)
    print(f"Total number of perpetual markets: {market_data['total_markets']}")
    print(f"Total open interest: ${market_data['statistics']['total_oi_usd']:,.2f}")
    print(f"Total 24h volume: ${market_data['statistics']['total_volume_24h']:,.2f}")
    print(f"Average funding rate: {market_data['statistics']['mean_funding_rate']*100:.4f}%")
    print(f"Largest market by OI: {market_data['statistics']['largest_oi']['symbol']} "
          f"(${market_data['statistics']['largest_oi']['open_interest_usd']:,.2f})")

if __name__ == "__main__":
    while True:
        print(f"\nFetching market data at {datetime.now()}")
        df = fetch_market_data()
        
        if df is not None and not df.empty:
            # Save to JSON (keep existing functionality)
            market_data = save_market_data_json(df)
            display_market_data(df, market_data)
            
            # Push to Supabase
            console.print("[cyan]Pushing data to Supabase...[/cyan]")
            push_to_supabase(df)
        else:
            print("Failed to fetch market data")
        
        print("\nWaiting 60 seconds for next update...")
        time.sleep(60) 