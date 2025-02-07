import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import seaborn as sns
import matplotlib.pyplot as plt
from pathlib import Path
import logging
from datetime import datetime
from rich.console import Console
from rich.table import Table

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
console = Console()

class PerpDataVisualizer:
    def __init__(self, data_path="data/perp_data_*.csv"):
        """Initialize visualizer with latest data file"""
        try:
            # Get the most recent data file
            files = sorted(Path().glob(data_path), key=lambda x: x.stat().st_mtime)
            if not files:
                raise FileNotFoundError("No data files found")
            
            self.df = pd.read_csv(files[-1])
            self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
            logger.info(f"Loaded data from {files[-1]}")
            
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            raise

    def create_market_overview(self):
        """Create an interactive market overview dashboard"""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                "Funding Rates by Token",
                "24h Volume Comparison",
                "Open Interest Distribution",
                "Price Comparison"
            )
        )

        # Funding rates
        fig.add_trace(
            go.Bar(x=self.df['token'], y=self.df['funding_rate'] * 100,
                  name="Funding Rate (%)", marker_color='lightblue'),
            row=1, col=1
        )

        # Volume comparison
        fig.add_trace(
            go.Bar(x=self.df['token'], y=self.df['volume_24h'],
                  name="Perp Volume", marker_color='lightgreen'),
            row=1, col=2
        )
        fig.add_trace(
            go.Bar(x=self.df['token'], y=self.df['spot_volume_24h'],
                  name="Spot Volume", marker_color='lightpink'),
            row=1, col=2
        )

        # Open Interest
        fig.add_trace(
            go.Pie(labels=self.df['token'], values=self.df['open_interest'],
                  name="Open Interest"),
            row=2, col=1
        )

        # Price comparison
        fig.add_trace(
            go.Scatter(x=self.df['token'], y=self.df['mark_price'],
                      name="Mark Price", mode='lines+markers'),
            row=2, col=2
        )
        fig.add_trace(
            go.Scatter(x=self.df['token'], y=self.df['spot_price'],
                      name="Spot Price", mode='lines+markers'),
            row=2, col=2
        )

        fig.update_layout(
            height=800,
            title_text="Perpetuals Market Overview",
            showlegend=True
        )

        # Save the plot
        fig.write_html("visualizations/market_overview.html")
        logger.info("Market overview dashboard saved to visualizations/market_overview.html")

    def create_rich_table(self):
        """Create a rich CLI table with key metrics"""
        table = Table(title="Perpetuals Market Summary")
        
        columns = [
            ("Token", "cyan"),
            ("Mark Price", "green"),
            ("Funding Rate", "yellow"),
            ("24h Volume", "magenta"),
            ("Open Interest", "blue"),
            ("Holder Count", "red")
        ]
        
        for col, color in columns:
            table.add_column(col, style=color)

        for _, row in self.df.iterrows():
            table.add_row(
                row['token'],
                f"${row['mark_price']:.4f}",
                f"{row['funding_rate']:.2%}",
                f"${row['volume_24h']:,.0f}",
                f"${row['open_interest']:,.0f}",
                f"{row['holder_count']:,}"
            )

        console.print(table)

    def save_summary_stats(self):
        """Save summary statistics to a file"""
        summary = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'total_volume': self.df['volume_24h'].sum(),
            'total_open_interest': self.df['open_interest'].sum(),
            'avg_funding_rate': self.df['funding_rate'].mean(),
            'highest_volume_token': self.df.loc[self.df['volume_24h'].idxmax(), 'token'],
            'highest_oi_token': self.df.loc[self.df['open_interest'].idxmax(), 'token']
        }

        Path("visualizations").mkdir(exist_ok=True)
        with open("visualizations/summary_stats.txt", "w") as f:
            for key, value in summary.items():
                f.write(f"{key}: {value}\n")
        
        logger.info("Summary statistics saved to visualizations/summary_stats.txt")

def main():
    # Create visualizations directory
    Path("visualizations").mkdir(exist_ok=True)
    
    # Initialize visualizer
    visualizer = PerpDataVisualizer()
    
    # Generate all visualizations
    visualizer.create_market_overview()
    visualizer.create_rich_table()
    visualizer.save_summary_stats()
    
    logger.info("All visualizations generated successfully!")

if __name__ == "__main__":
    main() 