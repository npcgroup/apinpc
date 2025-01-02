import aiohttp
import asyncio
import json
from datetime import datetime, timedelta
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HyperliquidFundingCollector:
    def __init__(self):
        self.base_url = 'https://api.hyperliquid.xyz/info'
        
    async def get_all_markets(self):
        """Fetch all available markets from Hyperliquid"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.base_url,
                json={"type": "metaAndAssetCtxs"},
                headers={'Content-Type': 'application/json'}
            ) as response:
                if response.status != 200:
                    raise Exception(f"Failed to fetch markets: {response.status}")
                data = await response.json()
                if isinstance(data, list) and len(data) > 0:
                    universe = data[0].get('universe', [])
                    return [market['name'] for market in universe]
                return []

    async def get_predicted_funding_rates(self):
        """Fetch predicted funding rates for all venues"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.base_url,
                json={"type": "predictedFundings"},
                headers={'Content-Type': 'application/json'}
            ) as response:
                if response.status != 200:
                    return {}
                data = await response.json()
                predicted_rates = {}
                for item in data:
                    if isinstance(item, list) and len(item) > 1:
                        coin = item[0]
                        venues = item[1]
                        for venue in venues:
                            if venue[0] == "HlPerp":
                                predicted_rates[coin] = venue[1].get("fundingRate", 0)
                return predicted_rates

    async def get_funding_data(self, token: str):
        """Fetch current, predicted, and historical funding rates for a token"""
        async with aiohttp.ClientSession() as session:
            # Get current market data
            current_payload = {
                "type": "metaAndAssetCtxs"
            }
            
            # Get historical funding rates (last 24h)
            yesterday = int((datetime.now() - timedelta(days=1)).timestamp() * 1000)
            historical_payload = {
                "type": "fundingHistory",
                "coin": token,
                "startTime": yesterday
            }
            
            # Make parallel requests
            current_response = await session.post(
                self.base_url,
                json=current_payload,
                headers={'Content-Type': 'application/json'}
            )
            historical_response = await session.post(
                self.base_url,
                json=historical_payload,
                headers={'Content-Type': 'application/json'}
            )
            
            if current_response.status != 200 or historical_response.status != 200:
                logger.error(f"Failed to fetch data for {token}")
                return None
            
            current_data = await current_response.json()
            historical_data = await historical_response.json()
            
            # Extract current market data
            if isinstance(current_data, list) and len(current_data) > 1:
                market_info = None
                asset_contexts = current_data[1]
                for context in asset_contexts:
                    if isinstance(context, dict) and 'funding' in context:
                        market_info = context
                        break
                
                if market_info:
                    current_funding = float(market_info.get('funding', 0))
                    
                    # Process historical rates
                    historical_rates = []
                    for entry in historical_data:
                        if isinstance(entry, dict):
                            historical_rates.append({
                                'timestamp': datetime.fromtimestamp(entry.get('time', 0) / 1000),
                                'rate': float(entry.get('fundingRate', 0))
                            })
                    
                    return {
                        'token': token,
                        'current_funding_rate': current_funding,
                        'mark_price': float(market_info.get('markPx', 0)),
                        'open_interest': float(market_info.get('openInterest', 0)),
                        'volume_24h': float(market_info.get('dayNtlVlm', 0)),
                        'historical_rates': historical_rates
                    }
            
            return None

async def main():
    collector = HyperliquidFundingCollector()
    
    try:
        # Get all markets
        markets = await collector.get_all_markets()
        logger.info(f"Found {len(markets)} markets")
        
        # Get predicted funding rates
        predicted_rates = await collector.get_predicted_funding_rates()
        
        # Fetch funding data for all markets
        results = []
        for token in markets:
            try:
                data = await collector.get_funding_data(token)
                if data:
                    # Add predicted funding rate if available
                    data['predicted_funding_rate'] = predicted_rates.get(token, 0)
                    results.append(data)
                    logger.info(f"Processed {token}")
            except Exception as e:
                logger.error(f"Error processing {token}: {str(e)}")
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save raw data
        with open(f'funding_data_{timestamp}.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        # Create a summary DataFrame
        if results:
            summary = pd.DataFrame([{
                'token': r['token'],
                'current_funding_rate': r['current_funding_rate'],
                'predicted_funding_rate': r['predicted_funding_rate'],
                'mark_price': r['mark_price'],
                'open_interest': r['open_interest'],
                'volume_24h': r['volume_24h'],
                'avg_24h_funding_rate': sum(h['rate'] for h in r['historical_rates']) / len(r['historical_rates']) if r['historical_rates'] else None
            } for r in results])
            
            # Save summary to CSV
            summary.to_csv(f'funding_summary_{timestamp}.csv', index=False)
            
            # Print top 5 highest current funding rates
            print("\nTop 5 Highest Current Funding Rates:")
            print(summary.nlargest(5, 'current_funding_rate')[['token', 'current_funding_rate', 'predicted_funding_rate']])
            
            # Print markets with significant funding rate differences
            print("\nMarkets with Notable Funding Rate Opportunities:")
            summary['funding_difference'] = summary['predicted_funding_rate'] - summary['current_funding_rate']
            print(summary.nlargest(5, 'funding_difference')[['token', 'current_funding_rate', 'predicted_funding_rate', 'funding_difference']])
            
        else:
            logger.error("No results were collected")
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())