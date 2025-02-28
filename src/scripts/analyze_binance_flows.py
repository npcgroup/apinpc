import pandas as pd
from datetime import datetime
import logging
from rich.console import Console
from rich.table import Table

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
console = Console()

def analyze_binance_flows(csv_path: str):
    """Analyze Binance CEX flows from DefiLlama CSV data"""
    try:
        # Read CSV file with low_memory=False to handle mixed types
        df = pd.read_csv(csv_path, low_memory=False)
        
        # Print column names to debug
        logger.info(f"Number of columns: {len(df.columns)}")
        
        # Convert Date column to datetime
        df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y')
        
        # Get the first "Binance CEX" column (which should contain the TVL)
        binance_col = 'Binance CEX'
        
        # Extract daily totals (TVL)
        daily_flows = df[['Date', binance_col]].copy()
        daily_flows.columns = ['Date', 'Total_USD']
        
        # Convert Total_USD to numeric, removing any non-numeric characters
        daily_flows['Total_USD'] = pd.to_numeric(
            daily_flows['Total_USD'].astype(str).str.replace(r'[^\d.-]', '', regex=True), 
            errors='coerce'
        )
        
        # Sort by date
        daily_flows = daily_flows.sort_values('Date')
        
        # Calculate daily change (inflow/outflow)
        daily_flows['Daily_Change'] = daily_flows['Total_USD'].diff()
        
        # Format output
        daily_flows['Date'] = daily_flows['Date'].dt.strftime('%Y-%m-%d')
        
        # Create a nice table for display
        table = Table(title="Binance CEX Daily Flows")
        table.add_column("Date", style="cyan")
        table.add_column("Flow Type", style="green")
        table.add_column("Amount (USD)", justify="right", style="yellow")
        table.add_column("Total TVL (USD)", justify="right", style="blue")
        
        # Display last 10 days of flows
        for _, row in daily_flows.tail(10).iterrows():
            if pd.notna(row['Daily_Change']):
                flow_type = "Inflow" if row['Daily_Change'] > 0 else "Outflow"
                table.add_row(
                    row['Date'],
                    flow_type,
                    f"${abs(row['Daily_Change']):,.2f}",
                    f"${row['Total_USD']:,.2f}"
                )
        
        console.print(table)
        
        # Print some statistics
        total_inflows = daily_flows[daily_flows['Daily_Change'] > 0]['Daily_Change'].sum()
        total_outflows = abs(daily_flows[daily_flows['Daily_Change'] < 0]['Daily_Change'].sum())
        
        print("\nSummary Statistics:")
        print(f"Total Inflows: ${total_inflows:,.2f}")
        print(f"Total Outflows: ${total_outflows:,.2f}")
        print(f"Net Flow: ${(total_inflows - total_outflows):,.2f}")
        
        return daily_flows
        
    except Exception as e:
        logger.error(f"Error analyzing Binance flows: {str(e)}")
        logger.exception("Full traceback:")
        return None

if __name__ == "__main__":
    csv_path = "data/defillama/binance-cex.csv"
    flows = analyze_binance_flows(csv_path)
    
    if flows is not None:
        # Save to CSV
        output_path = "data/defillama/binance_daily_flows.csv"
        flows.to_csv(output_path, index=False)
        print(f"\nResults saved to: {output_path}") 