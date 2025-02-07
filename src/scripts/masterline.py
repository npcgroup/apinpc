import subprocess
import sys
import time
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.layout import Layout
from rich.live import Live
from rich.table import Table
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('PipelineRunner')

# Load environment variables
load_dotenv()

console = Console()

class PipelineRunner:
    def __init__(self):
        self.scripts = {
            'binance_market': {
                'command': [sys.executable, "scripts/binance_market_data.py"],
                'description': "🔄 Binance Market Data Collection",
                'interval': 300,
                'retry_count': 3,
                'retry_delay': 60,
                'dependencies': []
            },
            'hyperliquid_funding': {
                'command': [sys.executable, "scripts/push_hyperliquid_json_to_supabase.py"],
                'description': "🌀 Hyperliquid Funding Rates",
                'interval': 600,
                'retry_count': 3,
                'retry_delay': 60,
                'dependencies': []
            },
            'binance_funding': {
                'command': [sys.executable, "scripts/binance_funding_rates.py"],
                'description': "📈 Binance Funding Rates",
                'interval': 600,
                'retry_count': 3,
                'retry_delay': 60,
                'dependencies': []
            },
            'bybit_market': {
                'command': [sys.executable, "scripts/bybit_market_data.py"],
                'description': "📊 Bybit Market Data",
                'interval': 300,
                'retry_count': 3,
                'retry_delay': 60,
                'dependencies': []
            },
            'hl_funding': {
                'command': ["ts-node", "scripts/hl-funding.ts"],
                'description': "⚡ Hyperliquid Funding Analysis",
                'interval': 900,
                'retry_count': 3,
                'retry_delay': 60,
                'dependencies': ['hyperliquid_funding']
            },
            'advanced_analysis': {
                'command': [sys.executable, "scripts/advanced_funding_analyzer.py"],
                'description': "🧠 Advanced Funding Analyzer",
                'interval': 1200,
                'retry_count': 3,
                'retry_delay': 60,
                'dependencies': ['binance_funding', 'hl_funding']
            }
        }
        self.last_run: Dict[str, float] = {}
        self.error_counts: Dict[str, int] = {name: 0 for name in self.scripts}
        self.last_success: Dict[str, Optional[datetime]] = {name: None for name in self.scripts}

    def check_dependencies(self, script_name: str) -> bool:
        """Check if all dependencies for a script have run successfully"""
        dependencies = self.scripts[script_name]['dependencies']
        for dep in dependencies:
            if dep not in self.last_success or not self.last_success[dep]:
                return False
            if time.time() - self.last_success[dep].timestamp() > self.scripts[dep]['interval'] * 2:
                return False
        return True

    def run_script(self, name: str) -> bool:
        """Execute a single script with rich visualization and retry logic"""
        script = self.scripts[name]
        
        if not self.check_dependencies(name):
            logger.warning(f"Dependencies not met for {name}")
            return False

        for attempt in range(script['retry_count']):
            try:
                # Run the script without waiting for output
                process = subprocess.Popen(
                    script['command'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                # Set a timeout of 5 minutes
                try:
                    stdout, stderr = process.communicate(timeout=300)
                    if process.returncode == 0:
                        # Reset error count on success
                        self.error_counts[name] = 0
                        self.last_success[name] = datetime.now()
                        
                        logger.info(f"Successfully executed {name}")
                        return True
                    else:
                        raise subprocess.CalledProcessError(process.returncode, script['command'], stdout, stderr)
                        
                except subprocess.TimeoutExpired:
                    process.kill()
                    logger.error(f"Timeout executing {name}")
                    raise
                
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
                self.error_counts[name] += 1
                error_msg = e.stderr if hasattr(e, 'stderr') else str(e)
                logger.error(f"Error in {name} (attempt {attempt + 1}): {error_msg}")
                
                if attempt < script['retry_count'] - 1:
                    logger.info(f"Retrying {name} in {script['retry_delay']} seconds...")
                    time.sleep(script['retry_delay'])
                else:
                    return False

            except Exception as e:
                logger.error(f"Unexpected error in {name}: {str(e)}")
                return False

        return False

    def generate_status_table(self) -> Panel:
        """Generate enhanced status table with more details"""
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Script", style="cyan")
        table.add_column("Status", justify="center")
        table.add_column("Last Success", justify="right")
        table.add_column("Errors", justify="center")

        for name, config in self.scripts.items():
            last_run = self.last_run.get(name, 0)
            last_success_time = self.last_success[name].strftime('%H:%M:%S') if self.last_success[name] else 'Never'
            
            if time.time() - last_run < config['interval']:
                status = "[green]ACTIVE[/green]"
            elif self.error_counts[name] > 0:
                status = "[red]ERROR[/red]"
            else:
                status = "[yellow]PENDING[/yellow]"

            table.add_row(
                config['description'],
                status,
                last_success_time,
                f"[{'red' if self.error_counts[name] > 0 else 'green'}]{self.error_counts[name]}"
            )

        return Panel(table, title="🚀 Pipeline Status", border_style="blue")

    def run_pipeline(self):
        """Run the complete pipeline with interval management"""
        console.print(Panel(
            "[bold]Supabase Data Pipeline[/bold]\n"
            "Collecting and analyzing funding rates across exchanges\n"
            "Press Ctrl+C to exit",
            style="bold cyan"
        ))

        # Initialize the layout outside the Live context
        layout = Layout()
        layout.split(
            Layout(name="header", ratio=1),
            Layout(name="progress", ratio=1),
            Layout(name="main", ratio=4),
            Layout(name="footer", ratio=1)
        )

        try:
            with Live(layout, console=console, screen=True, refresh_per_second=4) as live:
                while True:
                    try:
                        current_time = time.strftime('%Y-%m-%d %H:%M:%S')
                        
                        # Update header
                        layout["header"].update(
                            Panel(f"[bold]Last Update: {current_time}[/bold]", 
                                title="�� Pipeline Status")
                        )

                        # Calculate overall pipeline progress
                        total_scripts = len(self.scripts)
                        completed_scripts = sum(
                            1 for name in self.scripts 
                            if self.last_success.get(name) and 
                            time.time() - self.last_success[name].timestamp() < self.scripts[name]['interval']
                        )
                        
                        # Create progress bar
                        progress_pct = (completed_scripts / total_scripts) * 100
                        progress_bar = "█" * int(progress_pct / 2) + "░" * (50 - int(progress_pct / 2))
                        
                        # Calculate next script to run
                        next_runs = [
                            (name, self.scripts[name]['interval'] - (time.time() - self.last_run.get(name, 0)))
                            for name in self.scripts
                        ]
                        next_script = min(next_runs, key=lambda x: x[1] if x[1] > 0 else float('inf'))
                        eta_seconds = max(0, next_script[1])
                        
                        # Update progress panel
                        layout["progress"].update(Panel(
                            f"[bold cyan]Pipeline Progress:[/bold cyan] [white]{progress_pct:.1f}%[/white]\n"
                            f"[blue]{progress_bar}[/blue]\n"
                            f"[white]Active Scripts: {completed_scripts}/{total_scripts}[/white]\n"
                            f"[dim]Next Script: {self.scripts[next_script[0]]['description']}[/dim]",
                            title=f"⏳ ETA: {int(eta_seconds // 60)}m {int(eta_seconds % 60)}s",
                            border_style="cyan"
                        ))

                        # Update main content with status table
                        layout["main"].update(self.generate_status_table())

                        # Update footer with next runs
                        next_scripts = sorted(
                            [(name, max(0, config['interval'] - (time.time() - self.last_run.get(name, 0))))
                             for name, config in self.scripts.items()],
                            key=lambda x: x[1]
                        )[:3]
                        
                        footer_text = "\n".join([
                            f"[dim]{self.scripts[name]['description']}: {int(wait)}s[/dim]"
                            for name, wait in next_scripts
                        ])
                        
                        layout["footer"].update(
                            Panel(footer_text, title="🔄 Upcoming Executions")
                        )

                        # Run scripts that need execution
                        current_time = time.time()
                        for name in self.scripts:
                            last_run = self.last_run.get(name, 0)
                            interval = self.scripts[name]['interval']
                            
                            if current_time - last_run >= interval:
                                if self.run_script(name):
                                    self.last_run[name] = current_time

                        # Force refresh
                        live.refresh()
                        
                        # Short sleep to prevent CPU overuse
                        time.sleep(0.25)

                    except Exception as e:
                        logger.error(f"Error in pipeline loop: {str(e)}", exc_info=True)
                        console.print(f"[red]Error in pipeline loop:[/red] {str(e)}")
                        time.sleep(1)

        except Exception as e:
            logger.error(f"Critical error in Live display: {str(e)}", exc_info=True)
            console.print(f"[red]Critical error in Live display:[/red] {str(e)}")

if __name__ == "__main__":
    try:
        runner = PipelineRunner()
        runner.run_pipeline()
    except KeyboardInterrupt:
        console.print("\n[yellow]Pipeline shutdown requested[/yellow] 🛑")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Critical error: {str(e)}", exc_info=True)
        console.print(f"[red]Critical error:[/red] {str(e)}")
        console.print("[red]Check pipeline.log for details[/red]")
        sys.exit(1)