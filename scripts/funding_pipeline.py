import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
import sys
import os
import json
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

# Import the correct collector
from hypefundingstablev2 import HyperliquidFundingCollector
from sync_funding_to_supabase import SupabaseSync
from analyze_funding_rates import FundingRateAnalyzer

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
console = Console()

class FundingPipeline:
    def __init__(self):
        self.funding_collector = HyperliquidFundingCollector()
        self.supabase_sync = SupabaseSync()
        self.analyzer = FundingRateAnalyzer()
        self.output_dir = Path("data/pipeline")
        self.data_dir = Path("data/funding_rates")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)

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
                # Step 1: Collect Funding Data
                console.print(Panel("🚀 Starting data collection pipeline", style="bold green"))
                
                # Get all markets first
                markets = await self.funding_collector.get_all_markets()
                if not markets:
                    raise Exception("No markets found")
                
                # Get predicted funding rates
                predicted_rates = await self.funding_collector.get_predicted_funding_rates()
                
                # Setup progress bar for market data collection
                total_markets = len(markets)
                task1 = progress.add_task(
                    "[cyan]Collecting market data...", 
                    total=total_markets,
                    remaining="calculating..."
                )
                
                # Collect funding data with time estimation
                results = []
                start_time = datetime.now()
                completed = 0
                
                for token in markets:
                    try:
                        data = await self.funding_collector.get_funding_data(token)
                        if data:
                            data['predicted_funding_rate'] = predicted_rates.get(token, 0)
                            results.append(data)
                        
                        # Update progress and estimate remaining time
                        completed += 1
                        progress.update(task1, advance=1)
                        
                        # Calculate estimated time remaining
                        if completed > 0:
                            elapsed = (datetime.now() - start_time).total_seconds()
                            avg_time_per_market = elapsed / completed
                            remaining_markets = total_markets - completed
                            est_remaining_seconds = avg_time_per_market * remaining_markets
                            est_remaining = str(timedelta(seconds=int(est_remaining_seconds)))
                            progress.update(task1, remaining=est_remaining)
                            
                    except Exception as e:
                        logger.warning(f"Error collecting data for {token}: {str(e)}")
                        progress.update(task1, advance=1)
                        continue

                if not results:
                    raise Exception("No funding data collected")

                # Save raw data
                raw_data_file = self.data_dir / f"funding_raw_{timestamp}.json"
                with open(raw_data_file, 'w') as f:
                    json.dump(results, f, indent=2)
                
                progress.update(task1, completed=total_markets)
                console.print(f"✅ Collected data for {len(results)} markets")

                # Step 2: Sync to Supabase
                task2 = progress.add_task(
                    "[cyan]Syncing to Supabase...", 
                    total=len(results),
                    remaining="calculating..."
                )
                
                await self.supabase_sync.sync_funding_rates({
                    'timestamp': datetime.now().isoformat(),
                    'all_markets': results
                })
                progress.update(task2, completed=len(results))
                console.print("✅ Data synced to Supabase")

                # Step 3: Run Analysis
                task3 = progress.add_task(
                    "[cyan]Analyzing funding rates...", 
                    total=100,
                    remaining="~30 seconds"
                )
                
                analysis = self.analyzer.generate_analysis()
                progress.update(task3, completed=100)
                
                # Save pipeline run summary
                summary = {
                    "timestamp": timestamp,
                    "markets_collected": len(results),
                    "analysis_generated": bool(analysis),
                    "sync_status": "completed",
                    "raw_data_file": str(raw_data_file)
                }
                
                summary_file = self.output_dir / f"pipeline_summary_{timestamp}.json"
                with open(summary_file, 'w') as f:
                    json.dump(summary, f, indent=2)

                console.print(Panel(
                    f"""✨ Pipeline completed successfully!
                    \n📊 Markets processed: {len(results)}
                    \n📝 Summary saved to: {summary_file}
                    \n📄 Raw data saved to: {raw_data_file}
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
                    "status": "failed"
                }
                
                with open(self.output_dir / f"pipeline_error_{timestamp}.json", 'w') as f:
                    json.dump(error_summary, f, indent=2)
                
                sys.exit(1)

def main():
    try:
        # Check environment variables
        required_vars = ['SUPABASE_URL', 'SUPABASE_KEY']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            raise Exception(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        pipeline = FundingPipeline()
        asyncio.run(pipeline.run_pipeline())
        
    except Exception as e:
        console.print(f"[red]Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 