import asyncio
import aiohttp
import pandas as pd
from datetime import datetime
from decimal import Decimal
from typing import List, Dict
import logging
from supabase import create_client
import os
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HyperliquidFundingCrawler:
    """Crawler for HyperLiquid funding rate opportunities"""
    
    def __init__(self):
        load_dotenv()
        self.supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY")
        )
        self.base_url = "https://api.hyperliquid.xyz/info"

    async def fetch_funding_data(self) -> Dict:
        """Fetch current funding rates from HyperLiquid API"""
        async with aiohttp.ClientSession() as session:
            try:
                # Fetch predicted fundings for more accurate rates
                funding_response = await session.post(
                    self.base_url,
                    json={"type": "predictedFundings"}
                )
                
                if funding_response.status != 200:
                    raise Exception(f"Failed to fetch data from HyperLiquid API: Status {funding_response.status}")
                
                funding_data = await funding_response.json()
                
                if not funding_data:
                    logger.warning("Empty response from HyperLiquid API")
                    return {}
                
                logger.info(f"Successfully fetched funding data for {len(funding_data)} markets")
                return funding_data
                
            except aiohttp.ClientError as e:
                logger.error(f"Network error fetching funding data: {e}")
                return {}
            except Exception as e:
                logger.error(f"Error fetching funding data: {e}")
                return {}

    def process_funding_opportunities(self, data: List) -> pd.DataFrame:
        """Process raw funding data and identify arbitrage opportunities"""
        try:
            markets = []
            
            for coin_data in data:
                if not isinstance(coin_data, list) or len(coin_data) < 2:
                    continue
                
                coin = coin_data[0]
                venues = coin_data[1]
                
                hl_rate = None
                binance_rate = None
                bybit_rate = None
                
                # Extract rates for each venue
                for venue in venues:
                    try:
                        venue_name = venue[0] if isinstance(venue, list) and len(venue) > 0 else None
                        venue_data = venue[1] if isinstance(venue, list) and len(venue) > 1 else {}
                        
                        if venue_name == "HlPerp" and isinstance(venue_data, dict):
                            hl_rate = float(venue_data.get("fundingRate", 0))
                        elif venue_name == "BinancePerp" and isinstance(venue_data, dict):
                            binance_rate = float(venue_data.get("fundingRate", 0))
                        elif venue_name == "BybitPerp" and isinstance(venue_data, dict):
                            bybit_rate = float(venue_data.get("fundingRate", 0))
                    except (IndexError, TypeError, ValueError) as e:
                        logger.warning(f"Error processing venue data for {coin}: {e}")
                        continue
                
                # Calculate all possible arbitrage opportunities
                if hl_rate is not None:
                    # Binance opportunities
                    if binance_rate is not None:
                        spread = hl_rate - binance_rate
                        
                        # Long HL, Short Binance
                        markets.append({
                            "coin": coin,
                            "strategy": "Long HL - Short Binance",
                            "hyperliquid_rate": hl_rate * 100,
                            "counterparty": "Binance",
                            "counterparty_rate": binance_rate * 100,
                            "spread": spread * 100,
                            "timestamp": datetime.now().isoformat(),
                            "annualized_yield": spread * 100 * 365,
                            "position": "Long HL"
                        })
                        
                        # Short HL, Long Binance
                        markets.append({
                            "coin": coin,
                            "strategy": "Short HL - Long Binance",
                            "hyperliquid_rate": hl_rate * 100,
                            "counterparty": "Binance",
                            "counterparty_rate": binance_rate * 100,
                            "spread": -spread * 100,  # Reverse the spread for opposite position
                            "timestamp": datetime.now().isoformat(),
                            "annualized_yield": -spread * 100 * 365,
                            "position": "Short HL"
                        })
                    
                    # Bybit opportunities
                    if bybit_rate is not None:
                        spread = hl_rate - bybit_rate
                        
                        # Long HL, Short Bybit
                        markets.append({
                            "coin": coin,
                            "strategy": "Long HL - Short Bybit",
                            "hyperliquid_rate": hl_rate * 100,
                            "counterparty": "Bybit",
                            "counterparty_rate": bybit_rate * 100,
                            "spread": spread * 100,
                            "timestamp": datetime.now().isoformat(),
                            "annualized_yield": spread * 100 * 365,
                            "position": "Long HL"
                        })
                        
                        # Short HL, Long Bybit
                        markets.append({
                            "coin": coin,
                            "strategy": "Short HL - Long Bybit",
                            "hyperliquid_rate": hl_rate * 100,
                            "counterparty": "Bybit",
                            "counterparty_rate": bybit_rate * 100,
                            "spread": -spread * 100,  # Reverse the spread for opposite position
                            "timestamp": datetime.now().isoformat(),
                            "annualized_yield": -spread * 100 * 365,
                            "position": "Short HL"
                        })
            
            # Convert to DataFrame and process opportunities
            df = pd.DataFrame(markets)
            if not df.empty:
                df["abs_spread"] = df["spread"].abs()
                
                # Get top 10 opportunities for each strategy type
                top_opportunities = pd.DataFrame()
                
                # Long HL positions
                long_hl = df[df["position"] == "Long HL"].nlargest(10, "abs_spread")
                if not long_hl.empty:
                    top_opportunities = pd.concat([top_opportunities, long_hl])
                
                # Short HL positions
                short_hl = df[df["position"] == "Short HL"].nlargest(10, "abs_spread")
                if not short_hl.empty:
                    top_opportunities = pd.concat([top_opportunities, short_hl])
                
                top_opportunities = top_opportunities.drop("abs_spread", axis=1)
                
                # Log the opportunities
                logger.info("\nTop Funding Rate Arbitrage Opportunities:")
                logger.info("\nLong HyperLiquid Positions:")
                for _, row in long_hl.iterrows():
                    logger.info(
                        f"{row['coin']} ({row['strategy']}): "
                        f"HL Rate: {row['hyperliquid_rate']:.4f}% vs "
                        f"{row['counterparty']} Rate: {row['counterparty_rate']:.4f}% | "
                        f"Spread: {row['spread']:.4f}% | "
                        f"Annualized: {row['annualized_yield']:.2f}%"
                    )
                
                logger.info("\nShort HyperLiquid Positions:")
                for _, row in short_hl.iterrows():
                    logger.info(
                        f"{row['coin']} ({row['strategy']}): "
                        f"HL Rate: {row['hyperliquid_rate']:.4f}% vs "
                        f"{row['counterparty']} Rate: {row['counterparty_rate']:.4f}% | "
                        f"Spread: {row['spread']:.4f}% | "
                        f"Annualized: {row['annualized_yield']:.2f}%"
                    )
                
                return top_opportunities
            
            logger.info("No valid funding opportunities found")
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Error processing funding opportunities: {e}")
            logger.error(f"Raw data: {data}")
            return pd.DataFrame()

    async def store_opportunities(self, opportunities: pd.DataFrame):
        """Store arbitrage opportunities in Supabase"""
        if opportunities.empty:
            logger.info("No opportunities to store")
            return
            
        try:
            # Convert DataFrame to list of dictionaries
            records = opportunities.to_dict("records")
            
            # Insert into Supabase
            response = self.supabase.table("funding_arbitrage_opportunities").upsert(
                records,
                on_conflict="coin,counterparty"  # Update on conflict
            ).execute()
            
            logger.info(f"Successfully stored {len(records)} opportunities")
            
        except Exception as e:
            logger.error(f"Error storing opportunities: {e}")

    async def run(self):
        """Main execution loop"""
        while True:
            try:
                # Fetch and process data
                raw_data = await self.fetch_funding_data()
                if raw_data:
                    opportunities = self.process_funding_opportunities(raw_data)
                    await self.store_opportunities(opportunities)
                
                # Wait before next update (30 seconds)
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(30)

def main():
    crawler = HyperliquidFundingCrawler()
    asyncio.run(crawler.run())

if __name__ == "__main__":
    main() 