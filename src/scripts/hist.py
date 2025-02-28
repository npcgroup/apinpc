import aiohttp
import asyncio
import csv
import pandas as pd
from datetime import datetime, timedelta
import logging
import os
from typing import List, Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CryptoCompareCollector:
    def __init__(self, api_key: str, data_dir: str = "data/crypto_historical"):
        self.base_url = "https://min-api.cryptocompare.com/data/v2/histohour"
        self.api_key = api_key
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)

    async def fetch_historical_data(self, symbol: str) -> Optional[List[Dict[str, Any]]]:
        # Remove any 'K' prefix from symbols like 'KPEPE'
        cleaned_symbol = symbol.replace('K', '') if symbol.startswith('K') else symbol
        
        params = {
            "fsym": cleaned_symbol,
            "tsym": "USD",
            "limit": 2000,
            "toTs": -1,
            "api_key": self.api_key
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.base_url, params=params) as response:
                    if response.status != 200:
                        logger.error(f"Failed to fetch data for {symbol}: HTTP {response.status}")
                        return None
                    data = await response.json()
                    if data.get("Response") == "Error":
                        logger.error(f"API error for {symbol}: {data.get('Message')}")
                        return None
                    return data["Data"]["Data"]
            except Exception as e:
                logger.error(f"Error fetching data for {symbol}: {str(e)}")
                return None

    def save_data(self, symbol: str, data: List[Dict[str, Any]]):
        filename = os.path.join(self.data_dir, f"{symbol}_historical.csv")
        file_exists = os.path.exists(filename)
        
        with open(filename, mode="a" if file_exists else "w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=["timestamp", "datetime", "open", "high", "low", "close", "volumefrom", "volumeto"])
            if not file_exists:
                writer.writeheader()
            
            for entry in sorted(data, key=lambda x: x["time"]):
                dt = datetime.utcfromtimestamp(entry["time"])
                writer.writerow({
                    "timestamp": entry["time"],
                    "datetime": dt.isoformat(),
                    "open": entry["open"],
                    "high": entry["high"],
                    "low": entry["low"],
                    "close": entry["close"],
                    "volumefrom": entry["volumefrom"],
                    "volumeto": entry["volumeto"]
                })
        logger.info(f"Saved {len(data)} records for {symbol}")

async def process_symbol(collector: CryptoCompareCollector, symbol: str):
    logger.info(f"Fetching data for {symbol}")
    data = await collector.fetch_historical_data(symbol)
    if data:
        collector.save_data(symbol, data)
        logger.info(f"Successfully processed {symbol}")
    else:
        logger.warning(f"No data received for {symbol}")
    # Add a small delay to avoid hitting rate limits
    await asyncio.sleep(0.5)

async def main():
    api_key = "7d1cd0cc86f2bfe98c6ad54865b2a9b8af1b4bf68c3ecf876fc89f99185f485d"
    collector = CryptoCompareCollector(api_key)
    
    # Read symbols from the CSV file
    df = pd.read_csv('/Users/shaanp/Documents/2025-02-16T12-44_export.csv')
    symbols = df['symbol'].unique().tolist()
    
    # Create tasks for all symbols
    tasks = []
    for symbol in symbols:
        task = process_symbol(collector, symbol)
        tasks.append(task)
    
    # Process in batches of 5 to avoid overwhelming the API
    batch_size = 5
    for i in range(0, len(tasks), batch_size):
        batch = tasks[i:i + batch_size]
        await asyncio.gather(*batch)
        # Add a delay between batches
        await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(main())