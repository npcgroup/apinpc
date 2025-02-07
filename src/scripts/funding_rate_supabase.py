import os
from datetime import datetime, timezone
import asyncio
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv
from advanced_funding_analyzer import AdvancedFundingAnalyzer
from rich.console import Console
import io
from contextlib import redirect_stdout
import logging

# Setup logging and console
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
console = Console()

class FundingRateSupabase:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Initialize Supabase client with service role key
        supabase_url = os.getenv('NEXT_PUBLIC_SUPABASE_URL')
        supabase_key = os.getenv('NEXT_PUBLIC_SUPABASE_KEY')  # Changed to use service role key
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables are required")
        
        self.supabase: Client = create_client(
            supabase_url,
            supabase_key
        )
        
        # Initialize analyzers
        self.analyzer = AdvancedFundingAnalyzer()

    def capture_analyzer_output(self):
        """Capture both the console output and DataFrame from the analyzer"""
        output = io.StringIO()
        with redirect_stdout(output):
            df = self.analyzer.analyze_funding_opportunities()
            if not df.empty:
                self.analyzer.display_results(df)
        return output.getvalue(), df

    async def store_funding_analysis(self, df: pd.DataFrame, analysis_output: str):
        """Store the complete funding analysis"""
        try:
            timestamp = datetime.now(timezone.utc)
            
            # Store raw funding rates
            funding_rates = [{
                'timestamp': timestamp.isoformat(),
                'exchange': row['exchange'],
                'symbol': row['symbol'],
                'funding_rate': float(row['funding_rate']),
                'predicted_rate': float(row['predicted_rate']),
                'annualized_rate': float(row['annualized_rate']),
                'mark_price': float(row['mark_price']),
                'next_funding_time': row['next_funding_time'].isoformat(),
                'payment_interval': int(row['payment_interval'])
            } for _, row in df.iterrows()]
            
            # Store the raw rates
            console.print("\n[yellow]Storing funding rates...[/yellow]")
            self.supabase.table('funding_rates').insert(funding_rates).execute()
            console.print("[green]✓ Stored funding rates[/green]")

            # Process and store arbitrage opportunities
            comparison_df = self.analyzer._prepare_comparison_data(df)
            if not comparison_df.empty:
                opportunities = []
                for _, row in comparison_df.head(10).iterrows():
                    opp = {
                        'timestamp': timestamp.isoformat(),
                        'symbol': row['Symbol'],
                        'binance_rate': float(row['Binance Rate']),
                        'binance_predicted': float(row['Binance Pred.']),
                        'binance_annual': float(row['Binance Ann.%']),
                        'hl_rate': float(row['HL Rate']),
                        'hl_predicted': float(row['HL Pred.']),
                        'hl_annual': float(row['HL Ann.%']),
                        'spread': float(row['Spread']),
                        'strategy': 'Long Binance/Short HL' if row['Binance Rate'] < row['HL Rate'] else 'Long HL/Short Binance',
                        'confidence': 'High' if abs(float(row['Spread'])) > 0.0005 else 'Medium'
                    }
                    opportunities.append(opp)

                # Store arbitrage opportunities
                console.print("\n[yellow]Storing arbitrage opportunities...[/yellow]")
                self.supabase.table('funding_arbitrage_opportunities').insert(opportunities).execute()
                console.print("[green]✓ Stored arbitrage opportunities[/green]")

            # Store analysis summary
            summary = {
                'timestamp': timestamp.isoformat(),
                'total_markets': len(df),
                'avg_funding_rate': float(df['funding_rate'].mean()),
                'median_funding_rate': float(df['funding_rate'].median()),
                'highest_rate': float(df['funding_rate'].max()),
                'lowest_rate': float(df['funding_rate'].min()),
                'analysis_output': analysis_output,
                'total_opportunities': len(opportunities) if not comparison_df.empty else 0
            }

            console.print("\n[yellow]Storing analysis summary...[/yellow]")
            self.supabase.table('funding_analysis_summary').insert([summary]).execute()
            console.print("[green]✓ Stored analysis summary[/green]")

            return True

        except Exception as e:
            logger.error(f"Error storing funding analysis: {e}")
            return False

    async def run_pipeline(self):
        """Run the complete analysis and storage pipeline"""
        try:
            console.print("\n[cyan]Starting funding analysis pipeline...[/cyan]")
            
            # Run analyzer and capture output
            console.print("\n[yellow]Running funding analysis...[/yellow]")
            analysis_output, df = self.capture_analyzer_output()
            
            if df.empty:
                raise ValueError("No funding rate data available")
            
            # Store all data
            success = await self.store_funding_analysis(df, analysis_output)
            
            if success:
                console.print("\n[green]✓ Analysis pipeline completed successfully[/green]")
                console.print("\nAnalysis Output:")
                console.print(analysis_output)
            else:
                console.print("\n[red]× Failed to store analysis data[/red]")

        except Exception as e:
            console.print(f"[red]Error in pipeline: {str(e)}[/red]")
            raise

async def main():
    """Run the funding rate analysis and storage pipeline"""
    try:
        analyzer = FundingRateSupabase()
        await analyzer.run_pipeline()
    except Exception as e:
        console.print(f"[red]Fatal error in main execution: {str(e)}[/red]")

if __name__ == "__main__":
    asyncio.run(main()) 