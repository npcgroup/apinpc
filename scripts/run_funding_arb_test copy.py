import asyncio
import logging
from decimal import Decimal
from datetime import datetime, timedelta
import os
import pandas as pd
import aiohttp
from dotenv import load_dotenv
from typing import Dict, List

from scripts.v2_funding_rate_arb import FundingRateArbitrage, FundingRateArbitrageConfig
from hummingbot.core.data_type.common import TradeType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FundingRateAnalyzer:
    def __init__(self, supabase_client):
        self.supabase = supabase_client
        self.hl_api_url = "https://api.hyperliquid.xyz/info"
        self.binance_api_url = "https://fapi.binance.com/fapi/v1"

    async def fetch_hyperliquid_funding(self) -> Dict:
        """Fetch current and predicted funding rates from HyperLiquid"""
        async with aiohttp.ClientSession() as session:
            try:
                payload = {"type": "fundingHistory"}
                async with session.post(self.hl_api_url, json=payload) as response:
                    data = await response.json()
                    return self._process_hyperliquid_data(data)
            except Exception as e:
                logger.error(f"Error fetching HyperLiquid funding: {e}")
                return {}

    async def fetch_binance_funding(self) -> Dict:
        """Fetch current and predicted funding rates from Binance"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{self.binance_api_url}/premiumIndex") as response:
                    data = await response.json()
                    return self._process_binance_data(data)
            except Exception as e:
                logger.error(f"Error fetching Binance funding: {e}")
                return {}

    def _process_hyperliquid_data(self, data: List) -> Dict:
        """Process HyperLiquid funding rate data"""
        processed = {}
        for item in data:
            if isinstance(item, list) and len(item) >= 2:
                coin = item[0]
                rate = float(item[1].get('currentFunding', 0))
                predicted = float(item[1].get('predictedFunding', 0))
                processed[coin] = {
                    'current_rate': rate,
                    'predicted_rate': predicted,
                    'next_funding_time': datetime.now() + timedelta(hours=1)
                }
        return processed

    def _process_binance_data(self, data: List) -> Dict:
        """Process Binance funding rate data"""
        processed = {}
        for item in data:
            symbol = item['symbol'].replace('USDT', '')
            processed[symbol] = {
                'current_rate': float(item['lastFundingRate']),
                'predicted_rate': float(item['predictedFundingRate']),
                'next_funding_time': datetime.fromtimestamp(item['nextFundingTime'] / 1000)
            }
        return processed

    async def analyze_opportunities(self, hl_data: Dict, binance_data: Dict) -> pd.DataFrame:
        """Analyze arbitrage opportunities between exchanges"""
        opportunities = []
        
        for coin in set(hl_data.keys()) & set(binance_data.keys()):
            hl = hl_data[coin]
            binance = binance_data[coin]
            
            # Calculate spreads
            current_spread = hl['current_rate'] - binance['current_rate']
            predicted_spread = hl['predicted_rate'] - binance['predicted_rate']
            
            # Get historical data from Supabase
            historical = await self.get_historical_data(coin)
            
            # Calculate opportunity score
            score = self.calculate_opportunity_score(
                current_spread,
                predicted_spread,
                historical.get('avg_spread', 0),
                historical.get('success_rate', 0)
            )
            
            opportunities.append({
                'coin': coin,
                'hl_current_rate': hl['current_rate'],
                'hl_predicted_rate': hl['predicted_rate'],
                'binance_current_rate': binance['current_rate'],
                'binance_predicted_rate': binance['predicted_rate'],
                'current_spread': current_spread,
                'predicted_spread': predicted_spread,
                'opportunity_score': score,
                'next_funding_time': min(hl['next_funding_time'], binance['next_funding_time']),
                'timestamp': datetime.now()
            })
        
        return pd.DataFrame(opportunities)

    async def get_historical_data(self, coin: str) -> Dict:
        """Fetch historical arbitrage data from Supabase"""
        try:
            response = self.supabase.table('funding_arbitrage_opportunities')\
                .select('*')\
                .eq('coin', coin)\
                .order('timestamp.desc')\
                .limit(100)\
                .execute()
            
            if not response.data:
                return {'avg_spread': 0, 'success_rate': 0}
            
            df = pd.DataFrame(response.data)
            return {
                'avg_spread': df['spread'].mean(),
                'success_rate': (df['spread'] > 0).mean()
            }
        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")
            return {'avg_spread': 0, 'success_rate': 0}

    def calculate_opportunity_score(self, current_spread: float, predicted_spread: float, 
                                 historical_avg: float, success_rate: float) -> float:
        """Calculate opportunity score based on multiple factors"""
        spread_weight = 0.4
        prediction_weight = 0.3
        historical_weight = 0.2
        success_weight = 0.1
        
        return (abs(current_spread) * spread_weight +
                abs(predicted_spread) * prediction_weight +
                abs(historical_avg) * historical_weight +
                success_rate * success_weight)

async def test_strategy():
    """Test the funding rate arbitrage strategy with real data"""
    try:
        # Load environment variables
        load_dotenv()
        
        # Initialize Supabase client
        from supabase import create_client
        supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY")
        )
        
        # Initialize analyzer
        analyzer = FundingRateAnalyzer(supabase)
        
        # Fetch current funding rates
        hl_data = await analyzer.fetch_hyperliquid_funding()
        binance_data = await analyzer.fetch_binance_funding()
        
        # Analyze opportunities
        opportunities = await analyzer.analyze_opportunities(hl_data, binance_data)
        
        # Store results in Supabase
        if not opportunities.empty:
            records = opportunities.to_dict('records')
            supabase.table('funding_arbitrage_opportunities').upsert(records).execute()
            
            # Log top opportunities
            top_opps = opportunities.nlargest(5, 'opportunity_score')
            logger.info("\nTop 5 Arbitrage Opportunities:")
            logger.info(top_opps.to_string())
        
        # Initialize and run strategy with top opportunities
        config = FundingRateArbitrageConfig(
            supabase_url=os.getenv("SUPABASE_URL"),
            supabase_key=os.getenv("SUPABASE_KEY"),
            leverage=20,
            min_funding_rate_profitability=Decimal("0.001"),
            position_size_quote=Decimal("100"),
            tokens=set(opportunities.nlargest(3, 'opportunity_score')['coin'])
        )
        
        strategy = FundingRateArbitrage(config=config)
        
        # Test market initialization
        logger.info("\nTesting market initialization...")
        strategy.initialize_markets()
        
        # Execute top opportunities
        for _, opp in top_opps.iterrows():
            combo = strategy.get_most_profitable_combination(opp['coin'])
            if combo:
                logger.info(f"\nExecuting arbitrage for {opp['coin']}:")
                logger.info(f"Current Spread: {opp['current_spread']:.6f}")
                logger.info(f"Predicted Spread: {opp['predicted_spread']:.6f}")
                logger.info(f"Opportunity Score: {opp['opportunity_score']:.4f}")
                
                await strategy.execute_arbitrage(opp['coin'], combo)
        
        # Display active arbitrages
        logger.info("\nActive Arbitrages:")
        logger.info(strategy.format_status())
        
    except Exception as e:
        logger.error(f"Error running strategy test: {e}")
        raise

def main():
    """Run the strategy test"""
    asyncio.run(test_strategy())

if __name__ == "__main__":
    main() 