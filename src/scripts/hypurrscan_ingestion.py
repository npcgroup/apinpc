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

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
console = Console()

class TokenHolders(TypedDict):
    token: str
    holders: List[Dict]
    timestamp: datetime

class AddressDetails(TypedDict):
    address: str
    rank: Dict
    tags: List[str]
    details: Dict
    timestamp: datetime

class HypurrscanIngestion:
    def __init__(self):
        self.base_url = "https://api.hypurrscan.io"
        self.tokens = ["PURR", "HYPE", "HFUN"]  # Added HFUN to available tokens
    
    def get_token_holders(self, token: str, limit: Optional[int] = None) -> TokenHolders:
        """Fetch token holders data"""
        try:
            if token not in self.tokens:
                raise ValueError(f"Invalid token. Must be one of: {', '.join(self.tokens)}")

            if limit:
                response = requests.get(f"{self.base_url}/holdersWithLimit/{token}/{limit}")
            else:
                response = requests.get(f"{self.base_url}/holders/{token}")
            response.raise_for_status()
            
            return {
                'token': token,
                'holders': response.json(),
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error fetching holders for {token}: {str(e)}")
            return {'token': token, 'holders': [], 'timestamp': datetime.now()}

    def get_token_details(self, token: str) -> Dict:
        """Fetch token details"""
        try:
            if token not in self.tokens:
                raise ValueError(f"Invalid token. Must be one of: {', '.join(self.tokens)}")

            response = requests.get(f"{self.base_url}/tokenDetails/{token}")
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Error fetching token details: {str(e)}")
            return {}

    def get_twap(self, token: str) -> Dict:
        """Fetch TWAP data for token"""
        try:
            if token not in self.tokens:
                raise ValueError(f"Invalid token. Must be one of: {', '.join(self.tokens)}")

            response = requests.get(f"{self.base_url}/twap/{token}")
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Error fetching TWAP data: {str(e)}")
            return {}

    def get_global_data(self) -> Dict:
        """Fetch global data like aliases and deploys"""
        try:
            aliases = requests.get(f"{self.base_url}/globalAliases")
            deploys = requests.get(f"{self.base_url}/deploys")
            bridges = requests.get(f"{self.base_url}/bridges")
            
            return {
                'aliases': aliases.json() if aliases.ok else [],
                'deploys': deploys.json() if deploys.ok else [],
                'bridges': bridges.json() if bridges.ok else [],
                'timestamp': datetime.now()
            }
        except Exception as e:
            logger.error(f"Error fetching global data: {str(e)}")
            return {}

    def save_results(self, data: Dict, data_type: str, output_dir: str = "data/hypurrscan"):
        """Save results to JSON file and print summary"""
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"{output_dir}/{data_type}_{timestamp}.json"
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        logger.info(f"Saved {data_type} data to {output_file}")
        
        try:
            # Print summary table based on data type
            if '_holders' in data_type and data.get('holders'):
                table = Table(title=f"Token Holders: {data['token']}")
                table.add_column("Rank", style="cyan", justify="right")
                table.add_column("Address", style="green")
                table.add_column("Balance", justify="right", style="yellow")
                
                for i, holder in enumerate(data['holders'][:20], 1):
                    if isinstance(holder, dict):  # Check if holder is a dictionary
                        table.add_row(
                            str(i),
                            holder.get('address', 'N/A')[:10] + "...",
                            f"{float(holder.get('balance', 0)):,.2f}"
                        )
                console.print(table)
            
            elif '_details' in data_type and data:
                table = Table(title=f"Token Details")
                table.add_column("Metric", style="cyan")
                table.add_column("Value", style="green")
                
                for key, value in data.items():
                    if key != 'timestamp':
                        table.add_row(key, str(value))
                console.print(table)
            
            elif '_twap' in data_type and data:
                table = Table(title="TWAP Data")
                table.add_column("Metric", style="cyan")
                table.add_column("Value", style="green")
                
                if isinstance(data, dict):
                    for key, value in data.items():
                        table.add_row(key, str(value))
                    console.print(table)
            
            elif data_type == 'global' and data:
                table = Table(title="Global Statistics")
                table.add_column("Metric", style="cyan")
                table.add_column("Count", style="green")
                
                table.add_row("Aliases", str(len(data.get('aliases', []))))
                table.add_row("Deploys", str(len(data.get('deploys', []))))
                table.add_row("Bridges", str(len(data.get('bridges', []))))
                console.print(table)
                
        except Exception as e:
            logger.warning(f"Could not create summary table: {str(e)}")
            # Continue execution even if table creation fails
            
        return output_file

if __name__ == "__main__":
    ingestion = HypurrscanIngestion()
    
    # Process each token
    for token in ingestion.tokens:
        logger.info(f"\nProcessing {token}...")
        
        # Fetch token holders
        holders = ingestion.get_token_holders(token, limit=100)
        if holders['holders']:
            output_file = ingestion.save_results(holders, f'{token.lower()}_holders')
            print(f"\nHolders data saved to: {output_file}")
        
        # Fetch token details
        token_details = ingestion.get_token_details(token)
        if token_details:
            output_file = ingestion.save_results(token_details, f'{token.lower()}_details')
            print(f"\nToken details saved to: {output_file}")
        
        # Fetch TWAP data
        twap_data = ingestion.get_twap(token)
        if twap_data:
            output_file = ingestion.save_results(twap_data, f'{token.lower()}_twap')
            print(f"\nTWAP data saved to: {output_file}")
    
    # Fetch global data
    global_data = ingestion.get_global_data()
    if global_data:
        output_file = ingestion.save_results(global_data, 'global')
        print(f"\nGlobal data saved to: {output_file}") 