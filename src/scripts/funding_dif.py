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
import os
from supabase import create_client, Client

url: str = os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
key: str = os.environ.get("NEXT_PUBLIC_SUPABASE_KEY")
supabase: Client = create_client(url, key)


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
            response = (
                self.supabase.schema('public')
                .table('funding_market_snapshots')
                .select("symbol,exchange,funding_rate,created_at")  # Only select needed columns
                .gte('created_at', start_date)
                .lte('created_at', end_date)
                .execute()
            )
            
            df = pd.DataFrame(response.data)
            if not df.empty:
                df['created_at'] = pd.to_datetime(df['created_at'])
                logger.info(f"Fetched {len(df)} funding records")
                logger.info(f"Unique symbols: {df['symbol'].nunique()}")
                logger.info(f"Exchanges found: {df['exchange'].unique()}")
            return df
        except Exception as e:
            logger.error(f"Error fetching funding data: {e}")
            return pd.DataFrame()

    def fetch_price_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch price data from crypto_historical.price_history table"""
        try:
            logger.info(f"Fetching price data from {start_date} to {end_date}")
            
            # Query using schema method with correct column names
            response = (
                supabase.schema("crypto_historical")
                .table("price_history")
                .select("symbol,close,datetime")
                .gte('datetime', start_date)
                .lte('datetime', end_date)
                .execute()
            )
            
            df = pd.DataFrame(response.data)
            if not df.empty:
                logger.info(f"Retrieved {len(df)} price records")
                # Debug info
                logger.info(f"Sample of symbols: {df['symbol'].unique()[:5]}")
                logger.info(f"Date range: {df['datetime'].min()} to {df['datetime'].max()}")
                
                df['timestamp'] = pd.to_datetime(df['datetime'])
                df['price'] = df['close']
                
                # Ensure data quality
                df = df.dropna(subset=['price', 'timestamp'])
                df = df.sort_values('timestamp')
                df = df.drop_duplicates(subset=['symbol', 'timestamp'], keep='last')
                
                # More debug info
                logger.info(f"After cleaning: {len(df)} records")
                logger.info(f"Unique symbols: {df['symbol'].nunique()}")
                
                return df[['symbol', 'timestamp', 'price']]
            else:
                logger.warning("No price data found for the specified period")
                return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Error fetching price data: {e}")
            return pd.DataFrame()

    def calculate_funding_differential(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate funding rate differential between Binance and Hyperliquid"""
        try:
            # First, ensure we have the required columns
            required_columns = ['symbol', 'exchange', 'funding_rate', 'created_at']
            if not all(col in df.columns for col in required_columns):
                logger.error(f"Missing required columns. Found: {df.columns.tolist()}")
                return pd.DataFrame()

            # Pivot the data to get Binance and Hyperliquid rates side by side
            pivot_df = df.pivot_table(
                index=['symbol', 'created_at'],
                columns='exchange',
                values='funding_rate'
            ).reset_index()

            # Check if we have both exchanges
            if 'Binance' not in pivot_df.columns or 'Hyperliquid' not in pivot_df.columns:
                logger.error(f"Missing exchange data. Found exchanges: {pivot_df.columns.tolist()}")
                return pd.DataFrame()

            # Calculate differential
            pivot_df['funding_differential'] = pivot_df['Binance'] - pivot_df['Hyperliquid']
            pivot_df['funding_differential_pct'] = pivot_df['funding_differential'] * 100
            pivot_df['differential_direction'] = np.where(
                pivot_df['funding_differential'] > 0,
                'Binance_Higher',
                'Hyperliquid_Higher'
            )
            
            logger.info(f"Calculated differentials for {len(pivot_df)} records")
            return pivot_df
        except Exception as e:
            logger.error(f"Error calculating funding differential: {e}")
            return pd.DataFrame()

    def calculate_price_performance(self, price_df: pd.DataFrame, funding_df: pd.DataFrame) -> Dict:
        """Calculate price performance for different time windows"""
        try:
            results = {}
            
            # Debug info for data ranges and symbols
            logger.info("=== Data Overview ===")
            logger.info(f"Price data time range: {price_df['timestamp'].min()} to {price_df['timestamp'].max()}")
            logger.info(f"Funding data time range: {funding_df['created_at'].min()} to {funding_df['created_at'].max()}")
            
            # Pre-process price data
            price_df = price_df.set_index(['symbol', 'timestamp']).sort_index()
            
            for window in self.price_windows:
                performance_data = []
                window_delta = pd.Timedelta(hours=window)
                
                for _, row in funding_df.iterrows():
                    try:
                        symbol = row['symbol']
                        timestamp = row['created_at']
                        end_timestamp = timestamp + window_delta
                        
                        if symbol not in price_df.index.get_level_values('symbol'):
                            continue
                        
                        # Get price data for the window
                        symbol_prices = price_df.loc[symbol]
                        mask = (symbol_prices.index >= timestamp) & (symbol_prices.index <= end_timestamp)
                        window_prices = symbol_prices.loc[mask]
                        
                        if len(window_prices) >= 2:  # Need at least 2 price points
                            start_price = window_prices['price'].iloc[0]
                            end_price = window_prices['price'].iloc[-1]
                            price_change = ((end_price - start_price) / start_price) * 100
                            
                            performance_data.append({
                                'symbol': symbol,
                                'timestamp': timestamp,
                                'funding_differential': row['funding_differential'],
                                'funding_differential_pct': row['funding_differential_pct'],
                                'differential_direction': row['differential_direction'],
                                'price_change': price_change,
                                'start_price': start_price,
                                'end_price': end_price
                            })
                            
                    except Exception as e:
                        logger.debug(f"Error processing {symbol} for window {window}h: {e}")
                        continue
                
                if performance_data:
                    results[f'{window}h'] = pd.DataFrame(performance_data)
                    logger.info(f"Window {window}h: Created DataFrame with {len(performance_data)} records")
            
            return results
        except Exception as e:
            logger.error(f"Error calculating price performance: {e}")
            return {}

    def analyze_extreme_differentials(self, results: Dict, threshold: float = 1.0) -> Dict:
        """Analyze price performance for extreme funding differentials"""
        analysis = {}
        
        for window, df in results.items():
            try:
                # Use funding_differential_pct for threshold comparison
                extreme_df = df[abs(df['funding_differential_pct']) > threshold].copy()
                
                if extreme_df.empty:
                    logger.warning(f"No extreme differentials found for window {window}")
                    continue
                    
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
                    extreme_df['funding_differential_pct'],
                    extreme_df['price_change']
                )
                analysis[window]['correlation'] = {
                    'coefficient': correlation[0],
                    'p_value': correlation[1]
                }
                
                logger.info(f"Window {window}: Analyzed {len(extreme_df)} extreme differential records")
                
            except Exception as e:
                logger.error(f"Error analyzing window {window}: {e}")
                continue
        
        return analysis

    def visualize_results(self, results: Dict, threshold: float = 1.0):
        """Create visualizations for the analysis"""
        try:
            for window, df in results.items():
                if df.empty:
                    logger.warning(f"No data to visualize for window {window}")
                    continue
                    
                # Filter for extreme differentials using funding_differential_pct
                extreme_df = df[abs(df['funding_differential_pct']) > threshold].copy()
                
                if extreme_df.empty:
                    logger.warning(f"No extreme differentials to visualize for window {window}")
                    continue
                
                # Scatter plot
                fig = px.scatter(
                    extreme_df,
                    x='funding_differential_pct',  # Use percentage for visualization
                    y='price_change',
                    color='differential_direction',
                    title=f'Funding Differential vs Price Change ({window})',
                    labels={
                        'funding_differential_pct': 'Funding Rate Differential (%)',
                        'price_change': 'Price Change (%)'
                    }
                )
                
                # Add trend line
                fig.add_trace(go.Scatter(
                    x=extreme_df['funding_differential_pct'],
                    y=np.poly1d(np.polyfit(extreme_df['funding_differential_pct'], 
                                         extreme_df['price_change'], 1))(extreme_df['funding_differential_pct']),
                    mode='lines',
                    name='Trend Line'
                ))
                
                fig.show()
        except Exception as e:
            logger.error(f"Error visualizing results: {e}")

    def run_analysis(self, start_date: str, end_date: str, threshold: float = 1.0):
        """Run the complete analysis pipeline"""
        try:
            logger.info("Fetching data...")
            # Fetch funding data first
            funding_df = self.fetch_funding_data(start_date, end_date)
            
            if funding_df.empty:
                logger.error("No funding data available")
                return
            
            # Extend price data fetch window to ensure coverage
            price_start = (pd.to_datetime(start_date) - pd.Timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
            price_end = (pd.to_datetime(end_date) + pd.Timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
            
            price_df = self.fetch_price_data(price_start, price_end)
            
            if price_df.empty:
                logger.error("No price data available")
                return
            
            logger.info(f"Found {len(funding_df)} funding records")
            logger.info(f"Found {len(price_df)} price records")
            
            # Calculate funding differentials
            logger.info("Calculating funding differentials...")
            differential_df = self.calculate_funding_differential(funding_df)
            
            if differential_df.empty:
                logger.error("Could not calculate funding differentials")
                return
            
            # Filter price data to match symbols in funding data
            valid_symbols = differential_df['symbol'].unique()
            price_df = price_df[price_df['symbol'].isin(valid_symbols)]
            
            logger.info("Calculating price performance...")
            results = self.calculate_price_performance(price_df, differential_df)
            
            if not results:
                logger.error("Could not calculate price performance")
                return
            
            logger.info("Analyzing extreme differentials...")
            analysis = self.analyze_extreme_differentials(results, threshold)
            
            logger.info("Generating visualizations...")
            self.visualize_results(results, threshold)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in run_analysis: {e}")
            return None

def main():
    analyzer = FundingDifferentialAnalyzer()
    
    # Set date range to match available data
    end_date = datetime(2025, 2, 14, 21, 0, tzinfo=timezone.utc)  # Latest data point
    start_date = end_date - timedelta(days=7)  # Get 7 days of data
    
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