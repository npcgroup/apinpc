import aiohttp
import asyncio
import json
from datetime import datetime
import logging
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BirdeyeDataCollector:
    def __init__(self, api_key: str):
        self.base_url = "https://public-api.birdeye.so/v1"
        self.headers = {
            "accept": "application/json",
            "x-api-key": api_key,
            "x-chain": "solana"
        }

    async def get_token_data(self, symbol: str, address: str) -> Optional[Dict[str, Any]]:
        """Fetch token data from Birdeye API"""
        async with aiohttp.ClientSession() as session:
            # Get token overview
            overview_url = f"{self.base_url}/defi/token_overview"
            params = {"address": address}
            
            try:
                async with session.get(overview_url, headers=self.headers, params=params) as response:
                    if response.status != 200:
                        logger.error(f"Failed to fetch token overview: {response.status}")
                        return None
                    
                    data = await response.json()
                    if not data.get("success"):
                        logger.error(f"API error for {symbol}: {data.get('message')}")
                        return None

                    result = data.get("data", {})
                    
                    # Format the data according to our interface
                    return {
                        "symbol": symbol,
                        "timestamp": datetime.now().isoformat(),
                        "mark_price": float(result.get("price", 0)),
                        "funding_rate": 0,  # Birdeye doesn't provide funding rate
                        "volume_24h": float(result.get("volume24h", 0)),
                        "price_change_24h": float(result.get("priceChange24h", 0)),
                        "total_supply": float(result.get("supply", 0)),
                        "market_cap": float(result.get("marketCap", 0)),
                        "liquidity": float(result.get("liquidity", 0)),
                        "spot_price": float(result.get("price", 0)),
                        "spot_volume_24h": float(result.get("volume24h", 0)),
                        "txns_24h": int(result.get("txns24h", 0)),
                        "holder_count": int(result.get("holderCount", 0)),
                        "daily_volume": float(result.get("volume24h", 0))
                    }

            except Exception as e:
                logger.error(f"Error fetching data for {symbol} ({address}): {str(e)}")
                return None

async def main():
    # Create output directory if it doesn't exist
    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)

    # Get private API key from .env
    api_key = os.getenv("BIRDEYE_API_KEY")
    if not api_key:
        logger.error("BIRDEYE_API_KEY not found in .env file")
        return
    
    logger.info("Using private Birdeye API key")

    # Using token addresses from helius_ingest.py
    token_addresses = {
        "POPCAT": "7GCihgDB8fe6KNjn2MYtkzZcRjQy3t9GHdC8uHYmW2hr", 
        "WIF": "EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm",
        "GOAT": "CzLSujWBLFsSjncfkh59rUFqvafWcY5tzedWJSuypump",
        "PNUT": "2qEHjDLDLbuBgRYvsxhc5D6uDWAivNFZGan56P1tpump",
        "CHILLGUY": "Df6yfrKC8kZE3KNkrHERKzAetSxbrWeniQfyJY4Jpump",
        "MOODENG": "ED5nyyWEzpPPiWimP8vYm7sD7TD3LAt3Q3gRTWHzPJBY",
        "MEW": "MEW1gQWJ3nEXg2qgERiKu7FAFj79PHvQVREQUzScPP5",
        "BRETT": "BRETTqYJxZ3qZzFrcJLtQwEqNRGZjxj7PvzjzwJhGXL"
    }

    collector = BirdeyeDataCollector(api_key)
    
    try:
        print("\n🌟 Starting Birdeye Data Collection 🌟\n")
        
        # Fetch data for all tokens
        results = []
        for symbol, address in token_addresses.items():
            try:
                data = await collector.get_token_data(symbol, address)
                if data:
                    results.append(data)
                    logger.info(f"Successfully collected data for {symbol}")
            except Exception as e:
                logger.error(f"Error processing {symbol}: {str(e)}")

        # Save results
        if results:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(output_dir, f'all_data_{timestamp}.json')
            
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            logger.info(f"Data saved to {output_file}")
            print(f"\n✅ Data collection complete. Results saved to {output_file}")
            
            # Print summary
            print("\nData Summary:")
            print("-" * 60)
            for result in results:
                symbol = result['symbol']
                print(f"\n{symbol}:")
                print(f"  Price: ${result['spot_price']:,.8f}")
                print(f"  24h Volume: ${result['volume_24h']:,.2f}")
                print(f"  Market Cap: ${result['market_cap']:,.2f}")
                print(f"  Holders: {result['holder_count']:,}")
                print(f"  24h Transactions: {result['txns_24h']:,}")
        else:
            logger.error("No data was collected")
            
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())