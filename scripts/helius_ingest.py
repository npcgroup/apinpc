import os
import json
import asyncio
import aiohttp
import logging
from datetime import datetime
from typing import Dict, Optional
from dotenv import load_dotenv
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HeliusTokenAnalyzer:
    def __init__(self):
        # Load environment variables
        env_files = ['.env', '.env.local', '../.env', '../.env.local']
        for env_file in env_files:
            env_path = Path(env_file)
            if env_path.exists():
                logger.info(f"Loading environment from {env_path.absolute()}")
                load_dotenv(env_path)
        
        self.api_key = ('edb296ae-f9c1-47c4-866f-a43fc6b9832d')
        if not self.api_key:
            raise ValueError("NEXT_PUBLIC_HELIUS_API_KEY not found in environment variables")
            
        self.base_url = f"https://api.helius.xyz/v0"
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def save_debug_output(self, data: dict, filename: str):
        """Save debug output to a file"""
        debug_dir = Path('data/debug')
        debug_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filepath = debug_dir / f'{filename}_{timestamp}.json'
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Debug data saved to {filepath}")

    async def get_token_metadata(self, address: str) -> Optional[dict]:
        """Fetch metadata for a single token"""
        if not self.session:
            raise RuntimeError("Session not initialized. Use async with context manager.")
            
        url = f"{self.base_url}/token-metadata"
        payload = {
            "mintAccounts": [address],
            "includeOffChain": True,
            "disableCache": False
        }
        
        try:
            logger.info(f"Requesting metadata for {address}")
            logger.info(f"URL: {url}")
            logger.info(f"Payload: {json.dumps(payload)}")
            
            async with self.session.post(
                url,
                params={'api-key': self.api_key},
                json=payload,
                headers={'Content-Type': 'application/json'}
            ) as response:
                response_text = await response.text()
                logger.info(f"Response status: {response.status}")
                logger.info(f"Response body: {response_text}")
                
                if response.status == 200:
                    try:
                        data = json.loads(response_text)
                        if data and len(data) > 0:
                            logger.info(f"Successfully got metadata for {address}")
                            return data[0]
                        else:
                            logger.warning(f"Empty response for {address}")
                            return None
                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON response for {address}: {e}")
                        return None
                else:
                    logger.error(f"Error {response.status} fetching metadata for {address}: {response_text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Request failed for {address}: {str(e)}")
            return None

    async def get_holder_data(self, token_addresses: Dict[str, str]) -> Dict[str, dict]:
        """Fetch holder data and metadata for multiple tokens"""
        results = {}
        all_responses = {}
        
        for symbol, address in token_addresses.items():
            try:
                logger.info(f"\nProcessing {symbol} ({address})")
                metadata = await self.get_token_metadata(address)
                
                # Store raw response
                all_responses[symbol] = metadata
                
                # Initialize default values
                default_data = {
                    'holder_count': 0,
                    'total_supply': 0,
                    'decimals': 0,
                    'symbol': symbol,
                    'name': symbol,
                    'market_cap': 0,
                    'volume_24h': 0,
                    'price_usd': 0,
                    'twitter_followers': 0,
                    'discord_members': 0
                }
                
                if metadata:
                    off_chain = metadata.get('offChainData', {})
                    on_chain = metadata.get('onChainData', {})
                    
                    logger.info(f"Raw metadata for {symbol}:")
                    logger.info(json.dumps(metadata, indent=2))
                    
                    results[symbol] = {
                        'holder_count': int(off_chain.get('holderCount', 0)),
                        'total_supply': float(on_chain.get('supply', 0)),
                        'decimals': int(on_chain.get('decimals', 0)),
                        'symbol': on_chain.get('symbol', symbol),
                        'name': on_chain.get('name', symbol),
                        'market_cap': float(off_chain.get('marketCap', 0)),
                        'volume_24h': float(off_chain.get('volume24h', 0)),
                        'price_usd': float(off_chain.get('price', 0)),
                        'twitter_followers': int(off_chain.get('twitterFollowers', 0)),
                        'discord_members': int(off_chain.get('discordMembers', 0))
                    }
                else:
                    results[symbol] = default_data.copy()
                    logger.warning(f"Using default values for {symbol} due to missing metadata")
                
                await asyncio.sleep(0.2)
                
            except Exception as e:
                logger.error(f"Error processing {symbol}: {str(e)}")
                results[symbol] = default_data.copy()
                results[symbol]['error'] = str(e)
        
        # Save debug data
        self.save_debug_output(all_responses, 'helius_raw')
        self.save_debug_output(results, 'helius_processed')
        
        return results

async def main():
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
    
    try:
        async with HeliusTokenAnalyzer() as analyzer:
            logger.info("Starting Helius data collection...")
            holder_data = await analyzer.get_holder_data(token_addresses)
            
            print("\nToken Data Summary:")
            print("-" * 60)
            for token, data in holder_data.items():
                print(f"\n{token}:")
                print(f"  Holders: {data.get('holder_count', 0):,}")
                print(f"  Market Cap: ${data.get('market_cap', 0):,.2f}")
                print(f"  24h Volume: ${data.get('volume_24h', 0):,.2f}")
                print(f"  Price: ${data.get('price_usd', 0):,.8f}")
                
                if data.get('twitter_followers', 0) > 0:
                    print(f"  Twitter Followers: {data['twitter_followers']:,}")
                if data.get('discord_members', 0) > 0:
                    print(f"  Discord Members: {data['discord_members']:,}")
                if 'error' in data:
                    print(f"  Error: {data['error']}")
            
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())