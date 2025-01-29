import asyncio
import aiohttp
import pandas as pd
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict
import logging
from supabase import create_client
import os
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedFundingCrawler:
    """Enhanced crawler for funding rate opportunities with predictions"""
    
    def __init__(self):
        load_dotenv()
        self.supabase = create_client(
            os.getenv("NEXT_PUBLIC_SUPABASE_URL"),
            os.getenv("NEXT_PUBLIC_SUPABASE_KEY")
        )
        self.hl_api_url = "https://api.hyperliquid.xyz/info"
        self.binance_api_url = "https://fapi.binance.com/fapi/v1"
        
    async def fetch_hyperliquid_data(self) -> Dict:
        """Fetch current and predicted funding rates from HyperLiquid"""
        async with aiohttp.ClientSession() as session:
            try:
                # First get meta data
                meta_payload = {"type": "metaAndAssetCtxs"}
                async with session.post(self.hl_api_url, json=meta_payload) as meta_response:
                    meta_data = await meta_response.json()

                # Then get funding data
                funding_payload = {"type": "allMids"}
                async with session.post(self.hl_api_url, json=funding_payload) as funding_response:
                    funding_data = await funding_response.json()

                # Get predicted funding rates
                predicted_payload = {"type": "predictedFunding"}
                async with session.post(self.hl_api_url, json=predicted_payload) as predicted_response:
                    predicted_data = await predicted_response.json()

                return self._process_hyperliquid_data(meta_data, funding_data, predicted_data)
            except Exception as e:
                logger.error(f"Error fetching HyperLiquid data: {e}")
                return {}

    async def fetch_binance_data(self) -> Dict:
        """Fetch current and predicted funding rates from Binance"""
        async with aiohttp.ClientSession() as session:
            try:
                # Get current funding rate
                async with session.get(f"{self.binance_api_url}/fundingRate") as funding_response:
                    funding_data = await funding_response.json()

                # Get mark price and funding rate
                async with session.get(f"{self.binance_api_url}/premiumIndex") as premium_response:
                    premium_data = await premium_response.json()

                # Get 24h market data
                async with session.get(f"{self.binance_api_url}/ticker/24hr") as market_response:
                    market_data = await market_response.json()

                return self._process_binance_data(funding_data, premium_data, market_data)
            except Exception as e:
                logger.error(f"Error fetching Binance data: {e}")
                return {}

    def _process_hyperliquid_data(self, meta_data: Dict, funding_data: List, predicted_data: List) -> Dict:
        """Process HyperLiquid funding rate data"""
        processed = {}
        try:
            # Process meta data for market info
            market_info = {}
            for asset in meta_data.get("universe", []):
                symbol = asset.get("name")
                if symbol:
                    market_info[symbol] = {
                        "open_interest": float(asset.get("openInterest", 0)),
                        "volume_24h": float(asset.get("volume24h", 0))
                    }

            # Process current and predicted funding rates
            for coin, rate in funding_data.items():
                if coin in market_info:
                    current_rate = float(rate) if rate else 0
                    predicted_rate = 0
                    
                    # Find predicted rate
                    for pred in predicted_data:
                        if pred[0] == coin:
                            predicted_rate = float(pred[1].get("predicted", 0))
                            break

                    processed[coin] = {
                        'current_rate': current_rate,
                        'predicted_rate': predicted_rate,
                        'open_interest': market_info[coin]["open_interest"],
                        'volume_24h': market_info[coin]["volume_24h"],
                        'next_funding_time': datetime.now() + timedelta(hours=1)
                    }

            return processed
        except Exception as e:
            logger.error(f"Error processing HyperLiquid data: {e}")
            return {}

    def _process_binance_data(self, funding_data: List, premium_data: List, market_data: List) -> Dict:
        """Process Binance funding rate data"""
        processed = {}
        try:
            # Create market data lookup
            market_lookup = {
                item['symbol']: {
                    'volume': float(item['volume']),
                    'quoteVolume': float(item['quoteVolume'])
                }
                for item in market_data
            }

            # Process funding and premium data
            for item in funding_data:
                symbol = item['symbol'].replace('USDT', '')
                
                # Find corresponding premium data
                premium_info = next(
                    (p for p in premium_data if p['symbol'] == item['symbol']),
                    {}
                )
                
                # Get market data
                market_info = market_lookup.get(item['symbol'], {})
                
                processed[symbol] = {
                    'current_rate': float(item['fundingRate']),
                    'predicted_rate': float(premium_info.get('lastFundingRate', 0)),  # Use last funding as prediction
                    'open_interest': float(premium_info.get('openInterest', 0)),
                    'volume_24h': market_info.get('quoteVolume', 0),
                    'next_funding_time': datetime.fromtimestamp(item['fundingTime'] / 1000)
                }

            return processed
        except Exception as e:
            logger.error(f"Error processing Binance data: {e}")
            return {}

    async def get_historical_metrics(self, coin: str) -> Dict:
        """Get historical metrics from Supabase"""
        try:
            response = self.supabase.table('funding_arbitrage_opportunities')\
                .select('*')\
                .eq('coin', coin)\
                .order('timestamp.desc')\
                .limit(100)\
                .execute()
            
            if not response.data:
                return {'avg_spread': 0, 'volatility': 0, 'success_rate': 0}
            
            df = pd.DataFrame(response.data)
            return {
                'avg_spread': df['spread'].mean(),
                'volatility': df['spread'].std(),
                'success_rate': (df['spread'] > 0).mean()
            }
        except Exception as e:
            logger.error(f"Error fetching historical metrics: {e}")
            return {'avg_spread': 0, 'volatility': 0, 'success_rate': 0}

    def calculate_opportunity_score(self, 
                                 current_spread: float,
                                 predicted_spread: float,
                                 historical_metrics: Dict,
                                 volume: float,
                                 open_interest: float) -> float:
        """Calculate comprehensive opportunity score"""
        weights = {
            'current_spread': 0.3,
            'predicted_spread': 0.2,
            'historical_success': 0.15,
            'volatility': 0.15,
            'liquidity': 0.2
        }
        
        # Normalize metrics
        normalized_volume = min(volume / 1e8, 1)
        normalized_oi = min(open_interest / 1e8, 1)
        liquidity_score = (normalized_volume + normalized_oi) / 2
        
        return (
            abs(current_spread) * weights['current_spread'] +
            abs(predicted_spread) * weights['predicted_spread'] +
            historical_metrics['success_rate'] * weights['historical_success'] +
            (1 / (1 + historical_metrics['volatility'])) * weights['volatility'] +
            liquidity_score * weights['liquidity']
        )

    async def analyze_opportunities(self) -> pd.DataFrame:
        """Analyze and score funding rate opportunities"""
        hl_data = await self.fetch_hyperliquid_data()
        binance_data = await self.fetch_binance_data()
        
        opportunities = []
        for coin in set(hl_data.keys()) & set(binance_data.keys()):
            try:
                hl = hl_data[coin]
                binance = binance_data[coin]
                
                # Calculate spreads
                current_spread = hl['current_rate'] - binance['current_rate']
                predicted_spread = hl['predicted_rate'] - binance['predicted_rate']
                
                # Get historical metrics
                historical = await self.get_historical_metrics(coin)
                
                # Calculate metrics
                avg_volume = (hl['volume_24h'] + binance['volume_24h']) / 2
                min_oi = min(hl['open_interest'], binance['open_interest'])
                
                # Calculate opportunity score
                score = self.calculate_opportunity_score(
                    current_spread,
                    predicted_spread,
                    historical,
                    avg_volume,
                    min_oi
                )
                
                # Determine position type
                position_type = "Long HL" if current_spread > 0 else "Short HL"
                
                opportunities.append({
                    'coin': coin,
                    'strategy': f"{position_type} - {'Short' if position_type == 'Long HL' else 'Long'} Binance",
                    'hyperliquid_rate': hl['current_rate'] * 100,
                    'counterparty': 'Binance',
                    'counterparty_rate': binance['current_rate'] * 100,
                    'spread': current_spread * 100,
                    'predicted_spread': predicted_spread * 100,
                    'annualized_yield': current_spread * 100 * 365,
                    'position_type': position_type,
                    'market_size': min_oi,
                    'volume_24h': avg_volume,
                    'next_funding_time': min(hl['next_funding_time'], binance['next_funding_time']),
                    'priority_score': score,
                    'timestamp': datetime.now()
                })
                
            except Exception as e:
                logger.error(f"Error processing {coin}: {e}")
                continue
        
        return pd.DataFrame(opportunities)

    async def store_opportunities(self, opportunities: pd.DataFrame):
        """Store opportunities in Supabase"""
        if opportunities.empty:
            logger.info("No opportunities to store")
            return
        
        try:
            # Convert DataFrame to list of dictionaries
            records = opportunities.to_dict('records')
            
            # Store in Supabase
            response = self.supabase.table('funding_arbitrage_opportunities')\
                .upsert(records)\
                .execute()
            
            logger.info(f"Stored {len(records)} opportunities in Supabase")
            
        except Exception as e:
            logger.error(f"Error storing opportunities: {e}")

    async def run(self):
        """Main loop to continuously update opportunities"""
        logger.info("Starting Enhanced Funding Crawler...")
        
        while True:
            try:
                # Analyze opportunities
                opportunities = await self.analyze_opportunities()
                
                # Log top opportunities
                if not opportunities.empty:
                    top_opps = opportunities.nlargest(5, 'priority_score')
                    logger.info("\nTop 5 Funding Arbitrage Opportunities:")
                    for _, opp in top_opps.iterrows():
                        logger.info(
                            f"{opp['coin']} ({opp['strategy']}): "
                            f"Current Spread: {opp['spread']:.4f}% | "
                            f"Predicted Spread: {opp['predicted_spread']:.4f}% | "
                            f"Score: {opp['priority_score']:.4f}"
                        )
                
                # Store in Supabase
                await self.store_opportunities(opportunities)
                
                # Wait before next update
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(30)

def main():
    crawler = EnhancedFundingCrawler()
    asyncio.run(crawler.run())

if __name__ == "__main__":
    main() 