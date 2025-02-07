import ccxt.async_support as ccxt
import asyncio
import json
from datetime import datetime, timedelta
import logging
import os
from typing import Dict, Any, Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HyperliquidFundingCollector:
    def __init__(self):
        self.exchange = ccxt.hyperliquid({
            'enableRateLimit': True,
            'timeout': 30000,
        })
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.exchange.close()

    async def get_markets(self) -> list:
        """Fetch all available markets"""
        try:
            markets = await self.exchange.load_markets()
            return [symbol for symbol in markets.keys() if '/USDT:USDT' in symbol]
        except Exception as e:
            logger.error(f"Error fetching markets: {str(e)}")
            return []

    async def get_funding_rate_history(self, symbol: str, since: Optional[int] = None, limit: int = 100) -> list:
        """Fetch funding rate history for a specific symbol"""
        try:
            funding_history = await self.exchange.fetchFundingRateHistory(
                symbol=symbol,
                since=since,
                limit=limit
            )
            return funding_history
        except Exception as e:
            logger.error(f"Error fetching funding history for {symbol}: {str(e)}")
            return []

    async def collect_funding_data(self):
        """Collect funding rate history for all markets"""
        try:
            # Get all markets
            markets = await self.get_markets()
            logger.info(f"Found {len(markets)} markets")

            # Calculate timestamp for 24 hours ago
            since = int((datetime.now() - timedelta(days=1)).timestamp() * 1000)
            
            results = []
            for symbol in markets:
                try:
                    funding_history = await self.get_funding_rate_history(
                        symbol=symbol,
                        since=since,
                        limit=100
                    )
                    
                    if funding_history:
                        results.append({
                            'symbol': symbol,
                            'timestamp': datetime.now().isoformat(),
                            'funding_history': [
                                {
                                    'timestamp': entry['timestamp'],
                                    'rate': entry['rate'],
                                    'datetime': entry['datetime']
                                }
                                for entry in funding_history
                            ]
                        })
                        logger.info(f"Successfully collected funding history for {symbol}")
                except Exception as e:
                    logger.error(f"Error processing {symbol}: {str(e)}")

            return results

        except Exception as e:
            logger.error(f"Error in collect_funding_data: {str(e)}")
            return []

async def main():
    # Create output directory if it doesn't exist
    output_dir = "data/funding_rates"
    os.makedirs(output_dir, exist_ok=True)

    try:
        print("\n🌟 Starting Hyperliquid Funding Rate Collection 🌟\n")
        
        async with HyperliquidFundingCollector() as collector:
            results = await collector.collect_funding_data()

            # Save results
            if results:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = os.path.join(output_dir, f'funding_history_{timestamp}.json')
                
                with open(output_file, 'w') as f:
                    json.dump(results, f, indent=2, default=str)
                
                logger.info(f"Data saved to {output_file}")
                print(f"\n✅ Data collection complete. Results saved to {output_file}")
                
                # Print summary
                print("\nFunding Rate Summary:")
                print("-" * 60)
                for result in results:
                    symbol = result['symbol']
                    history = result['funding_history']
                    if history:
                        latest_rate = history[0]['rate']
                        avg_rate = sum(h['rate'] for h in history) / len(history)
                        print(f"\n{symbol}:")
                        print(f"  Latest Rate: {latest_rate:.8%}")
                        print(f"  24h Average: {avg_rate:.8%}")
                        print(f"  Samples: {len(history)}")
            else:
                logger.error("No data was collected")
                
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
    finally:
        # Cleanup
        await asyncio.sleep(1)  # Allow time for any pending tasks to complete

if __name__ == "__main__":
    asyncio.run(main()) 