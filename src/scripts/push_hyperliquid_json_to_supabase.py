import json
import pandas as pd
from datetime import datetime, timezone, timedelta
from pathlib import Path
import logging
from supabase import create_client
import os
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
console = Console()

class HyperliquidJsonUploader:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Initialize Supabase client
        self.supabase = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_KEY')
        )
        
        # Setup paths
        self.json_dir = Path('hyperliquid_funding_rates')
        self.latest_file = self.json_dir / 'latest.json'
        
    def load_json_data(self, file_path=None):
        """Load data from JSON file"""
        try:
            file_to_read = file_path if file_path else self.latest_file
            
            if not file_to_read.exists():
                raise FileNotFoundError(f"JSON file not found: {file_to_read}")
            
            with open(file_to_read, 'r') as f:
                data = json.load(f)
            
            return data
            
        except Exception as e:
            logger.error(f"Error loading JSON data: {e}")
            return None

    def convert_funding_rate(self, rate):
        """
        Convert funding rate to proper 8-hour format
        Examples:
        - 0.00014723 -> -0.14723 (matches platform display)
        - -0.00014723 -> -0.14723
        The rate shown on the platform is in percentage form,
        needs to be moved 3 decimal places
        """
        try:
            # Convert to float and multiply by 1000 to get the correct percentage
            # (moving decimal point 3 places right)
            return float(rate) * 1000
        except (TypeError, ValueError):
            logger.warning(f"Invalid funding rate value: {rate}")
            return 0.0

    def process_funding_data(self, data):
        """Convert JSON data to proper format for Supabase with correct funding rate calculations"""
        try:
            records = []
            timestamp = datetime.fromisoformat(data['datetime'].replace('Z', '+00:00'))
            # Convert to milliseconds and ensure it's an integer
            epoch_ms = int(timestamp.timestamp() * 1000)
            
            # Process each rate entry
            for rate in data['rates']:
                try:
                    # Convert funding rates to proper format (basis points)
                    raw_funding_rate = float(rate['funding_rate'])
                    converted_funding_rate = self.convert_funding_rate(raw_funding_rate)
                    
                    # Ensure next_funding_time is properly formatted
                    next_funding_time = None
                    if rate.get('next_funding_time'):
                        try:
                            next_funding_time = pd.to_datetime(rate['next_funding_time']).isoformat()
                        except:
                            # If conversion fails, calculate next funding time (8 hours from current)
                            next_funding_time = (timestamp + timedelta(hours=8)).isoformat()
                    
                    record = {
                        'symbol': rate['symbol'],
                        'funding_rate': converted_funding_rate / 100,  # Store as decimal
                        'funding_rate_pct': converted_funding_rate,    # Store as percentage
                        'timestamp': epoch_ms,  # Ensure this is an integer
                        'datetime': timestamp.isoformat(),
                        'prediction_price': float(rate['prediction_price']) if rate.get('prediction_price') else None,
                        'next_funding_time': next_funding_time
                    }
                    
                    # Validate timestamp before adding to records
                    if not isinstance(record['timestamp'], int):
                        raise ValueError(f"Invalid timestamp format for {rate['symbol']}: {record['timestamp']}")
                    
                    # Add debug logging
                    logger.info(f"Converting {rate['symbol']}: "
                              f"Original rate: {raw_funding_rate}, "
                              f"Converted rate: {converted_funding_rate:0.4f}%, "
                              f"Timestamp: {record['timestamp']}")
                    
                    records.append(record)
                    
                except Exception as e:
                    logger.warning(f"Skipping rate entry due to error: {e}")
                    continue
            
            if not records:
                raise ValueError("No valid records were processed")
            
            return records
            
        except Exception as e:
            logger.error(f"Error processing funding data: {e}")
            logger.exception("Full traceback:")
            return None

    def push_to_supabase(self, records):
        """Push processed records to Supabase with validation"""
        if not records:
            logger.warning("No records to push")
            return False
        
        try:
            # Validate records before pushing
            for record in records:
                # Log a sample of records for verification
                logger.info(f"Pushing record - Symbol: {record['symbol']}, "
                          f"Funding Rate: {record['funding_rate_pct']}%, "
                          f"Timestamp: {record['datetime']}")
                
                if abs(record['funding_rate_pct']) > 100:
                    logger.warning(f"Unusually high funding rate detected for {record['symbol']}: "
                                 f"{record['funding_rate_pct']}%")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("[cyan]Pushing to Supabase...", total=None)
                
                # Insert new records instead of upserting
                result = self.supabase.table('hyperliquid_funding_rates').insert(
                    records
                ).execute()
                
                progress.update(task, completed=True)
            
            console.print(Panel(
                f"✅ Successfully pushed {len(records)} new records to Supabase\n"
                f"Sample rates:\n" + "\n".join(
                    f"{r['symbol']}: {r['funding_rate_pct']}%" 
                    for r in records[:5]
                ),
                style="bold green"
            ))
            return True
            
        except Exception as e:
            if 'duplicate key value violates unique constraint' in str(e):
                # Log duplicate entries but don't treat as error
                logger.info("Some records already exist in database (skipped duplicates)")
                return True
            else:
                console.print(Panel(
                    f"❌ Error pushing to Supabase: {str(e)}",
                    style="bold red"
                ))
                return False

def main():
    try:
        uploader = HyperliquidJsonUploader()
        
        # Load JSON data
        console.print("[cyan]Loading JSON data...[/cyan]")
        data = uploader.load_json_data()
        
        if not data:
            raise Exception("Failed to load JSON data")
        
        # Process data with proper rate conversion
        console.print("[cyan]Processing funding data with rate conversion...[/cyan]")
        records = uploader.process_funding_data(data)
        
        if not records:
            raise Exception("Failed to process funding data")
        
        # Display sample of converted rates
        console.print(Panel(
            "Sample of converted funding rates:\n" + "\n".join(
                f"{r['symbol']}: {r['funding_rate_pct']}%" 
                for r in records[:5]
            ),
            style="bold cyan"
        ))
        
        # Push to Supabase
        success = uploader.push_to_supabase(records)
        
        if success:
            console.print(Panel(
                "🎉 Data successfully uploaded to Supabase!",
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