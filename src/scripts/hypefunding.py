import aiohttp
import asyncio
import json
from datetime import datetime, timedelta
import pandas as pd
import logging
import os
from tqdm import tqdm
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HyperliquidFundingCollector:
    def __init__(self):
        self.base_url = 'https://api.hyperliquid.xyz'
        self.session = None
        
    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def make_request(self, endpoint: str, payload: Dict) -> Dict:
        """Make API request with better error handling"""
        try:
            url = f"{self.base_url}/{endpoint}"
            async with self.session.post(
                url,
                json=payload,
                headers={'Content-Type': 'application/json'}
            ) as response:
                if response.status != 200:
                    raise Exception(f"API request failed with status {response.status}")
                return await response.json()
        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            raise

    async def get_market_state(self, token: str) -> Dict:
        """Get current market state with accurate mark price"""
        try:
            # Use the correct endpoint for market info
            response = await self.make_request("info", {
                "type": "metaAndAssetCtxs"
            })
            
            if isinstance(response, list) and len(response) > 1:
                # Find the market data for the specific token
                for market in response[1]:
                    if market.get('name') == token:
                        return market
            
            raise Exception(f"Market data not found for {token}")
        except Exception as e:
            logger.error(f"Failed to get market state for {token}: {str(e)}")
            raise

    async def get_funding_data(self, token: str) -> Optional[Dict]:
        """Get accurate funding data for a token"""
        try:
            # Get market state for accurate mark price and funding
            market_state = await self.get_market_state(token)
            
            # Get current funding rate from exchange info
            funding_info = await self.make_request("exchange", {
                "type": "fundingInfo",
                "coin": token
            })

            # Get trades for volume calculation
            trades = await self.make_request("exchange", {
                "type": "trades",
                "coin": token,
                "startTime": int((datetime.now() - timedelta(days=1)).timestamp() * 1000)
            })

            # Extract and validate data
            mark_price = float(market_state.get('markPx', 0))
            current_funding = float(market_state.get('funding', 0))
            open_interest = float(market_state.get('openInterest', 0))
            
            # Calculate 24h volume
            volume_24h = sum(
                float(trade['sz']) * float(trade['px'])
                for trade in trades
                if isinstance(trade, dict) and 'sz' in trade and 'px' in trade
            )

            # Validate the data
            if mark_price <= 0:
                logger.warning(f"Invalid mark price for {token}: {mark_price}")
                return None

            return {
                'token': token,
                'current_funding_rate': current_funding,
                'mark_price': mark_price,
                'open_interest': open_interest,
                'notional_open_interest': open_interest * mark_price,
                'volume_24h': volume_24h,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error fetching data for {token}: {str(e)}")
            return None

    async def get_all_markets(self) -> List[str]:
        """Get list of all available markets"""
        try:
            response = await self.make_request("info", {
                "type": "metaAndAssetCtxs"
            })
            
            if isinstance(response, list) and len(response) > 0:
                universe = response[0].get('universe', [])
                return [
                    market['name'] 
                    for market in universe 
                    if market.get('name') and market.get('isActive', True)
                ]
            return []
        except Exception as e:
            logger.error(f"Failed to fetch markets: {str(e)}")
            return []

    async def get_predicted_funding_rates(self) -> Dict[str, float]:
        """Get accurate predicted funding rates"""
        try:
            response = await self.make_request("exchange", {
                "type": "allPredictedFunding"
            })
            
            rates = {}
            for item in response:
                if isinstance(item, dict):
                    token = item.get('coin')
                    rate = item.get('predicted')
                    if token and rate is not None:
                        try:
                            rates[token] = float(rate)
                        except (ValueError, TypeError):
                            continue
            return rates
        except Exception as e:
            logger.error(f"Failed to fetch predicted rates: {str(e)}")
            return {}

async def main():
    output_dir = "data/funding_rates"
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        async with HyperliquidFundingCollector() as collector:
            # Get all markets
            markets = await collector.get_all_markets()
            if not markets:
                raise Exception("No markets found")
            
            logger.info(f"Found {len(markets)} markets")
            
            # Get predicted funding rates
            predicted_rates = await collector.get_predicted_funding_rates()
            logger.info(f"Fetched predicted rates for {len(predicted_rates)} markets")
            
            # Collect market data
            results = []
            with tqdm(total=len(markets), desc="Collecting market data") as pbar:
                for token in markets:
                    try:
                        data = await collector.get_funding_data(token)
                        if data:
                            data['predicted_funding_rate'] = predicted_rates.get(token, 0)
                            results.append(data)
                            logger.debug(f"Successfully processed {token}")
                    except Exception as e:
                        logger.error(f"Error processing {token}: {str(e)}")
                    finally:
                        pbar.update(1)

            # Save results
            if not results:
                logger.error("No valid results collected")
                return []
                
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"{output_dir}/funding_raw_{timestamp}.json"
            
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            logger.info(f"Saved {len(results)} market results to {output_file}")
            return results

    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        return []

if __name__ == "__main__":
    results = asyncio.run(main())
    if results:
        print(f"Successfully collected data for {len(results)} markets")
    else:
        print("No data collected")