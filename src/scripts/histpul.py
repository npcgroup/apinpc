import aiohttp
import asyncio
import pandas as pd
from datetime import datetime, timedelta
import logging
import os
from typing import List, Dict, Any, Optional
import glob
from dotenv import load_dotenv
import time
import json

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CryptoDataFetcher:
    def __init__(self, api_key: str, data_dir: str = "data/crypto_historical"):
        self.base_url = "https://min-api.cryptocompare.com/data/v2/histohour"
        self.api_key = api_key
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Track failed symbols for reporting
        self.failed_symbols = []
        self.successful_symbols = []
        
    async def fetch_latest_data(self, symbol: str, start_date: datetime) -> Optional[pd.DataFrame]:
        """Fetch latest price data for a symbol from start_date to present"""
        # Remove any 'K' prefix from symbols like 'KPEPE'
        cleaned_symbol = symbol.replace('K', '') if symbol.startswith('K') else symbol
        
        # Calculate the timestamp for the start date
        start_timestamp = int(start_date.timestamp())
        
        params = {
            "fsym": cleaned_symbol,
            "tsym": "USD",
            "limit": 2000,  # Maximum allowed by API
            "toTs": -1,     # Current time
            "api_key": self.api_key
        }
        
        all_data = []
        current_timestamp = int(datetime.now().timestamp())
        
        logger.info(f"Fetching data for {symbol} from {start_date.strftime('%Y-%m-%d')}")
        
        # We need to fetch data in chunks because the API has a limit of 2000 records per request
        retry_count = 0
        max_retries = 3
        
        while current_timestamp > start_timestamp:
            params["toTs"] = current_timestamp
            
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(self.base_url, params=params) as response:
                        if response.status != 200:
                            logger.error(f"Failed to fetch data for {symbol}: HTTP {response.status}")
                            
                            # If we get rate limited, wait and retry
                            if response.status == 429 and retry_count < max_retries:
                                retry_count += 1
                                wait_time = 2 ** retry_count  # Exponential backoff
                                logger.info(f"Rate limited. Retrying in {wait_time} seconds...")
                                await asyncio.sleep(wait_time)
                                continue
                                
                            self.failed_symbols.append(symbol)
                            return None
                        
                        data = await response.json()
                        if data.get("Response") == "Error":
                            logger.error(f"API error for {symbol}: {data.get('Message')}")
                            self.failed_symbols.append(symbol)
                            return None
                        
                        chunk_data = data["Data"]["Data"]
                        if not chunk_data:
                            break
                        
                        all_data.extend(chunk_data)
                        
                        # Update the timestamp for the next request
                        oldest_timestamp = min(item["time"] for item in chunk_data)
                        if oldest_timestamp >= current_timestamp:
                            break
                        
                        current_timestamp = oldest_timestamp - 3600  # Subtract 1 hour to avoid duplicates
                        
                        # If we've reached or gone past the start date, we're done
                        if oldest_timestamp <= start_timestamp:
                            break
                        
                        # Reset retry count on successful request
                        retry_count = 0
                        
                except Exception as e:
                    logger.error(f"Error fetching data for {symbol}: {str(e)}")
                    
                    # Retry on connection errors
                    if retry_count < max_retries:
                        retry_count += 1
                        wait_time = 2 ** retry_count  # Exponential backoff
                        logger.info(f"Connection error. Retrying in {wait_time} seconds...")
                        await asyncio.sleep(wait_time)
                        continue
                    
                    self.failed_symbols.append(symbol)
                    return None
                
                # Add a small delay to avoid hitting rate limits
                await asyncio.sleep(1.0)  # Increased delay to avoid rate limits
        
        # Filter out data before the start date
        filtered_data = [item for item in all_data if item["time"] >= start_timestamp]
        
        if not filtered_data:
            logger.warning(f"No data found for {symbol} after {start_date.strftime('%Y-%m-%d')}")
            self.failed_symbols.append(symbol)
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame(filtered_data)
        
        # Add symbol column
        df['symbol'] = symbol
        
        # Format datetime
        df['datetime'] = df['time'].apply(lambda x: datetime.utcfromtimestamp(x).isoformat())
        df.rename(columns={'time': 'timestamp'}, inplace=True)
        
        # Ensure proper column order
        columns = [
            'symbol',
            'timestamp',
            'datetime',
            'open',
            'high',
            'low',
            'close',
            'volumefrom',
            'volumeto'
        ]
        
        # Select only the columns we need
        df = df[columns]
        
        logger.info(f"Successfully fetched {len(df)} records for {symbol}")
        self.successful_symbols.append(symbol)
        return df

    # Try alternative API if primary fails
    async def fetch_alternative_data(self, symbol: str, start_date: datetime) -> Optional[pd.DataFrame]:
        """Fallback method to fetch data from an alternative endpoint if the main one fails"""
        # Use the histoday endpoint as a fallback
        alt_url = "https://min-api.cryptocompare.com/data/v2/histoday"
        
        cleaned_symbol = symbol.replace('K', '') if symbol.startswith('K') else symbol
        start_timestamp = int(start_date.timestamp())
        
        params = {
            "fsym": cleaned_symbol,
            "tsym": "USD",
            "limit": 365,  # Get up to a year of daily data
            "toTs": -1,
            "api_key": self.api_key
        }
        
        logger.info(f"Trying alternative API for {symbol}")
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(alt_url, params=params) as response:
                    if response.status != 200:
                        logger.error(f"Alternative API failed for {symbol}: HTTP {response.status}")
                        return None
                    
                    data = await response.json()
                    if data.get("Response") == "Error":
                        logger.error(f"Alternative API error for {symbol}: {data.get('Message')}")
                        return None
                    
                    daily_data = data["Data"]["Data"]
                    if not daily_data:
                        return None
                    
                    # Filter by start date
                    filtered_data = [item for item in daily_data if item["time"] >= start_timestamp]
                    
                    if not filtered_data:
                        return None
                    
                    # Convert to DataFrame
                    df = pd.DataFrame(filtered_data)
                    
                    # Add symbol column
                    df['symbol'] = symbol
                    
                    # Format datetime
                    df['datetime'] = df['time'].apply(lambda x: datetime.utcfromtimestamp(x).isoformat())
                    df.rename(columns={'time': 'timestamp'}, inplace=True)
                    
                    # Ensure proper column order
                    columns = [
                        'symbol',
                        'timestamp',
                        'datetime',
                        'open',
                        'high',
                        'low',
                        'close',
                        'volumefrom',
                        'volumeto'
                    ]
                    
                    # Select only the columns we need
                    df = df[columns]
                    
                    logger.info(f"Successfully fetched {len(df)} daily records for {symbol} using alternative API")
                    return df
                
            except Exception as e:
                logger.error(f"Error with alternative API for {symbol}: {str(e)}")
                return None

async def process_symbol(fetcher: CryptoDataFetcher, symbol: str, start_date: datetime) -> Optional[pd.DataFrame]:
    """Process a single symbol and return the DataFrame with latest data"""
    try:
        # Try the primary API first
        df = await fetcher.fetch_latest_data(symbol, start_date)
        
        # If primary API fails, try the alternative
        if df is None:
            logger.info(f"Primary API failed for {symbol}, trying alternative...")
            df = await fetcher.fetch_alternative_data(symbol, start_date)
            
        return df
    except Exception as e:
        logger.error(f"Error processing {symbol}: {str(e)}")
        return None

async def main():
    # Set your API key here
    api_key = "7d1cd0cc86f2bfe98c6ad54865b2a9b8af1b4bf68c3ecf876fc89f99185f485d"
    fetcher = CryptoDataFetcher(api_key)
    
    # Set the start date to February 18th, 2024
    start_date = datetime(2024, 2, 18)
    
    # Get the list of symbols from existing CSV files
    data_dir = "data/crypto_historical"
    csv_files = glob.glob(os.path.join(data_dir, '*_historical.csv'))
    symbols = [os.path.basename(file).replace('_historical.csv', '') for file in csv_files]
    
    if not symbols:
        logger.error("No existing CSV files found.")
        return
    
    logger.info(f"Found {len(symbols)} symbols to update")
    
    # List to store all dataframes
    all_dfs = []
    
    # Process in batches to avoid overwhelming the API
    batch_size = 3  # Reduced batch size to avoid rate limits
    for i in range(0, len(symbols), batch_size):
        batch_symbols = symbols[i:i + batch_size]
        logger.info(f"Processing batch {i//batch_size + 1} of {len(symbols)//batch_size + 1}")
        
        tasks = [process_symbol(fetcher, symbol, start_date) for symbol in batch_symbols]
        results = await asyncio.gather(*tasks)
        
        # Add non-None results to our list
        for df in results:
            if df is not None and not df.empty:
                all_dfs.append(df)
        
        # Add a longer delay between batches to avoid rate limits
        await asyncio.sleep(3)
    
    if not all_dfs:
        logger.error("No data was fetched for any symbol")
        return
    
    # Combine all dataframes
    logger.info("Combining all dataframes...")
    combined_df = pd.concat(all_dfs, ignore_index=True)
    
    # Sort by symbol and timestamp
    combined_df = combined_df.sort_values(['symbol', 'timestamp'])
    
    # Generate output filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"data/latest_price_data_{timestamp}.csv"
    
    # Save to CSV
    combined_df.to_csv(output_file, index=False)
    logger.info(f"Saved combined data to {output_file}")
    
    # Print some stats
    logger.info("\nDataset Statistics:")
    logger.info(f"Total rows: {len(combined_df)}")
    logger.info(f"Unique symbols: {combined_df['symbol'].nunique()}")
    logger.info(f"Date range: {combined_df['datetime'].min()} to {combined_df['datetime'].max()}")
    
    # Report on failed and successful symbols
    logger.info(f"Successfully fetched data for {len(fetcher.successful_symbols)} symbols")
    logger.info(f"Failed to fetch data for {len(fetcher.failed_symbols)} symbols")
    
    if fetcher.failed_symbols:
        logger.info(f"Failed symbols: {fetcher.failed_symbols}")
        
        # Save failed symbols to a file for reference
        with open(f"data/failed_symbols_{timestamp}.json", 'w') as f:
            json.dump(fetcher.failed_symbols, f)
    
    return output_file

if __name__ == "__main__":
    start_time = time.time()
    asyncio.run(main())
    end_time = time.time()
    logger.info(f"Total execution time: {end_time - start_time:.2f} seconds")