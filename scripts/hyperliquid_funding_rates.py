import ccxt
import pandas as pd
from datetime import datetime
import time
import json
from pathlib import Path
from supabase import create_client
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

def push_to_supabase(df):
    """
    Push funding rates data to Supabase
    """
    if df is None or df.empty:
        return
    
    try:
        # Convert DataFrame to list of dictionaries for insertion
        records = df.to_dict('records')
        
        # Convert datetime strings to proper timestamp format if needed
        for record in records:
            if isinstance(record['datetime'], str):
                record['datetime'] = pd.to_datetime(record['datetime'])
            if record.get('next_funding_time') and isinstance(record['next_funding_time'], str):
                record['next_funding_time'] = pd.to_datetime(record['next_funding_time'])
        
        # Insert data into Supabase
        result = supabase.table('hyperliquid_funding_rates').upsert(
            records,
            on_conflict='symbol,timestamp'
        ).execute()
        
        print(f"Successfully pushed {len(records)} records to Supabase")
        return result
    
    except Exception as e:
        print(f"Error pushing to Supabase: {e}")
        return None

def fetch_all_funding_rates():
    """
    Fetch current funding rates for all perpetual contracts from Hyperliquid
    Returns a pandas DataFrame with the funding rate data
    """
    try:
        # Initialize Hyperliquid client
        exchange = ccxt.hyperliquid({
            'enableRateLimit': True,
            'options': {
                'defaultType': 'swap',
            }
        })

        # Get all markets first
        markets = exchange.load_markets()
        
        # Filter for perpetual contracts only
        perp_markets = [symbol for symbol, market in markets.items() if 
                       market.get('swap', False) and not market.get('spot', False)]
        
        records = []
        current_timestamp = int(datetime.now().timestamp() * 1000)
        
        for symbol in perp_markets:
            try:
                funding_rate = exchange.fetch_funding_rate(symbol)
                
                record = {
                    'symbol': symbol,
                    'funding_rate': float(funding_rate['fundingRate']),
                    'funding_rate_pct': float(funding_rate['fundingRate'] * 100),
                    'timestamp': funding_rate.get('timestamp', current_timestamp),
                    'datetime': funding_rate.get('datetime', datetime.now().isoformat()),
                    'prediction_price': float(funding_rate.get('info', {}).get('premium', 0)),
                    'next_funding_time': funding_rate.get('nextFundingTime')
                }
                
                records.append(record)
                print(f"Successfully fetched {symbol}")
                
                time.sleep(0.1)  # Rate limiting
                
            except Exception as e:
                print(f"Error fetching {symbol}: {str(e)}")
                continue
        
        # Create DataFrame
        df = pd.DataFrame(records)
        
        if not df.empty:
            # Convert types and handle missing values
            df['funding_rate'] = pd.to_numeric(df['funding_rate'], errors='coerce')
            df['funding_rate_pct'] = pd.to_numeric(df['funding_rate_pct'], errors='coerce')
            df['prediction_price'] = pd.to_numeric(df['prediction_price'], errors='coerce')
            df['timestamp'] = pd.to_numeric(df['timestamp'], errors='coerce').fillna(current_timestamp)
            
            # Sort by absolute funding rate
            df['abs_funding_rate'] = df['funding_rate'].abs()
            df = df.sort_values('abs_funding_rate', ascending=False)
            df = df.drop('abs_funding_rate', axis=1)
        
        return df

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def save_funding_rates_json(df):
    """
    Save funding rates to a nicely formatted JSON file
    """
    if df is None or df.empty:
        print("No data to save")
        return
    
    # Create output directory
    output_dir = Path('hyperliquid_funding_rates')
    output_dir.mkdir(exist_ok=True)
    
    # Current timestamp for filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Convert DataFrame to dictionary
    funding_data = {
        'timestamp': timestamp,
        'datetime': datetime.now().isoformat(),
        'total_markets': len(df),
        'statistics': {
            'highest_rate': {
                'symbol': df.iloc[0]['symbol'],
                'rate': float(df.iloc[0]['funding_rate']),
                'rate_pct': float(df.iloc[0]['funding_rate'] * 100)
            },
            'lowest_rate': {
                'symbol': df.iloc[-1]['symbol'],
                'rate': float(df.iloc[-1]['funding_rate']),
                'rate_pct': float(df.iloc[-1]['funding_rate'] * 100)
            },
            'mean_rate': float(df['funding_rate'].mean()),
            'median_rate': float(df['funding_rate'].median())
        },
        'rates': []
    }
    
    # Add each funding rate
    for _, row in df.iterrows():
        rate_data = {
            'symbol': row['symbol'],
            'funding_rate': float(row['funding_rate']),
            'funding_rate_pct': float(row['funding_rate'] * 100),
            'datetime': row['datetime']
        }
        
        # Only add timestamp if it exists and is not None
        if pd.notna(row.get('timestamp')):
            rate_data['timestamp'] = int(row['timestamp'])
        else:
            # Use current timestamp if original is None
            rate_data['timestamp'] = int(datetime.now().timestamp() * 1000)
        
        # Add optional fields if they exist and are not None
        if pd.notna(row.get('prediction_price')):
            rate_data['prediction_price'] = float(row['prediction_price'])
        if pd.notna(row.get('next_funding_time')):
            rate_data['next_funding_time'] = row['next_funding_time']
            
        funding_data['rates'].append(rate_data)
    
    # Save to JSON file
    output_file = output_dir / f'funding_rates_{timestamp}.json'
    with open(output_file, 'w') as f:
        json.dump(funding_data, f, indent=2)
    
    print(f"\nSaved funding rates to {output_file}")
    
    # Also save to latest.json
    latest_file = output_dir / 'latest.json'
    with open(latest_file, 'w') as f:
        json.dump(funding_data, f, indent=2)
    
    return funding_data

def display_funding_rates(df, funding_data):
    """
    Display funding rates in a formatted way
    """
    if df is None or df.empty:
        print("No data to display")
        return
    
    print("\nCurrent Perpetual Funding Rates:")
    print("=" * 80)
    
    # Format for display
    pd.set_option('display.float_format', lambda x: '%.6f' % x)
    display_columns = ['symbol', 'funding_rate_pct', 'datetime']
    if 'prediction_price' in df.columns:
        display_columns.append('prediction_price')
    if 'next_funding_time' in df.columns:
        display_columns.append('next_funding_time')
        
    display_df = df[display_columns]
    display_df.columns = ['Symbol', 'Funding Rate %', 'DateTime'] + \
                        (['Prediction Price'] if 'prediction_price' in df.columns else []) + \
                        (['Next Funding'] if 'next_funding_time' in df.columns else [])
    
    print(display_df)
    
    # Print some statistics
    print("\nSummary Statistics:")
    print("-" * 40)
    print(f"Total number of perpetual markets: {funding_data['total_markets']}")
    print(f"Highest funding rate: {funding_data['statistics']['highest_rate']['rate_pct']:.6f}% "
          f"({funding_data['statistics']['highest_rate']['symbol']})")
    print(f"Lowest funding rate: {funding_data['statistics']['lowest_rate']['rate_pct']:.6f}% "
          f"({funding_data['statistics']['lowest_rate']['symbol']})")
    print(f"Mean funding rate: {funding_data['statistics']['mean_rate']*100:.6f}%")
    print(f"Median funding rate: {funding_data['statistics']['median_rate']*100:.6f}%")

if __name__ == "__main__":
    while True:
        print(f"\nFetching funding rates at {datetime.now()}")
        df = fetch_all_funding_rates()
        
        if df is not None and not df.empty:
            # Push to Supabase
            push_to_supabase(df)
            
            # Save to local JSON and display (existing functionality)
            funding_data = save_funding_rates_json(df)
            display_funding_rates(df, funding_data)
        else:
            print("Failed to fetch funding rates")
        
        # Wait before next update
        print("\nWaiting 60 seconds for next update...")
        time.sleep(60) 