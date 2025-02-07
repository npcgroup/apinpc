import os
import requests
import time
from typing import Dict, List, Optional, TypedDict
from datetime import datetime
import logging
import json
from rich.console import Console
from rich.table import Table
from pathlib import Path
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add these to the imports at the top
console = Console()

load_dotenv()

class TokenProfile(TypedDict):
    url: str
    chainId: str
    tokenAddress: str
    icon: Optional[str]
    header: Optional[str]
    description: Optional[str]

class TokenMetrics(TypedDict):
    address: str
    symbol: str
    name: str
    price: float
    volume24h: float
    marketCap: float
    totalSupply: Optional[float]
    timestamp: datetime

class DataIngestion:
    def __init__(self):
        self.dexscreener_base_url = "https://api.dexscreener.com"
        self.defillama_base_url = "https://api.llama.fi"
        self.dune_api_key = os.getenv("NEXT_PUBLIC_DUNE_API_KEY")
        self.flipside_api_key = os.getenv("NEXT_PUBLIC_FLIPSIDE_API_KEY")
        self.messari_api_key = os.getenv("NEXT_PUBLIC_MESSARI_API_KEY")

    def retry_request(self, url: str, max_retries: int = 3, delay: int = 2) -> dict:
        """Make HTTP request with retry logic"""
        for attempt in range(max_retries):
            try:
                response = requests.get(url, timeout=5)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Failed to fetch {url} after {max_retries} attempts: {str(e)}")
                    raise
                logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay}s...")
                time.sleep(delay)
                delay *= 2  # Exponential backoff

    def get_token_profiles(self) -> List[TokenProfile]:
        """Fetch latest token profiles from DexScreener"""
        try:
            data = self.retry_request(f"{self.dexscreener_base_url}/token-profiles/latest/v1")
            logger.info(f"Fetched {len(data)} token profiles from DexScreener")
            return data
        except Exception as e:
            logger.error(f"Error fetching token profiles: {str(e)}")
            return []

    def get_token_pairs(self, token_addresses: List[str]) -> dict:
        """Fetch token pairs from DexScreener"""
        if not token_addresses:
            return {}
        
        # DexScreener allows max 30 addresses per request
        chunk_size = 30
        all_pairs = {}
        
        for i in range(0, len(token_addresses), chunk_size):
            chunk = token_addresses[i:i + chunk_size]
            addresses_str = ','.join(chunk)
            try:
                data = self.retry_request(
                    f"{self.dexscreener_base_url}/latest/dex/tokens/{addresses_str}"
                )
                if data.get('pairs'):
                    for pair in data['pairs']:
                        all_pairs[pair['baseToken']['address'].lower()] = pair
            except Exception as e:
                logger.error(f"Error fetching pairs for chunk {i}: {str(e)}")
            
            # Rate limiting
            time.sleep(1)
            
        return all_pairs

    def get_defillama_tokens(self) -> List[dict]:
        """Fetch token data from DefiLlama"""
        try:
            data = self.retry_request(f"{self.defillama_base_url}/protocols")
            return [p for p in data if p.get('tvl') and p.get('chains')]
        except Exception as e:
            logger.error(f"Error fetching DefiLlama tokens: {str(e)}")
            return []

    def ingest_token_data(self):
        """Main token data ingestion process"""
        try:
            # Get token data from multiple sources
            token_profiles = self.get_token_profiles()
            defillama_tokens = self.get_defillama_tokens()

            # Get token addresses
            token_addresses = [t['tokenAddress'].lower() for t in token_profiles]
            
            # Get detailed pair data
            token_pairs = self.get_token_pairs(token_addresses)

            # Combine data
            token_metrics: List[TokenMetrics] = []
            for profile in token_profiles:
                try:
                    address = profile['tokenAddress'].lower()
                    pair_data = token_pairs.get(address, {})
                    
                    metrics: TokenMetrics = {
                        'address': address,
                        'symbol': pair_data.get('baseToken', {}).get('symbol', ''),
                        'name': pair_data.get('baseToken', {}).get('name', ''),
                        'price': float(pair_data.get('priceUsd', 0)),
                        'volume24h': float(pair_data.get('volume24h', 0)),
                        'marketCap': float(pair_data.get('marketCap', 0)),
                        'totalSupply': None,
                        'timestamp': datetime.now()
                    }
                    token_metrics.append(metrics)
                except Exception as e:
                    logger.error(f"Error processing token {profile.get('tokenAddress')}: {str(e)}")

            logger.info(f"Processed {len(token_metrics)} tokens")
            return token_metrics

        except Exception as e:
            logger.error(f"Token ingestion error: {str(e)}")
            raise

    def save_results(self, token_metrics: List[TokenMetrics], output_dir: str = "data"):
        """Save results to JSON file and print summary"""
        # Create output directory if it doesn't exist
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Save to JSON file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"{output_dir}/token_metrics_{timestamp}.json"
        
        # Convert datetime objects to string for JSON serialization
        json_metrics = []
        for metric in token_metrics:
            json_metric = metric.copy()
            json_metric['timestamp'] = json_metric['timestamp'].isoformat()
            json_metrics.append(json_metric)
            
        with open(output_file, 'w') as f:
            json.dump(json_metrics, f, indent=2)
        
        logger.info(f"Saved results to {output_file}")
        
        # Print summary table
        table = Table(title="Token Metrics Summary")
        table.add_column("Symbol", style="cyan")
        table.add_column("Name", style="magenta")
        table.add_column("Price", justify="right", style="green")
        table.add_column("Volume 24h", justify="right", style="yellow")
        table.add_column("Market Cap", justify="right", style="blue")
        
        for metric in sorted(token_metrics, key=lambda x: x['marketCap'], reverse=True)[:20]:
            table.add_row(
                metric['symbol'],
                metric['name'][:30],
                f"${metric['price']:.2f}",
                f"${metric['volume24h']:,.0f}",
                f"${metric['marketCap']:,.0f}"
            )
        
        console.print(table)
        
        return output_file

if __name__ == "__main__":
    ingestion = DataIngestion()
    token_metrics = ingestion.ingest_token_data()
    
    if token_metrics:
        output_file = ingestion.save_results(token_metrics)
        print(f"\nFull results saved to: {output_file}")
    else:
        print("No token metrics were collected") 