import requests
from datetime import datetime, timedelta
import logging
from rich.console import Console
from rich.table import Table
from pathlib import Path
import json
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
console = Console()

class BinanceFlowIngestion:
    def __init__(self):
        self.base_url = "https://api.llama.fi"
        # Common coins on Binance
        self.coins = [
            'bitcoin', 'ethereum', 'usdt', 'usdc', 'bnb',
            'xrp', 'ada', 'doge', 'sol', 'dot'
        ]
    
    def get_coin_flows(self, coin: str, start: int, end: int) -> dict:
        """Fetch flows for a specific coin"""
        try:
            url = f"{self.base_url}/inflows/binance/{coin}/{start}"
            response = requests.get(url, params={"end": end})
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching flows for {coin}: {str(e)}")
            return None

    def get_binance_flows(self) -> dict:
        """Fetch Binance CEX flow data for multiple coins"""
        try:
            # Get timestamps for time range (24h)
            end = int(datetime.now().timestamp())
            start = end - 86400  # 24 hours in seconds
            
            all_flows = []
            total_inflow = 0
            total_outflow = 0
            
            # Create table for display
            table = Table(title="Binance 24h Flows by Coin")
            table.add_column("Coin", style="cyan")
            table.add_column("Inflow", justify="right", style="green")
            table.add_column("Outflow", justify="right", style="red")
            table.add_column("Net Flow", justify="right", style="yellow")
            
            for coin in self.coins:
                logger.info(f"Fetching flows for {coin}...")
                coin_data = self.get_coin_flows(coin, start, end)
                
                if coin_data:
                    # Calculate coin totals
                    coin_inflow = sum(float(d.get('inflow', 0)) for d in coin_data)
                    coin_outflow = sum(float(d.get('outflow', 0)) for d in coin_data)
                    coin_net = coin_inflow - coin_outflow
                    
                    # Add to totals
                    total_inflow += coin_inflow
                    total_outflow += coin_outflow
                    
                    # Add to table
                    table.add_row(
                        coin.upper(),
                        f"${coin_inflow:,.2f}",
                        f"${coin_outflow:,.2f}",
                        f"${coin_net:,.2f}"
                    )
                    
                    # Store coin data
                    all_flows.append({
                        'coin': coin,
                        'inflow': coin_inflow,
                        'outflow': coin_outflow,
                        'net_flow': coin_net,
                        'raw_data': coin_data
                    })
                
                # Sleep briefly to avoid rate limits
                time.sleep(0.5)
            
            net_flow = total_inflow - total_outflow
            
            # Add totals row
            table.add_row(
                "TOTAL",
                f"${total_inflow:,.2f}",
                f"${total_outflow:,.2f}",
                f"${net_flow:,.2f}",
                style="bold"
            )
            
            # Display table
            console.print(table)
            
            flow_data = {
                'timestamp': datetime.now().isoformat(),
                'inflow24h': total_inflow,
                'outflow24h': total_outflow,
                'netflow24h': net_flow,
                'flows_by_coin': all_flows
            }
            
            return flow_data
            
        except Exception as e:
            logger.error(f"Error fetching Binance flows: {str(e)}")
            return None

    def save_results(self, flow_data: dict) -> str:
        """Save flow data to a JSON file"""
        try:
            # Create output directory if it doesn't exist
            output_dir = Path("data/defillama")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"binance_flows_{timestamp}.json"
            output_path = output_dir / filename
            
            # Save to file
            with open(output_path, 'w') as f:
                json.dump(flow_data, f, indent=2)
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error saving results: {str(e)}")
            return None

if __name__ == "__main__":
    ingestion = BinanceFlowIngestion()
    flow_data = ingestion.get_binance_flows()
    
    if flow_data:
        output_file = ingestion.save_results(flow_data)
        print(f"\nResults saved to: {output_file}")
    else:
        print("No flow data was collected") 