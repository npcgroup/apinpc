import os
import requests
from typing import Dict, List, TypedDict
from datetime import datetime
import logging
import json
from rich.console import Console
from rich.table import Table
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
console = Console()

class Protocol(TypedDict):
    name: str
    tvl: float
    chains: List[str]
    volume24h: float
    address: str

class DefiLlamaIngestion:
    def __init__(self):
        self.base_url = "https://api.llama.fi"
        
    def get_protocols(self) -> List[Protocol]:
        """Fetch protocol data from DefiLlama"""
        try:
            response = requests.get(f"{self.base_url}/protocols")
            response.raise_for_status()
            data = response.json()
            
            protocols = []
            for p in data:
                if p.get('tvl') and p.get('chains'):
                    protocols.append({
                        'name': p.get('name', ''),
                        'tvl': float(p.get('tvl', 0)),
                        'chains': p.get('chains', []),
                        'volume24h': float(p.get('volume24h', 0)),
                        'address': p.get('address', '')
                    })
            
            logger.info(f"Fetched {len(protocols)} protocols from DefiLlama")
            return protocols
            
        except Exception as e:
            logger.error(f"Error fetching protocols: {str(e)}")
            return []

    def save_results(self, protocols: List[Protocol], output_dir: str = "data/defillama"):
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"{output_dir}/protocols_{timestamp}.json"
        
        with open(output_file, 'w') as f:
            json.dump(protocols, f, indent=2)
        
        logger.info(f"Saved {len(protocols)} protocols to {output_file}")
        
        table = Table(title="DefiLlama Protocols")
        table.add_column("Name", style="cyan")
        table.add_column("TVL", justify="right", style="green")
        table.add_column("Volume 24h", justify="right", style="yellow")
        table.add_column("Chains", style="magenta")
        
        for protocol in sorted(protocols, key=lambda x: x['tvl'], reverse=True)[:20]:
            table.add_row(
                protocol['name'],
                f"${protocol['tvl']:,.0f}",
                f"${protocol['volume24h']:,.0f}",
                ", ".join(protocol['chains'][:3])
            )
        
        console.print(table)
        return output_file

if __name__ == "__main__":
    ingestion = DefiLlamaIngestion()
    protocols = ingestion.get_protocols()
    
    if protocols:
        output_file = ingestion.save_results(protocols)
        print(f"\nResults saved to: {output_file}")
    else:
        print("No protocols were collected") 