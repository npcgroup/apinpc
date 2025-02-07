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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
console = Console()

class HyperscanMetrics(TypedDict):
    address: str
    chain_id: str
    transaction_count: int
    balance: float
    first_tx_timestamp: datetime
    last_tx_timestamp: datetime
    token_transfers: int
    timestamp: datetime

class HyperscanIngestion:
    def __init__(self):
        self.base_url = "https://api.hyperscan.xyz/info"  # Replace with actual API URL
        self.api_key = os.getenv("HYPERSCAN_API_KEY")
        if not self.api_key:
            raise ValueError("HYPERSCAN_API_KEY environment variable not set")

    def retry_request(self, url: str, max_retries: int = 3, delay: int = 2) -> dict:
        """Make HTTP request with retry logic"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Failed to fetch {url} after {max_retries} attempts: {str(e)}")
                    raise
                logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay}s...")
                time.sleep(delay)
                delay *= 2

    def get_address_metrics(self, addresses: List[str]) -> List[HyperscanMetrics]:
        """Fetch address metrics from Hyperscan"""
        try:
            metrics = []
            for address in addresses:
                data = self.retry_request(f"{self.base_url}/v1/addresses/{address}")
                
                metrics.append({
                    'address': address,
                    'chain_id': data.get('chain_id', ''),
                    'transaction_count': int(data.get('transaction_count', 0)),
                    'balance': float(data.get('balance', 0)),
                    'first_tx_timestamp': datetime.fromtimestamp(data.get('first_tx_timestamp', 0)),
                    'last_tx_timestamp': datetime.fromtimestamp(data.get('last_tx_timestamp', 0)),
                    'token_transfers': int(data.get('token_transfers', 0)),
                    'timestamp': datetime.now()
                })
                
                # Rate limiting
                time.sleep(0.2)  # 5 requests per second
            
            logger.info(f"Fetched metrics for {len(metrics)} addresses from Hyperscan")
            return metrics
            
        except Exception as e:
            logger.error(f"Error fetching address metrics: {str(e)}")
            return []

    def save_results(self, metrics: List[HyperscanMetrics], output_dir: str = "data/hyperscan"):
        """Save results to JSON file and print summary"""
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"{output_dir}/address_metrics_{timestamp}.json"
        
        # Convert datetime objects to string for JSON serialization
        json_metrics = []
        for metric in metrics:
            json_metric = metric.copy()
            json_metric['timestamp'] = json_metric['timestamp'].isoformat()
            json_metric['first_tx_timestamp'] = json_metric['first_tx_timestamp'].isoformat()
            json_metric['last_tx_timestamp'] = json_metric['last_tx_timestamp'].isoformat()
            json_metrics.append(json_metric)
            
        with open(output_file, 'w') as f:
            json.dump(json_metrics, f, indent=2)
        
        logger.info(f"Saved {len(metrics)} address metrics to {output_file}")
        
        # Print summary table
        table = Table(title="Hyperscan Address Metrics")
        table.add_column("Address", style="cyan")
        table.add_column("Chain", style="magenta")
        table.add_column("Txn Count", justify="right", style="green")
        table.add_column("Balance", justify="right", style="yellow")
        table.add_column("Token Transfers", justify="right", style="blue")
        table.add_column("Last Active", style="red")
        
        for metric in sorted(metrics, key=lambda x: x['transaction_count'], reverse=True)[:20]:
            table.add_row(
                metric['address'][:10] + "...",
                metric['chain_id'],
                f"{metric['transaction_count']:,}",
                f"{metric['balance']:.4f}",
                f"{metric['token_transfers']:,}",
                metric['last_tx_timestamp'].strftime("%Y-%m-%d")
            )
        
        console.print(table)
        return output_file

if __name__ == "__main__":
    # Example addresses to track
    addresses = [
        "0x1234...",  # Replace with actual addresses
        "0x5678..."
    ]
    
    ingestion = HyperscanIngestion()
    metrics = ingestion.get_address_metrics(addresses)
    
    if metrics:
        output_file = ingestion.save_results(metrics)
        print(f"\nResults saved to: {output_file}")
    else:
        print("No address metrics were collected") 