import pandas as pd
from datetime import datetime, timezone
import logging
from supabase import create_client
import os
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from typing import List, Dict, Optional
import sys

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
console = Console()

class BinanceDataUploader:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Initialize Supabase client
        self.supabase = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_KEY')
        )
    
    def process_market_data(self, df: pd.DataFrame) -> List[Dict]:
        """Process DataFrame into records for Supabase"""
        try:
            if df is None or df.empty:
                raise ValueError("No data to process")
            
            records = []
            for _, row in df.iterrows():
                # Calculate USD values
                mark_price = float(row['mark_price'])
                open_interest = float(row['open_interest'])
                open_interest_usd = open_interest * mark_price  # Convert to USD value
                
                record = {
                    'symbol': row['symbol'],
                    'base': row['base'],
                    'quote': row['quote'],
                    'open_interest': open_interest,
                    'open_interest_usd': open_interest_usd,  # Store USD value
                    'mark_price': mark_price,
                    'index_price': float(row['index_price']),
                    'high_24h': float(row['high_24h']),
                    'low_24h': float(row['low_24h']),
                    'volume_24h': float(row['volume_24h']),
                    'volume_base_24h': float(row['volume_base_24h']),
                    'price_change_24h': float(row['price_change_24h']),
                    'price_change': float(row['price_change']),
                    'funding_rate': float(row['funding_rate']),
                    'next_funding_time': row['next_funding_time'],
                    'contract_size': float(row['contract_size']),
                    'leverage_max': float(row['leverage_max']),
                    'timestamp': int(row['timestamp']),
                    'datetime': pd.to_datetime(row['datetime']).isoformat(),
                    'type': row['type']
                }
                records.append(record)
                
                # Log sample of processed records with USD values
                if len(records) <= 5:
                    logger.info(f"Processed {record['symbol']}: "
                              f"OI={record['open_interest']:.2f} {row['base']}, "
                              f"OI_USD=${record['open_interest_usd']:,.2f}, "
                              f"Price=${record['mark_price']:,.2f}")
            
            return records
            
        except Exception as e:
            logger.error(f"Error processing market data: {e}")
            return None
    
    def push_to_supabase(self, records: List[Dict]) -> bool:
        """Push records to Supabase"""
        if not records:
            logger.warning("No records to push")
            return False
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("[cyan]Pushing to Supabase...", total=None)
                
                # Insert new records
                result = self.supabase.table('binance_market_data').insert(
                    records
                ).execute()
                
                progress.update(task, completed=True)
            
            console.print(Panel(
                f"✅ Successfully pushed {len(records)} records to Supabase\n"
                f"Sample markets:\n" + "\n".join(
                    f"{r['symbol']}: ${r['open_interest_usd']:,.2f} OI" 
                    for r in records[:5]
                ),
                style="bold green"
            ))
            return True
            
        except Exception as e:
            if 'duplicate key value violates unique constraint' in str(e):
                logger.info("Some records already exist (skipped duplicates)")
                return True
            else:
                console.print(Panel(
                    f"❌ Error pushing to Supabase: {str(e)}",
                    style="bold red"
                ))
                return False

def main():
    try:
        from binance_market_data import fetch_market_data
        
        uploader = BinanceDataUploader()
        
        # Fetch market data
        console.print("[cyan]Fetching Binance market data...[/cyan]")
        df = fetch_market_data()
        
        if df is None:
            raise Exception("Failed to fetch market data")
        
        # Process data
        console.print("[cyan]Processing market data...[/cyan]")
        records = uploader.process_market_data(df)
        
        if not records:
            raise Exception("Failed to process market data")
        
        # Push to Supabase
        success = uploader.push_to_supabase(records)
        
        if success:
            console.print(Panel(
                "🎉 Market data successfully uploaded to Supabase!",
                style="bold green"
            ))
        else:
            raise Exception("Failed to push data to Supabase")
            
    except Exception as e:
        console.print(Panel(
            f"❌ Error: {str(e)}",
            style="bold red"
        ))
        sys.exit(1)

if __name__ == "__main__":
    main() 