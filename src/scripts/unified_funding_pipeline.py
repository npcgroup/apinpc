import asyncio
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import os
import json
import pandas as pd
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table
from dotenv import load_dotenv

# Setup logging with more detail
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
console = Console()

try:
    from supabase import create_client, Client
except ImportError as e:
    console.print("[red]Error: Failed to import Supabase client. Installing required packages...[/red]")
    os.system("pip install supabase-py gotrue postgrest")
    from supabase import create_client, Client

# Import the funding rate collectors
try:
    from binance_funding_rates import fetch_all_funding_rates as fetch_binance_rates
    from hyperliquid_funding_rates import fetch_all_funding_rates as fetch_hyperliquid_rates
except ImportError as e:
    console.print(f"[red]Error importing funding rate collectors: {str(e)}[/red]")
    sys.exit(1)

class UnifiedFundingPipeline:
    def __init__(self):
        load_dotenv()
        
        try:
            # Initialize Supabase client
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_KEY')
            
            if not supabase_url or not supabase_key:
                raise ValueError("Missing Supabase credentials in environment variables")
            
            self.supabase = create_client(supabase_url, supabase_key)
            logger.info(f"Initialized Supabase client with URL: {supabase_url}")
            
        except Exception as e:
            console.print(f"[red]Failed to initialize Supabase client: {str(e)}[/red]")
            raise

        # Setup directories
        self.output_dir = Path("data/unified_funding")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def serialize_datetime(self, obj):
        """Helper method to serialize datetime objects"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, timedelta):
            return str(obj)
        return str(obj)

    async def push_to_supabase(self, df, exchange):
        """Push funding rates to appropriate Supabase table"""
        if df is None or df.empty:
            logger.warning(f"No {exchange} data to push")
            return False
        
        try:
            # Process DataFrame based on exchange
            if exchange == 'hyperliquid':
                # Generate current timestamp
                current_time = datetime.now(timezone.utc)
                current_epoch = int(current_time.timestamp() * 1000)
                
                # Debug log
                logger.info(f"Processing {len(df)} {exchange} records")
                logger.info(f"Columns present: {df.columns.tolist()}")
                
                # Fill missing timestamps
                df['timestamp'] = df['timestamp'].fillna(current_epoch)
                
                # Convert datetime strings to proper timestamp format
                df['datetime'] = pd.to_datetime(df['datetime'], utc=True)
                if 'next_funding_time' in df.columns:
                    df['next_funding_time'] = pd.to_datetime(df['next_funding_time'], utc=True)
                
                # Ensure all required numeric columns are float
                numeric_columns = ['funding_rate', 'funding_rate_pct', 'prediction_price']
                for col in numeric_columns:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Convert DataFrame to records
            records = df.to_dict('records')
            table_name = f"{exchange}_funding_rates"
            
            # Process and validate each record
            processed_records = []
            for record in records:
                try:
                    # Ensure required fields
                    if not record.get('timestamp'):
                        record['timestamp'] = int(datetime.now(timezone.utc).timestamp() * 1000)
                    if not record.get('datetime'):
                        record['datetime'] = datetime.now(timezone.utc)
                    
                    # Convert numeric fields
                    record['funding_rate'] = float(record['funding_rate'])
                    record['funding_rate_pct'] = float(record['funding_rate_pct'])
                    
                    if 'prediction_price' in record:
                        record['prediction_price'] = float(record['prediction_price']) if record['prediction_price'] else None
                    
                    processed_records.append(record)
                    
                except Exception as e:
                    logger.error(f"Error processing record: {record}")
                    logger.error(f"Error details: {str(e)}")
                    continue
            
            if not processed_records:
                raise ValueError("No valid records to push after processing")
            
            # Debug log before pushing
            logger.info(f"Attempting to push {len(processed_records)} records to {table_name}")
            logger.info(f"Sample record: {processed_records[0]}")
            
            # Upsert records
            result = self.supabase.table(table_name).upsert(
                processed_records,
                on_conflict='symbol,timestamp'
            ).execute()
            
            logger.info(f"✅ Successfully pushed {len(processed_records)} {exchange} records to Supabase")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error pushing {exchange} data to Supabase: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            logger.exception("Full traceback:")
            return False

    def create_summary_table(self, binance_df, hyperliquid_df):
        """Create a rich table comparing funding rates across exchanges"""
        table = Table(title="📊 Funding Rates Summary")
        
        table.add_column("Metric", style="cyan")
        table.add_column("Binance", style="green")
        table.add_column("Hyperliquid", style="magenta")
        
        # Add summary rows
        table.add_row(
            "Total Markets",
            str(len(binance_df) if binance_df is not None else 0),
            str(len(hyperliquid_df) if hyperliquid_df is not None else 0)
        )
        
        if binance_df is not None and not binance_df.empty:
            b_max = f"{binance_df['funding_rate_pct'].max():.4f}%"
            b_min = f"{binance_df['funding_rate_pct'].min():.4f}%"
            b_mean = f"{binance_df['funding_rate_pct'].mean():.4f}%"
        else:
            b_max = b_min = b_mean = "N/A"
            
        if hyperliquid_df is not None and not hyperliquid_df.empty:
            h_max = f"{hyperliquid_df['funding_rate_pct'].max():.4f}%"
            h_min = f"{hyperliquid_df['funding_rate_pct'].min():.4f}%"
            h_mean = f"{hyperliquid_df['funding_rate_pct'].mean():.4f}%"
        else:
            h_max = h_min = h_mean = "N/A"
        
        table.add_row("Highest Rate", b_max, h_max)
        table.add_row("Lowest Rate", b_min, h_min)
        table.add_row("Mean Rate", b_mean, h_mean)
        
        return table

    async def run_pipeline(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            TextColumn("•"),
            TextColumn("[cyan]Est. remaining: {task.fields[remaining]}"),
            console=console
        ) as progress:
            try:
                console.print(Panel("🚀 Starting Unified Funding Rates Pipeline", style="bold green"))
                
                # Step 1: Fetch Data
                task1 = progress.add_task(
                    "[cyan]Fetching Binance funding rates...", 
                    total=100,
                    remaining="calculating..."
                )
                
                task2 = progress.add_task(
                    "[magenta]Fetching Hyperliquid funding rates...", 
                    total=100,
                    remaining="calculating..."
                )
                
                # Fetch data from both exchanges
                binance_df = fetch_binance_rates()
                progress.update(task1, completed=100)
                
                hyperliquid_df = fetch_hyperliquid_rates()
                progress.update(task2, completed=100)
                
                if binance_df is None and hyperliquid_df is None:
                    raise Exception("Failed to fetch data from both exchanges")
                
                # Step 2: Push to Supabase
                task3 = progress.add_task(
                    "[cyan]Syncing to Supabase...", 
                    total=100,
                    remaining="~30 seconds"
                )
                
                # Push data to respective tables
                binance_success = await self.push_to_supabase(binance_df, "binance")
                hyperliquid_success = await self.push_to_supabase(hyperliquid_df, "hyperliquid")
                
                progress.update(task3, completed=100)
                
                # Step 3: Save Summary
                summary = {
                    "timestamp": timestamp,
                    "binance": {
                        "success": binance_success,
                        "markets_collected": len(binance_df) if binance_df is not None else 0
                    },
                    "hyperliquid": {
                        "success": hyperliquid_success,
                        "markets_collected": len(hyperliquid_df) if hyperliquid_df is not None else 0
                    },
                    "completion_time": datetime.now().isoformat()
                }
                
                # Save summary to file
                summary_file = self.output_dir / f"funding_summary_{timestamp}.json"
                with open(summary_file, 'w') as f:
                    json.dump(summary, f, indent=2, default=self.serialize_datetime)
                
                # Display summary table
                summary_table = self.create_summary_table(binance_df, hyperliquid_df)
                console.print(summary_table)
                
                # Final success message
                console.print(Panel(
                    f"""✨ Pipeline completed successfully!
                    \n📊 Binance markets: {summary['binance']['markets_collected']}
                    \n📊 Hyperliquid markets: {summary['hyperliquid']['markets_collected']}
                    \n📝 Summary saved to: {summary_file}
                    \n⏱️ Total time: {progress.tasks[0].elapsed:.2f}s""",
                    title="Pipeline Summary",
                    style="bold green"
                ))

            except Exception as e:
                error_msg = f"❌ Pipeline failed: {str(e)}"
                logger.error(error_msg)
                console.print(Panel(error_msg, style="bold red"))
                
                # Save error summary
                error_summary = {
                    "timestamp": timestamp,
                    "error": str(e),
                    "stage": progress.tasks[-1].description if progress.tasks else "Unknown",
                    "status": "failed",
                    "error_time": datetime.now().isoformat()
                }
                
                error_file = self.output_dir / f"pipeline_error_{timestamp}.json"
                with open(error_file, 'w') as f:
                    json.dump(error_summary, f, indent=2, default=self.serialize_datetime)
                
                sys.exit(1)

async def main():
    try:
        # Check environment variables
        required_vars = ['SUPABASE_URL', 'SUPABASE_KEY']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            raise Exception(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        pipeline = UnifiedFundingPipeline()
        
        # Test Supabase connection
        try:
            test_result = pipeline.supabase.table('hyperliquid_funding_rates').select("count(*)").execute()
            logger.info("Successfully connected to Supabase")
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {str(e)}")
            raise
        
        await pipeline.run_pipeline()
        
    except Exception as e:
        console.print(f"[red]Fatal error: {str(e)}[/red]")
        logger.exception("Pipeline failed with error:")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 