import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from supabase import create_client
import os
from dotenv import load_dotenv
import logging
from typing import Dict, List, Tuple
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FundingDifferentialAnalyzer:
    def __init__(self):
        load_dotenv()
        self.supabase = create_client(
            os.getenv("NEXT_PUBLIC_SUPABASE_URL"),
            os.getenv("NEXT_PUBLIC_SUPABASE_KEY")
        )
        self.price_windows = [1, 4, 8, 24]  # hours to analyze

    def fetch_funding_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch funding rate data from Supabase"""
        try:
            response = (self.supabase.table('funding_market_snapshots')
                .select("*")
                .gte('created_at', start_date)
                .lte('created_at', end_date)
                .execute())
            
            df = pd.DataFrame(response.data)
            df['created_at'] = pd.to_datetime(df['created_at'])
            return df
        except Exception as e:
            logger.error(f"Error fetching funding data: {e}")
            return pd.DataFrame()

    def fetch_price_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch price data from Supabase using binance_market_data table"""
        try:
            # Convert to UTC timestamp in milliseconds
            start_timestamp = int(pd.Timestamp(start_date).tz_localize('UTC').timestamp() * 1000)
            end_timestamp = int(pd.Timestamp(end_date).tz_localize('UTC').timestamp() * 1000)
            
            logger.info(f"Fetching price data from {start_date} to {end_date}")
            logger.info(f"Timestamps: {start_timestamp} to {end_timestamp}")
            
            response = (self.supabase.table('binance_market_data')
                .select("symbol,mark_price,timestamp,datetime")
                .gte('timestamp', start_timestamp)
                .lte('timestamp', end_timestamp)
                .execute())
            
            df = pd.DataFrame(response.data)
            if not df.empty:
                logger.info(f"Retrieved {len(df)} price records")
                df['timestamp'] = pd.to_datetime(df['datetime'])  # Use datetime column
                df['price'] = df['mark_price']  # Map mark_price to price for compatibility
                
                # Keep only required columns
                df = df[['symbol', 'timestamp', 'price']]
            
                return df
            else:
                logger.warning("No price data found for the specified period")
                return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Error fetching price data: {e}")
            return pd.DataFrame()

    def calculate_funding_differential(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate funding rate differential between Binance and Hyperliquid"""
        try:
            # Pivot the data to get Binance and Hyperliquid rates side by side
            pivot_df = df.pivot_table(
                index=['symbol', 'created_at'],
                columns='exchange',
                values='funding_rate'
            ).reset_index()

            # Calculate differential
            pivot_df['funding_differential'] = pivot_df['Binance'] - pivot_df['Hyperliquid']
            pivot_df['funding_differential_pct'] = (pivot_df['funding_differential'] * 100)
            pivot_df['differential_direction'] = np.where(
                pivot_df['funding_differential'] > 0,
                'Binance_Higher',
                'Hyperliquid_Higher'
            )
            
            return pivot_df
        except Exception as e:
            logger.error(f"Error calculating funding differential: {e}")
            return pd.DataFrame()

    def calculate_price_performance(self, price_df: pd.DataFrame, funding_df: pd.DataFrame) -> Dict:
        """Calculate price performance for different time windows"""
        try:
            results = {}
            
            for window in self.price_windows:
                performance_data = []
                
                for _, row in funding_df.iterrows():
                    symbol = row['symbol']
                    timestamp = row['created_at']
                    
                    # Get price data for the window
                    future_prices = price_df[
                        (price_df['symbol'] == symbol) &
                        (price_df['timestamp'] >= timestamp) &
                        (price_df['timestamp'] <= timestamp + pd.Timedelta(hours=window))
                    ]['price'].values
                    
                    if len(future_prices) >= 2:
                        start_price = future_prices[0]
                        end_price = future_prices[-1]
                        price_change = ((end_price - start_price) / start_price) * 100
                        
                        performance_data.append({
                            'symbol': symbol,
                            'timestamp': timestamp,
                            'funding_differential': row['funding_differential'],
                            'differential_direction': row['differential_direction'],
                            'price_change': price_change
                        })
                
                results[f'{window}h'] = pd.DataFrame(performance_data)
            
            return results
        except Exception as e:
            logger.error(f"Error calculating price performance: {e}")
            return {}

    def analyze_extreme_differentials(self, results: Dict, threshold: float = 1.0) -> Dict:
        """Analyze price performance for extreme funding differentials"""
        analysis = {}
        
        for window, df in results.items():
            extreme_df = df[abs(df['funding_differential'] * 100) > threshold].copy()
            
            analysis[window] = {
                'overall': {
                    'mean_return': extreme_df['price_change'].mean(),
                    'median_return': extreme_df['price_change'].median(),
                    'std_return': extreme_df['price_change'].std(),
                    'sample_size': len(extreme_df)
                },
                'by_direction': extreme_df.groupby('differential_direction').agg({
                    'price_change': ['mean', 'median', 'std', 'count']
                }).round(4).to_dict()
            }
            
            # Calculate correlation
            correlation = stats.pearsonr(
                extreme_df['funding_differential'],
                extreme_df['price_change']
            )
            analysis[window]['correlation'] = {
                'coefficient': correlation[0],
                'p_value': correlation[1]
            }
        
        return analysis

    def visualize_results(self, results: Dict, threshold: float = 1.0):
        """Create visualizations for the analysis"""
        for window, df in results.items():
            # Filter for extreme differentials
            extreme_df = df[abs(df['funding_differential'] * 100) > threshold].copy()
            
            # Scatter plot
            fig = px.scatter(
                extreme_df,
                x='funding_differential',
                y='price_change',
                color='differential_direction',
                title=f'Funding Differential vs Price Change ({window})',
                labels={
                    'funding_differential': 'Funding Rate Differential (%)',
                    'price_change': 'Price Change (%)'
                }
            )
            
            # Add trend line
            fig.add_trace(go.Scatter(
                x=extreme_df['funding_differential'],
                y=np.poly1d(np.polyfit(extreme_df['funding_differential'], 
                                     extreme_df['price_change'], 1))(extreme_df['funding_differential']),
                mode='lines',
                name='Trend Line'
            ))
            
            fig.show()

    def run_analysis(self, start_date: str, end_date: str, threshold: float = 1.0):
        """Run the complete analysis pipeline"""
        logger.info("Fetching data...")
        funding_df = self.fetch_funding_data(start_date, end_date)
        price_df = self.fetch_price_data(start_date, end_date)
        
        if funding_df.empty or price_df.empty:
            logger.error("No data available for analysis")
            return
        
        logger.info("Calculating funding differentials...")
        differential_df = self.calculate_funding_differential(funding_df)
        
        logger.info("Calculating price performance...")
        results = self.calculate_price_performance(price_df, differential_df)
        
        logger.info("Analyzing extreme differentials...")
        analysis = self.analyze_extreme_differentials(results, threshold)
        
        logger.info("Generating visualizations...")
        self.visualize_results(results, threshold)
        
        return analysis

def main():
    analyzer = FundingDifferentialAnalyzer()
    
    # Set specific date range where data is available
    start_date = datetime(2025, 1, 21, tzinfo=timezone.utc)  # Start from Jan 21, 2025
    end_date = datetime(2025, 1, 27, tzinfo=timezone.utc)    # End at Jan 27, 2025
    
    logger.info(f"Analyzing data from {start_date} to {end_date}")
    
    analysis = analyzer.run_analysis(
        start_date.strftime("%Y-%m-%d %H:%M:%S"),
        end_date.strftime("%Y-%m-%d %H:%M:%S"),
        threshold=1.0  # 100% funding rate differential threshold
    )
    
    if analysis:
        logger.info("\nAnalysis Results:")
        for window, stats in analysis.items():
            print(f"\n=== {window} Window ===")
            print(f"Overall Mean Return: {stats['overall']['mean_return']:.2f}%")
            print(f"Sample Size: {stats['overall']['sample_size']}")
            print(f"Correlation Coefficient: {stats['correlation']['coefficient']:.4f}")
            print(f"P-value: {stats['correlation']['p_value']:.4f}")
            
            print("\nBy Direction:")
            for direction, metrics in stats['by_direction'].items():
                print(f"\n{direction}:")
                print(f"Mean Return: {metrics['mean']:.2f}%")
                print(f"Sample Size: {metrics['count']}")

if __name__ == "__main__":
    main()
