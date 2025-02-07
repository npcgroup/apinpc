import ccxt.async_support as ccxt
import aiohttp
import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional, Tuple
from decimal import Decimal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FundingRatePredictor:
    def __init__(self):
        self.binance = ccxt.binance({
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future',
            }
        })
        self.hl_api_url = "https://api.hyperliquid.xyz/info"
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.binance.close()

    async def get_hyperliquid_predicted_rates(self) -> Dict[str, Decimal]:
        """Fetch predicted funding rates from Hyperliquid"""
        async with aiohttp.ClientSession() as session:
            try:
                # Get predicted funding rates
                payload = {"type": "allPredictedFunding"}
                async with session.post(self.hl_api_url, json=payload) as response:
                    if response.status != 200:
                        logger.error(f"Hyperliquid API error: {response.status}")
                        return {}
                    
                    data = await response.json()
                    predicted_rates = {}
                    
                    for item in data:
                        if isinstance(item, dict):
                            coin = item.get('coin')
                            rate = item.get('predicted')
                            if coin and rate is not None:
                                try:
                                    predicted_rates[coin] = Decimal(str(rate))
                                except (ValueError, TypeError):
                                    continue
                    
                    return predicted_rates
                    
            except Exception as e:
                logger.error(f"Error fetching Hyperliquid predicted rates: {e}")
                return {}

    async def get_binance_predicted_rates(self) -> Dict[str, Decimal]:
        """Fetch predicted funding rates from Binance"""
        try:
            markets = await self.binance.load_markets()
            predicted_rates = {}
            
            # Fetch premium index (includes predicted rates)
            premium_index = await self.binance.fapiPublic_get_premiumindex()
            
            for item in premium_index:
                try:
                    symbol = item['symbol']
                    # Convert USDT pairs to match Hyperliquid format
                    base = symbol.replace('USDT', '')
                    predicted_rate = Decimal(str(item['predictedFundingRate']))
                    predicted_rates[base] = predicted_rate
                except (KeyError, ValueError, TypeError) as e:
                    logger.warning(f"Error processing Binance rate for {symbol}: {e}")
                    continue
                    
            return predicted_rates
            
        except Exception as e:
            logger.error(f"Error fetching Binance predicted rates: {e}")
            return {}

    async def get_funding_opportunities(self) -> Dict[str, Dict]:
        """Find funding rate arbitrage opportunities between exchanges"""
        try:
            # Fetch predicted rates from both exchanges
            hl_rates = await self.get_hyperliquid_predicted_rates()
            binance_rates = await self.get_binance_predicted_rates()
            
            opportunities = {}
            
            # Find common markets and calculate spreads
            for market in set(hl_rates.keys()) & set(binance_rates.keys()):
                hl_rate = hl_rates[market]
                binance_rate = binance_rates[market]
                spread = hl_rate - binance_rate
                
                opportunities[market] = {
                    'hyperliquid_predicted': float(hl_rate),
                    'binance_predicted': float(binance_rate),
                    'spread': float(spread),
                    'annualized_spread': float(spread * 365 * 100),  # Annualized percentage
                    'timestamp': datetime.utcnow().isoformat()
                }
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Error calculating funding opportunities: {e}")
            return {}

async def main():
    try:
        async with FundingRatePredictor() as predictor:
            # Get funding opportunities
            opportunities = await predictor.get_funding_opportunities()
            
            if opportunities:
                # Sort by absolute spread
                sorted_opps = sorted(
                    opportunities.items(),
                    key=lambda x: abs(x[1]['spread']),
                    reverse=True
                )
                
                print("\n🌟 Top Funding Rate Opportunities 🌟")
                print("=" * 80)
                print(f"{'Market':<10} {'HL Rate':>10} {'Binance Rate':>12} {'Spread':>10} {'Annual %':>10}")
                print("-" * 80)
                
                for market, data in sorted_opps[:10]:  # Show top 10
                    print(f"{market:<10} {data['hyperliquid_predicted']:>10.4%} "
                          f"{data['binance_predicted']:>12.4%} {data['spread']:>10.4%} "
                          f"{data['annualized_spread']:>10.1f}%")
                
                print("\n💡 Positive spread means Hyperliquid rate > Binance rate")
                print("   Consider long Binance / short Hyperliquid for positive spreads")
                print("   Consider long Hyperliquid / short Binance for negative spreads")
                
            else:
                print("No funding opportunities found")
                
    except Exception as e:
        logger.error(f"Error in main execution: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 