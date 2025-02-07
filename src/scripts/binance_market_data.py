import ccxt
import pandas as pd
from datetime import datetime
import time
import json
from pathlib import Path

def fetch_market_data():
    """
    Fetch comprehensive market data for all perpetual contracts from Binance
    Returns a pandas DataFrame with the market data
    """
    # Initialize Binance client
    exchange = ccxt.binance({
        'enableRateLimit': True,
        'options': {
            'defaultType': 'future',  # Use futures markets
        }
    })

    try:
        # Fetch all funding rates first to get active perpetual markets
        funding_rates = exchange.fetch_funding_rates()
        
        # Filter for only USDT-margined futures
        perp_markets = [symbol for symbol in funding_rates.keys() 
                       if symbol.endswith(':USDT')]  # Only USDT-margined
        
        if not perp_markets:
            print("No perpetual markets found")
            return None
            
        print(f"\nFound {len(perp_markets)} perpetual markets")
        for symbol in perp_markets[:5]:  # Print first 5 markets as sample
            print(f"Sample market: {symbol}")
        
        # Fetch all tickers to get mark prices and other market data
        tickers = exchange.fetch_tickers(perp_markets)
        
        # Convert to more usable format
        records = []
        
        for symbol in perp_markets:
            try:
                # Get market info
                market = exchange.market(symbol)
                ticker = tickers.get(symbol, {})
                funding_rate = funding_rates.get(symbol, {})
                
                # Skip if we don't have basic market data
                if not market or not ticker:
                    print(f"Missing market data for {symbol}")
                    continue
                
                # Safely get mark price first as it's needed for calculations
                mark_price = ticker.get('last')
                if mark_price is None or mark_price == 0:
                    print(f"Invalid mark price for {symbol}")
                    continue
                
                # Fetch open interest
                try:
                    oi_data = exchange.fetch_open_interest(symbol)
                    if oi_data is None:
                        print(f"No open interest data for {symbol}")
                        continue
                    
                    # Safely convert values with fallbacks
                    open_interest = float(oi_data.get('openInterestAmount', 0) or 0)
                    open_interest_usd = float(oi_data.get('openInterestValue', open_interest * mark_price) or 0)
                    
                    # Skip if no meaningful open interest
                    if open_interest <= 0:
                        print(f"No open interest for {symbol}")
                        continue
                        
                    # Safely get all other numeric values with fallbacks
                    records.append({
                        'symbol': symbol,
                        'base': market['base'],
                        'quote': market['quote'],
                        # Open Interest data
                        'open_interest': open_interest,
                        'open_interest_usd': open_interest_usd,
                        # Price data
                        'mark_price': float(mark_price),
                        'index_price': float(ticker.get('index', mark_price) or mark_price),
                        'high_24h': float(ticker.get('high', 0) or 0),
                        'low_24h': float(ticker.get('low', 0) or 0),
                        # Volume data
                        'volume_24h': float(ticker.get('quoteVolume', 0) or 0),
                        'volume_base_24h': float(ticker.get('baseVolume', 0) or 0),
                        # Price changes
                        'price_change_24h': float(ticker.get('percentage', 0) or 0),
                        'price_change': float(ticker.get('change', 0) or 0),
                        # Funding data
                        'funding_rate': float(funding_rate.get('fundingRate', 0) or 0),
                        'next_funding_time': funding_rate.get('nextFundingTime'),
                        # Contract info
                        'contract_size': float(market.get('contractSize', 1) or 1),
                        'leverage_max': float(market.get('maxLeverage', 0) or 0),
                        # Timestamps
                        'timestamp': int(datetime.now().timestamp() * 1000),
                        'datetime': datetime.now().isoformat(),
                        'type': 'linear_perpetual'
                    })
                    
                    print(f"Successfully processed {symbol}")
                    
                except Exception as oi_error:
                    print(f"Error fetching open interest for {symbol}: {str(oi_error)}")
                    continue
                
                # Small delay to respect rate limits
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Error processing {symbol}: {str(e)}")
                continue
        
        # Create DataFrame
        df = pd.DataFrame(records)
        
        if not df.empty:
            # Sort by USD value to see largest markets first
            df = df.sort_values('open_interest_usd', ascending=False)
            
            print(f"\nSuccessfully fetched data for {len(df)} markets")
            return df
        else:
            print("No valid market data found")
            return None

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def save_market_data_json(df):
    """
    Save market data to a nicely formatted JSON file
    """
    if df is None or df.empty:
        print("No data to save")
        return
    
    # Create output directory
    output_dir = Path('binance_market_data')
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
    
    print(f"\nSaved market data to {output_file}")
    
    # Also save to latest.json
    latest_file = output_dir / 'latest.json'
    with open(latest_file, 'w') as f:
        json.dump(market_data, f, indent=2)
    
    return market_data

def display_market_data(df, market_data):
    """
    Display market data in a formatted way
    """
    if df is None or df.empty:
        print("No data to display")
        return
    
    print("\nCurrent Perpetual Market Data:")
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

if __name__ == "__main__":
    while True:
        print(f"\nFetching market data at {datetime.now()}")
        df = fetch_market_data()
        if df is not None and not df.empty:
            market_data = save_market_data_json(df)
            display_market_data(df, market_data)
        else:
            print("Failed to fetch market data")
        
        # Wait for 1 minute before next update
        print("\nWaiting 60 seconds for next update...")
        time.sleep(60) 