import os
import requests
from typing import Dict, List, TypedDict, Optional
from datetime import datetime, timedelta
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
    inflow24h: Optional[float]
    outflow24h: Optional[float]
    netflow24h: Optional[float]

class DefiLlamaIngestion:
    def __init__(self):
        self.base_url = "https://api.llama.fi"
        
    def get_exchange_flows(self, exchange: str = "binance") -> Dict[str, float]:
        """Fetch exchange flow data from DefiLlama"""
        try:
            # Get timestamp for 24 hours ago
            end = int(datetime.now().timestamp())
            start = end - 86400  # 24 hours in seconds
            
            # Updated to use the correct v2 endpoint
            response = requests.get(
                f"{self.base_url}/v2/cex/flows/{exchange}",
                params={"startTime": start, "endTime": end}
            )
            response.raise_for_status()
            data = response.json()
            
            # The v2 API returns data in a different format
            if data and len(data) > 0:
                # Sum up all deposits and withdrawals
                total_inflow = sum(float(d.get('deposits', 0)) for d in data)
                total_outflow = sum(float(d.get('withdrawals', 0)) for d in data)
                net_flow = total_inflow - total_outflow
                
                logger.info(f"Fetched flow data for {exchange}: Inflow=${total_inflow:,.0f}, Outflow=${total_outflow:,.0f}")
                
                return {
                    'inflow24h': total_inflow,
                    'outflow24h': total_outflow,
                    'netflow24h': net_flow
                }
            else:
                logger.warning(f"No flow data returned for {exchange}")
                return {'inflow24h': 0, 'outflow24h': 0, 'netflow24h': 0}
            
        except Exception as e:
            logger.error(f"Error fetching exchange flows: {str(e)}")
            return {'inflow24h': 0, 'outflow24h': 0, 'netflow24h': 0}

    def get_protocols(self) -> List[Protocol]:
        """Fetch protocol data from DefiLlama"""
        try:
            response = requests.get(f"{self.base_url}/protocols")
            response.raise_for_status()
            data = response.json()
            
            # Get Binance flow data
            flow_data = self.get_exchange_flows("binance")
            
            protocols = []
            for p in data:
                if p.get('tvl') and p.get('chains'):
                    protocol_data = {
                        'name': p.get('name', ''),
                        'tvl': float(p.get('tvl', 0)),
                        'chains': p.get('chains', []),
                        'volume24h': float(p.get('volume24h', 0)),
                        'address': p.get('address', ''),
                        'inflow24h': None,
                        'outflow24h': None,
                        'netflow24h': None
                    }
                    
                    # Add flow data only for Binance-related protocols
                    if any(name in p.get('name', '').lower() for name in ['binance', 'bnb']):
                        protocol_data.update(flow_data)
                    
                    protocols.append(protocol_data)
            
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
        table.add_column("Inflow 24h", justify="right", style="blue")
        table.add_column("Outflow 24h", justify="right", style="red")
        table.add_column("Net Flow 24h", justify="right", style="purple")
        table.add_column("Chains", style="magenta")
        
        for protocol in sorted(protocols, key=lambda x: x['tvl'], reverse=True)[:20]:
            inflow = f"${protocol['inflow24h']:,.0f}" if protocol.get('inflow24h') is not None else "N/A"
            outflow = f"${protocol['outflow24h']:,.0f}" if protocol.get('outflow24h') is not None else "N/A"
            net_flow = f"${protocol['netflow24h']:,.0f}" if protocol.get('netflow24h') is not None else "N/A"
            
            table.add_row(
                protocol['name'],
                f"${protocol['tvl']:,.0f}",
                f"${protocol['volume24h']:,.0f}",
                inflow,
                outflow,
                net_flow,
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