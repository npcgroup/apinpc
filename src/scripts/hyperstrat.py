import os
import aiohttp
import asyncio
import pandas as pd
from datetime import datetime
import logging
from rich.console import Console
from rich.table import Table
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
console = Console()

class PerpDataCollector:
    def __init__(self):
        self.hl_base_url = "https://api.hyperliquid.xyz/info"
        self.dexscreener_base_url = "https://api.dexscreener.com/latest/dex/tokens"
        self.solscan_base_url = "https://public-api.solscan.io/token/holders"
        self.tokens = ["POPCAT", "WIF", "GOAT", "PNUT", "CHILLGUY", "MOODENG", "MEW", "BRETT"]
        
        # Using correct token addresses from ingest_perp_data.py
        self.token_addresses = {
            "POPCAT": "7GCihgDB8fe6KNjn2MYtkzZcRjQy3t9GHdC8uHYmW2hr", 
            "WIF": "EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm",
            "GOAT": "CzLSujWBLFsSjncfkh59rUFqvafWcY5tzedWJSuypump",
            "PNUT": "2qEHjDLDLbuBgRYvsxhc5D6uDWAivNFZGan56P1tpump",
            "CHILLGUY": "Df6yfrKC8kZE3KNkrHERKzAetSxbrWeniQfyJY4Jpump",
            "MOODENG": "ED5nyyWEzpPPiWimP8vYm7sD7TD3LAt3Q3gRTWHzPJBY",
            "MEW": "MEW1gQWJ3nEXg2qgERiKu7FAFj79PHvQVREQUzScPP5",
            "BRETT": "BRETTqYJxZ3qZzFrcJLtQwEqNRGZjxj7PvzjzwJhGXL"
        }

    async def get_hl_market_data(self, session: aiohttp.ClientSession, token: str):
        """Fetch Hyperliquid market data"""
        try:
            # Update the request payload format
            markets_payload = {
                "type": "meta",
                "coin": token
            }
            
            funding_payload = {
                "type": "fundingHistory",
                "coin": token
            }
            
            # Get market data
            async with session.post(
                self.hl_base_url,
                json=markets_payload,
                headers={'Content-Type': 'application/json'}
            ) as response:
                if response.status != 200:
                    logger.error(f"Market data request failed for {token}: {response.status}")
                    return None
                markets_data = await response.json()
                
            # Get funding rates
            async with session.post(
                self.hl_base_url,
                json=funding_payload,
                headers={'Content-Type': 'application/json'}
            ) as response:
                if response.status != 200:
                    logger.error(f"Funding data request failed for {token}: {response.status}")
                    return None
                funding_data = await response.json()
                
            # Extract market data
            if markets_data and isinstance(markets_data, dict):
                market = markets_data.get('assetInfo', {}).get(token, {})
                funding = funding_data[0] if funding_data else {}
                
                return {
                    'funding_rate': float(funding.get('funding', 0)),
                    'volume_24h': float(market.get('dayNtlVlm', 0)),
                    'open_interest': float(market.get('openInterest', 0)),
                    'mark_price': float(market.get('markPx', 0))
                }
            
            logger.warning(f"No market data found for {token}")
            return None
                
        except Exception as e:
            logger.error(f"Error fetching Hyperliquid data for {token}: {str(e)}")
            return None

    async def get_dexscreener_data(self, session: aiohttp.ClientSession, token: str):
        """Fetch DexScreener data"""
        try:
            address = self.token_addresses.get(token)
            if not address:
                return None
                
            url = f"{self.dexscreener_base_url}/solana/{address}"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'pairs' in data and data['pairs']:
                        pair = data['pairs'][0]
                        return {
                            'spot_price': float(pair.get('priceUsd', 0)),
                            'spot_volume_24h': float(pair.get('volume', {}).get('h24', 0)),
                            'liquidity': float(pair.get('liquidity', {}).get('usd', 0))
                        }
                return None
                
        except Exception as e:
            logger.error(f"Error fetching DexScreener data for {token}: {str(e)}")
            return None

    async def get_solscan_data(self, session: aiohttp.ClientSession, token: str):
        """Fetch Solscan holder data"""
        try:
            address = self.token_addresses.get(token)
            if not address:
                return None
                
            headers = {
                'token': os.getenv('SOLSCAN_API_KEY'),
                'Accept': 'application/json'
            }
            
            async with session.get(
                f"{self.solscan_base_url}?tokenAddress={address}",
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'holder_count': data.get('total', 0)
                    }
                return None
                
        except Exception as e:
            logger.error(f"Error fetching Solscan data for {token}: {str(e)}")
            return None


    async def collect_and_merge_data(self):
        all_data = []
        timestamp = datetime.now()

        async with aiohttp.ClientSession() as session:
            for token in self.tokens:
                try:
                    hl_data = await self.get_hl_market_data(session, token)
                    if hl_data:
                        merged_data = {
                            'timestamp': timestamp,
                            'token': token,
                            **hl_data
                        }
                        
                        dex_data = await self.get_dexscreener_data(session, token)
                        if dex_data:
                            merged_data.update(dex_data)
                            
                        solscan_data = await self.get_solscan_data(session, token)
                        if solscan_data:
                            merged_data.update(solscan_data)
                            
                        all_data.append(merged_data)
                        logger.info(f"Collected data for {token}")
                        
                except Exception as e:
                    logger.error(f"Error processing {token}: {str(e)}")

        return pd.DataFrame(all_data)

async def main():
    collector = PerpDataCollector()
    df = await collector.collect_and_merge_data()
    if not df.empty:
        collector.save_to_database(df)
    else:
        logger.warning("No data collected")

if __name__ == "__main__":
    asyncio.run(main())