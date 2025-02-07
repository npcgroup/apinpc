import subprocess
import time
import signal
import sys
import logging
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
console = Console()

class HyperliquidPipeline:
    def __init__(self):
        self.funding_rates_process = None
        self.scripts_dir = Path('scripts')
        self.wait_time = 300  # 5 minutes in seconds
        
    def start_funding_rates(self):
        """Start the hyperliquid funding rates script"""
        try:
            console.print("[cyan]Starting Hyperliquid funding rates collection...[/cyan]")
            
            # Start the funding rates script
            self.funding_rates_process = subprocess.Popen(
                [sys.executable, str(self.scripts_dir / 'hyperliquid_funding_rates.py')],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            console.print(Panel(
                "✅ Hyperliquid funding rates collection started",
                style="bold green"
            ))
            return True
            
        except Exception as e:
            console.print(Panel(
                f"❌ Failed to start funding rates collection: {str(e)}",
                style="bold red"
            ))
            return False

    def stop_funding_rates(self):
        """Stop the hyperliquid funding rates script"""
        if self.funding_rates_process:
            try:
                console.print("[cyan]Stopping Hyperliquid funding rates collection...[/cyan]")
                
                # Send SIGTERM signal to the process
                self.funding_rates_process.terminate()
                
                # Wait for the process to terminate
                self.funding_rates_process.wait(timeout=10)
                
                console.print(Panel(
                    "✅ Hyperliquid funding rates collection stopped",
                    style="bold green"
                ))
                return True
                
            except subprocess.TimeoutExpired:
                # Force kill if process doesn't terminate
                self.funding_rates_process.kill()
                console.print("[yellow]Had to force kill the funding rates process[/yellow]")
                return True
                
            except Exception as e:
                console.print(Panel(
                    f"❌ Error stopping funding rates collection: {str(e)}",
                    style="bold red"
                ))
                return False

    def push_to_supabase(self):
        """Run the push to Supabase script"""
        try:
            console.print("[cyan]Pushing data to Supabase...[/cyan]")
            
            # Run the push script
            result = subprocess.run(
                [sys.executable, str(self.scripts_dir / 'push_hyperliquid_json_to_supabase.py')],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                console.print(Panel(
                    "✅ Successfully pushed data to Supabase",
                    style="bold green"
                ))
                return True
            else:
                console.print(Panel(
                    f"❌ Error pushing to Supabase:\n{result.stderr}",
                    style="bold red"
                ))
                return False
                
        except Exception as e:
            console.print(Panel(
                f"❌ Error running Supabase push script: {str(e)}",
                style="bold red"
            ))
            return False

    def run_pipeline(self):
        """Run the complete pipeline"""
        try:
            while True:
                # Start funding rates collection
                if not self.start_funding_rates():
                    raise Exception("Failed to start funding rates collection")
                
                # Let it run for a minute to collect data
                time.sleep(60)
                
                # Stop funding rates collection
                if not self.stop_funding_rates():
                    raise Exception("Failed to stop funding rates collection")
                
                # Push data to Supabase
                if not self.push_to_supabase():
                    logger.warning("Failed to push data to Supabase")
                
                # Wait before next cycle
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    TimeElapsedColumn(),
                    console=console
                ) as progress:
                    task = progress.add_task(
                        "[cyan]Waiting for next cycle...",
                        total=self.wait_time
                    )
                    
                    while not progress.finished:
                        time.sleep(1)
                        progress.update(task, advance=1)
                
                console.print(f"\n[green]Starting new cycle at {datetime.now()}[/green]\n")
                
        except KeyboardInterrupt:
            console.print("\n[yellow]Pipeline interrupted by user[/yellow]")
            self.stop_funding_rates()
            sys.exit(0)
            
        except Exception as e:
            console.print(Panel(
                f"❌ Pipeline error: {str(e)}",
                style="bold red"
            ))
            self.stop_funding_rates()
            sys.exit(1)

def main():
    try:
        pipeline = HyperliquidPipeline()
        
        console.print(Panel(
            "🚀 Starting Hyperliquid Pipeline\n"
            "This will:\n"
            "1. Run funding rates collection\n"
            "2. Push data to Supabase\n"
            "3. Wait 5 minutes\n"
            "4. Repeat\n\n"
            "Press Ctrl+C to stop",
            style="bold cyan"
        ))
        
        pipeline.run_pipeline()
        
    except Exception as e:
        console.print(Panel(
            f"❌ Fatal error: {str(e)}",
            style="bold red"
        ))
        sys.exit(1)

if __name__ == "__main__":
    main() 