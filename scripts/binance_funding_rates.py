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
    if df is None:
        return
    
    try:
        # Convert DataFrame to list of dictionaries for insertion
        records = df.to_dict('records')
        
        # Insert data into Supabase
        # Using upsert to handle the unique constraint
        result = supabase.table('binance_funding_rates').upsert(
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
    Fetch current funding rates for all markets from Binance
    Returns a pandas DataFrame with the funding rate data
    """
    # Initialize Binance client
    exchange = ccxt.binance({
        'enableRateLimit': True,
        'options': {
            'defaultType': 'future',  # Use futures markets
        }
    })

    try:
        # Fetch all funding rates
        funding_rates = exchange.fetch_funding_rates()
        
        # Convert to more usable format
        records = []
        
        for symbol, data in funding_rates.items():
            records.append({
                'symbol': symbol,
                'funding_rate': data['fundingRate'],
                'funding_rate_pct': data['fundingRate'] * 100,
                'timestamp': data['timestamp'],
                'datetime': data['datetime'],
            })
        
        # Create DataFrame
        df = pd.DataFrame(records)
        
        # Sort by absolute funding rate to see most extreme values first
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
    if df is None:
        return
    
    # Create output directory
    output_dir = Path('funding_rates')
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
        funding_data['rates'].append({
            'symbol': row['symbol'],
            'funding_rate': float(row['funding_rate']),
            'funding_rate_pct': float(row['funding_rate'] * 100),
            'timestamp': int(row['timestamp']),
            'datetime': row['datetime']
        })
    
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
    if df is None:
        return
    
    print("\nCurrent Funding Rates:")
    print("=" * 80)
    
    # Format for display
    pd.set_option('display.float_format', lambda x: '%.6f' % x)
    display_df = df[['symbol', 'funding_rate_pct', 'datetime']]
    display_df.columns = ['Symbol', 'Funding Rate %', 'DateTime']
    
    print(display_df)
    
    # Print some statistics
    print("\nSummary Statistics:")
    print("-" * 40)
    print(f"Total number of markets: {funding_data['total_markets']}")
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
        
        # Push to Supabase
        push_to_supabase(df)
        
        # Save to local JSON and display (existing functionality)
        funding_data = save_funding_rates_json(df)
        display_funding_rates(df, funding_data)
        
        # Wait for 1 minute before next update
        print("\nWaiting 10 minutes for next update...")
        time.sleep(600) 