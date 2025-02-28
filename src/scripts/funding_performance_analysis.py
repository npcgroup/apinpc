import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, timezone
from supabase import create_client
import os
from dotenv import load_dotenv
import logging
from typing import Dict, Tuple
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FundingPerformanceAnalyzer:
    def __init__(self):
        load_dotenv()
        self.supabase = create_client(
            os.getenv("NEXT_PUBLIC_SUPABASE_URL"),
            os.getenv("NEXT_PUBLIC_SUPABASE_KEY")
        )
        self.windows = [1, 4, 8, 24]  # hours to analyze

    def fetch_historical_picks(self, weeks: int = 8) -> pd.DataFrame:
        """Fetch and process funding rates with proper daily averaging"""
        try:
            # Get the full date range available in the database
            response_range = (
                self.supabase.table('funding_market_snapshots')
                .select('created_at')
                .order('created_at')  # For ascending order
                .limit(1)
                .execute()
            )
            
            if not response_range.data:
                logger.error("No data found in database")
                return pd.DataFrame()
            
            earliest_available = pd.to_datetime(response_range.data[0]['created_at'])
            
            # Get latest timestamp
            response_latest = (
                self.supabase.table('funding_market_snapshots')
                .select('created_at')
                .order('created_at', desc=True)  # For descending order
                .limit(1)
                .execute()
            )
            
            latest_timestamp = pd.to_datetime(response_latest.data[0]['created_at'])
            
            # Debug timestamps
            logger.info(f"Earliest available: {earliest_available}")
            logger.info(f"Latest available: {latest_timestamp}")
            
            # Use the longer of: available data range or requested weeks
            start_date = min(
                earliest_available,
                latest_timestamp - timedelta(weeks=weeks)
            )
            
            logger.info(f"Fetching data from {start_date} to {latest_timestamp}")
            logger.info(f"Total days: {(latest_timestamp - start_date).days}")
            
            # Fetch all data for the period in chunks to handle large datasets
            all_data = []
            current_start = start_date
            chunk_size = timedelta(days=7)
            
            while current_start < latest_timestamp:
                current_end = min(current_start + chunk_size, latest_timestamp)
                
                response = (
                    self.supabase.table('funding_market_snapshots')
                    .select("*")
                    .gte('created_at', current_start.isoformat())
                    .lt('created_at', current_end.isoformat())
                    .execute()
                )
                
                if response.data:
                    chunk_df = pd.DataFrame(response.data)
                    all_data.append(chunk_df)
                    logger.info(f"Fetched chunk: {len(chunk_df)} records from {current_start} to {current_end}")
                
                current_start = current_end
            
            if not all_data:
                logger.error("No data retrieved")
                return pd.DataFrame()
            
            df = pd.concat(all_data, ignore_index=True)
            
            # Debug info
            logger.info(f"Retrieved {len(df)} total records")
            logger.info(f"Date range in data: {df['created_at'].min()} to {df['created_at'].max()}")
            
            # Convert timestamps and numeric columns
            df['created_at'] = pd.to_datetime(df['created_at'])
            df['funding_rate'] = pd.to_numeric(df['funding_rate'], errors='coerce')
            df['opportunity_score'] = pd.to_numeric(df['opportunity_score'], errors='coerce')
            
            # Process each symbol-exchange pair
            all_daily_data = []
            
            for (symbol, exchange), group in df.groupby(['symbol', 'exchange']):
                # Create daily resampled data with proper timezone handling
                daily_data = (
                    group.set_index('created_at')
                    .tz_localize(None)  # Remove timezone for resampling
                    .resample('D')
                    .agg({
                        'funding_rate': 'mean',
                        'opportunity_score': 'mean',
                        'symbol': 'first',
                        'exchange': 'first',
                        'suggested_position': lambda x: x.mode().iloc[0] if not x.empty else None
                    })
                    .reset_index()
                )
                
                # Handle missing data
                daily_data['funding_rate'] = (
                    daily_data['funding_rate']
                    .fillna(method='ffill', limit=2)  # Forward fill up to 2 days
                    .fillna(method='bfill', limit=2)  # Back fill up to 2 days
                    .interpolate(method='linear', limit=3)  # Interpolate remaining gaps
                )
                
                # Only keep rows with valid funding rates
                daily_data = daily_data.dropna(subset=['funding_rate'])
                
                if not daily_data.empty:
                    all_daily_data.append(daily_data)
            
            if all_daily_data:
                result_df = pd.concat(all_daily_data, ignore_index=True)
                
                # Log data quality metrics
                logger.info("\nDaily Data Statistics:")
                logger.info(f"Total daily records: {len(result_df)}")
                logger.info(f"Unique symbols: {result_df['symbol'].nunique()}")
                logger.info(f"Date range: {result_df['created_at'].min().date()} to {result_df['created_at'].max().date()}")
                logger.info(f"Days covered: {result_df['created_at'].dt.date.nunique()}")
                logger.info(f"Average records per day: {len(result_df)/result_df['created_at'].dt.date.nunique():.1f}")
                logger.info(f"Average daily funding rate range: {result_df['funding_rate'].min():.4f} to {result_df['funding_rate'].max():.4f}")
                
                # Calculate completeness for each symbol-exchange pair
                completeness = (
                    result_df.groupby(['symbol', 'exchange'])
                    .agg({'created_at': lambda x: len(x.dt.date.unique())})
                    .assign(coverage_pct=lambda x: (x['created_at'] / (latest_timestamp - start_date).days) * 100)
                )
                
                logger.info("\nData Completeness:")
                logger.info(f"Average coverage: {completeness['coverage_pct'].mean():.1f}%")
                logger.info(f"Symbols with >90% coverage: {len(completeness[completeness['coverage_pct'] > 90])}")
                
                return result_df
                
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Error fetching historical picks: {e}")
            logger.exception("Detailed error:")
            return pd.DataFrame()

    def fetch_price_data(self, symbols: list, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch price data for given symbols"""
        try:
            response = (
                self.supabase.schema("crypto_historical")
                .table("price_history")
                .select("symbol,close,datetime")
                .in_('symbol', symbols)
                .gte('datetime', start_date)
                .lte('datetime', end_date)
                .execute()
            )
            
            df = pd.DataFrame(response.data)
            if not df.empty:
                # Convert to datetime and ensure UTC timezone
                df['timestamp'] = pd.to_datetime(df['datetime'])
                # If timestamp is naive, localize to UTC
                if df['timestamp'].dt.tz is None:
                    df['timestamp'] = df['timestamp'].dt.tz_localize('UTC')
                # If timestamp has different timezone, convert to UTC
                else:
                    df['timestamp'] = df['timestamp'].dt.tz_convert('UTC')
                    
                df['price'] = df['close']
                
                logger.info(f"Fetched {len(df)} price records for {len(symbols)} symbols")
                logger.info(f"Price data range: {df['timestamp'].min()} to {df['timestamp'].max()}")
                
                return df[['symbol', 'timestamp', 'price']]
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Error fetching price data: {e}")
            logger.exception("Detailed error:")
            return pd.DataFrame()

    def calculate_returns(self, picks_df: pd.DataFrame, price_df: pd.DataFrame) -> pd.DataFrame:
        """Calculate returns for each pick across different time windows"""
        results = []
        
        try:
            # Handle timezone conversion for both dataframes
            def ensure_utc(series):
                if series.dt.tz is None:
                    return series.dt.tz_localize('UTC')
                return series.dt.tz_convert('UTC')
            
            if not price_df.empty:
                price_df['timestamp'] = ensure_utc(pd.to_datetime(price_df['timestamp']))
            if not picks_df.empty:
                picks_df['created_at'] = ensure_utc(pd.to_datetime(picks_df['created_at']))
            
            for _, pick in picks_df.iterrows():
                symbol = pick['symbol']
                entry_time = pick['created_at']
                
                for window in self.windows:
                    exit_time = entry_time + timedelta(hours=window)
                    
                    # Get relevant price data
                    symbol_prices = price_df[
                        (price_df['symbol'] == symbol) & 
                        (price_df['timestamp'] >= entry_time) & 
                        (price_df['timestamp'] <= exit_time)
                    ]
                    
                    if len(symbol_prices) >= 2:
                        entry_price = symbol_prices.iloc[0]['price']
                        exit_price = symbol_prices.iloc[-1]['price']
                        
                        # Calculate return based on suggested position
                        price_change = ((exit_price - entry_price) / entry_price) * 100
                        if pick['suggested_position'] == 'Short':
                            price_change = -price_change
                        
                        results.append({
                            'symbol': symbol,
                            'entry_time': entry_time,
                            'window': window,
                            'funding_rate': pick['funding_rate'],
                            'opportunity_score': pick['opportunity_score'],
                            'exchange': pick['exchange'],
                            'suggested_position': pick['suggested_position'],
                            'return': price_change,
                            'successful': (price_change > 0)
                        })
            
            if results:
                return pd.DataFrame(results)
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Error calculating returns: {e}")
            logger.exception("Detailed error:")
            return pd.DataFrame()

    def create_performance_visualizations(self, performance_df: pd.DataFrame):
        """Create various performance visualizations"""
        # 1. Success Rate by Time Window
        success_by_window = (
            performance_df.groupby('window')
            .agg({
                'successful': 'mean',
                'return': ['mean', 'std', 'count']
            })
            .round(4)
        )
        
        fig1 = go.Figure()
        fig1.add_trace(go.Bar(
            x=success_by_window.index,
            y=success_by_window[('successful', 'mean')] * 100,
            name='Success Rate',
            text=[f"{x:.1f}%" for x in success_by_window[('successful', 'mean')] * 100],
            textposition='auto',
        ))
        
        fig1.update_layout(
            title='Success Rate by Time Window',
            xaxis_title='Time Window (hours)',
            yaxis_title='Success Rate (%)',
            template='plotly_dark',
            height=500
        )
        fig1.show()
        
        # 2. Return Distribution
        fig2 = px.box(
            performance_df,
            x='window',
            y='return',
            color='exchange',
            title='Return Distribution by Time Window and Exchange',
            template='plotly_dark',
            height=500
        )
        fig2.show()
        
        # 3. Performance Over Time
        daily_performance = (
            performance_df.groupby([pd.Grouper(key='entry_time', freq='D'), 'window'])
            .agg({
                'return': 'mean',
                'successful': 'mean'
            })
            .reset_index()
        )
        
        fig3 = px.line(
            daily_performance,
            x='entry_time',
            y='return',
            color='window',
            title='Average Daily Returns by Time Window',
            template='plotly_dark',
            height=500
        )
        fig3.show()
        
        # 4. Correlation Plot
        fig4 = px.scatter(
            performance_df,
            x='funding_rate',
            y='return',
            color='exchange',
            facet_col='window',
            trendline="ols",
            title='Funding Rate vs Return by Time Window',
            template='plotly_dark',
            height=600
        )
        fig4.show()

    def analyze_top_performers(self, performance_df: pd.DataFrame):
        """Analyze and display the best performing funding rate signals"""
        try:
            # Group by symbol and calculate average success metrics
            symbol_performance = (
                performance_df.groupby(['symbol', 'exchange'])
                .agg({
                    'successful': 'mean',
                    'return': ['mean', 'count', 'std'],
                    'funding_rate': 'mean',
                    'opportunity_score': 'mean'
                })
                .round(4)
            )
            
            # Flatten column names
            symbol_performance.columns = [
                'success_rate', 'avg_return', 'trade_count', 
                'return_std', 'avg_funding_rate', 'avg_opportunity_score'
            ]
            
            # Filter for symbols with at least 3 trades
            symbol_performance = symbol_performance[symbol_performance['trade_count'] >= 3]
            
            # Sort by average return
            top_performers = symbol_performance.sort_values('avg_return', ascending=False)
            bottom_performers = symbol_performance.sort_values('avg_return', ascending=True)
            
            # Create visualization for top performers
            fig = go.Figure()
            
            # Add bars for returns
            fig.add_trace(go.Bar(
                x=top_performers.head(10).index.get_level_values('symbol'),
                y=top_performers.head(10)['avg_return'],
                name='Average Return %',
                text=top_performers.head(10)['avg_return'].apply(lambda x: f'{x:.2f}%'),
                textposition='auto',
            ))
            
            # Add scatter for success rate
            fig.add_trace(go.Scatter(
                x=top_performers.head(10).index.get_level_values('symbol'),
                y=top_performers.head(10)['success_rate'] * 100,
                name='Success Rate %',
                yaxis='y2',
                mode='markers',
                marker=dict(size=12)
            ))
            
            # Update layout
            fig.update_layout(
                title='Top 10 Performing Assets',
                xaxis_title='Symbol',
                yaxis_title='Average Return (%)',
                yaxis2=dict(
                    title='Success Rate (%)',
                    overlaying='y',
                    side='right'
                ),
                template='plotly_dark',
                height=600,
                showlegend=True
            )
            
            fig.show()
            
            # Print detailed statistics
            print("\n=== Top 10 Performing Assets ===")
            for (symbol, exchange), metrics in top_performers.head(10).iterrows():
                print(f"\n{symbol} ({exchange}):")
                print(f"Average Return: {metrics['avg_return']:.2f}%")
                print(f"Success Rate: {metrics['success_rate']*100:.1f}%")
                print(f"Number of Trades: {metrics['trade_count']}")
                print(f"Average Funding Rate: {metrics['avg_funding_rate']:.4f}%")
                print(f"Return Std Dev: {metrics['return_std']:.2f}%")
                print(f"Avg Opportunity Score: {metrics['avg_opportunity_score']:.2f}")
            
            return top_performers
            
        except Exception as e:
            logger.error(f"Error analyzing top performers: {e}")
            return pd.DataFrame()

    def create_detailed_asset_chart(self, performance_df: pd.DataFrame, price_df: pd.DataFrame, symbol: str):
        """Create detailed performance chart for a specific asset including price movement"""
        try:
            asset_data = performance_df[performance_df['symbol'] == symbol].copy()
            asset_prices = price_df[price_df['symbol'] == symbol].copy()
            
            if asset_data.empty or asset_prices.empty:
                return None
            
            # Ensure timestamps are properly aligned
            asset_data['entry_time'] = pd.to_datetime(asset_data['entry_time'])
            asset_prices['timestamp'] = pd.to_datetime(asset_prices['timestamp'])
            
            # Create continuous price index
            full_range = pd.date_range(
                start=min(asset_data['entry_time'].min(), asset_prices['timestamp'].min()),
                end=max(asset_data['entry_time'].max(), asset_prices['timestamp'].max()),
                freq='1H'
            )
            
            # Resample price data to ensure smooth visualization
            price_df_resampled = asset_prices.set_index('timestamp').reindex(full_range)
            price_df_resampled['price'] = price_df_resampled['price'].interpolate(method='linear')
            price_df_resampled['smooth_price'] = price_df_resampled['price'].rolling(window=6, min_periods=1).mean()
            
            # Create figure
            fig = go.Figure()
            
            # Add price line with improved styling
            fig.add_trace(go.Scatter(
                x=price_df_resampled.index,
                y=price_df_resampled['smooth_price'],
                name='Price',
                line=dict(color='blue', width=2, shape='spline'),
                yaxis='y3'
            ))
            
            # Add funding rate line
            fig.add_trace(go.Scatter(
                x=asset_data['entry_time'],
                y=asset_data['funding_rate'],
                name='Funding Rate',
                line=dict(color='yellow', width=2),
                mode='lines+markers',
                marker=dict(size=6)
            ))
            
            # Add trade returns
            fig.add_trace(go.Scatter(
                x=asset_data['entry_time'],
                y=asset_data['return'],
                name='Trade Return',
                mode='markers',
                marker=dict(
                    size=12,
                    color=asset_data['return'],
                    colorscale='RdYlGn',
                    showscale=True,
                    colorbar=dict(
                        title='Return %',
                        thickness=15,
                        len=0.7
                    ),
                    line=dict(width=1, color='white')
                ),
                yaxis='y2'
            ))
            
            # Update layout with improved styling
            fig.update_layout(
                title=dict(
                    text=f'{symbol} Performance Analysis',
                    font=dict(size=24)
                ),
                xaxis=dict(
                    title='Time',
                    gridcolor='rgba(128, 128, 128, 0.2)',
                    showgrid=True
                ),
                yaxis=dict(
                    title='Funding Rate (%)',
                    titlefont=dict(color='yellow'),
                    tickfont=dict(color='yellow'),
                    gridcolor='rgba(128, 128, 128, 0.2)',
                    showgrid=True
                ),
                yaxis2=dict(
                    title='Return (%)',
                    titlefont=dict(color='green'),
                    tickfont=dict(color='green'),
                    overlaying='y',
                    side='right',
                    gridcolor='rgba(128, 128, 128, 0.2)',
                    showgrid=False
                ),
                yaxis3=dict(
                    title='Price ($)',
                    titlefont=dict(color='blue'),
                    tickfont=dict(color='blue'),
                    overlaying='y',
                    side='left',
                    position=0.05,
                    gridcolor='rgba(128, 128, 128, 0.2)',
                    showgrid=False
                ),
                template='plotly_dark',
                height=800,
                showlegend=True,
                legend=dict(
                    yanchor="top",
                    y=0.99,
                    xanchor="left",
                    x=0.01,
                    bgcolor='rgba(0,0,0,0.5)'
                ),
                margin=dict(l=100, r=100, t=100, b=50),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            
            # Add enhanced performance statistics
            stats = {
                'Avg Return': f"{asset_data['return'].mean():.2f}%",
                'Success Rate': f"{(asset_data['successful'].mean() * 100):.1f}%",
                'Avg Funding': f"{asset_data['funding_rate'].mean():.4f}%",
                'Trade Count': str(len(asset_data)),
                'Price Change': f"{((asset_prices['price'].iloc[-1] / asset_prices['price'].iloc[0] - 1) * 100):.2f}%",
                'Return Volatility': f"{asset_data['return'].std():.2f}%",
                'Sharpe Ratio': f"{(asset_data['return'].mean() / asset_data['return'].std() if asset_data['return'].std() != 0 else 0):.2f}"
            }
            
            annotation_text = '<br>'.join([f"<b>{k}:</b> {v}" for k, v in stats.items()])
            fig.add_annotation(
                xref='paper',
                yref='paper',
                x=0.99,
                y=0.99,
                text=annotation_text,
                showarrow=False,
                font=dict(size=12, color='white'),
                bgcolor='rgba(0,0,0,0.7)',
                bordercolor='white',
                borderwidth=1,
                align='left'
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating asset chart for {symbol}: {e}")
            return None

    def generate_analysis_summary(self, performance_df: pd.DataFrame, price_df: pd.DataFrame) -> None:
        """Generate a comprehensive analysis summary"""
        try:
            print("\n=== Funding Rate Analysis Summary ===\n")
            
            # 1. Overall Performance Metrics
            print("1. Overall Performance:")
            print(f"Total trades analyzed: {len(performance_df)}")
            print(f"Unique symbols tracked: {performance_df['symbol'].nunique()}")
            print(f"Date range: {performance_df['entry_time'].min().date()} to {performance_df['entry_time'].max().date()}")
            print(f"Overall success rate: {(performance_df['successful'].mean() * 100):.1f}%")
            print(f"Average return: {performance_df['return'].mean():.2f}%")
            
            # 2. Performance by Time Window
            print("\n2. Performance by Time Window:")
            for window in sorted(performance_df['window'].unique()):
                window_data = performance_df[performance_df['window'] == window]
                print(f"\n{window}h Window:")
                print(f"  Success rate: {(window_data['successful'].mean() * 100):.1f}%")
                print(f"  Average return: {window_data['return'].mean():.2f}%")
                print(f"  Best trade: {window_data['return'].max():.2f}%")
                print(f"  Worst trade: {window_data['return'].min():.2f}%")
            
            # 3. Top Performing Symbols
            print("\n3. Top Performing Symbols:")
            symbol_performance = (
                performance_df.groupby('symbol')
                .agg({
                    'return': ['mean', 'count'],
                    'successful': 'mean',
                    'funding_rate': 'mean'
                })
                .round(4)
            )
            symbol_performance.columns = ['avg_return', 'trade_count', 'success_rate', 'avg_funding']
            top_symbols = symbol_performance[symbol_performance['trade_count'] >= 5].sort_values('avg_return', ascending=False)
            
            for symbol, metrics in top_symbols.head().iterrows():
                print(f"\n{symbol}:")
                print(f"  Average return: {metrics['avg_return']:.2f}%")
                print(f"  Success rate: {(metrics['success_rate'] * 100):.1f}%")
                print(f"  Number of trades: {metrics['trade_count']}")
                print(f"  Average funding rate: {metrics['avg_funding']:.4f}%")
            
            # 4. Funding Rate Analysis
            print("\n4. Funding Rate Analysis:")
            print(f"Average funding rate: {performance_df['funding_rate'].mean():.4f}%")
            print(f"Funding rate range: {performance_df['funding_rate'].min():.4f}% to {performance_df['funding_rate'].max():.4f}%")
            
            # Calculate correlation between funding rates and returns
            correlation = performance_df['funding_rate'].corr(performance_df['return'])
            print(f"Correlation with returns: {correlation:.3f}")
            
            # 5. Strategy Insights
            print("\n5. Strategy Insights:")
            by_position = performance_df.groupby('suggested_position').agg({
                'return': ['mean', 'count'],
                'successful': 'mean'
            }).round(4)
            
            for position, metrics in by_position.iterrows():
                print(f"\n{position} positions:")
                print(f"  Average return: {metrics[('return', 'mean')]:.2f}%")
                print(f"  Success rate: {(metrics[('successful', 'mean')] * 100):.1f}%")
                print(f"  Number of trades: {metrics[('return', 'count')]}")
            
            # 6. Risk Metrics
            print("\n6. Risk Metrics:")
            print(f"Return volatility: {performance_df['return'].std():.2f}%")
            sharpe = (performance_df['return'].mean() / performance_df['return'].std() 
                     if performance_df['return'].std() != 0 else 0)
            print(f"Sharpe ratio: {sharpe:.2f}")
            
        except Exception as e:
            logger.error(f"Error generating analysis summary: {e}")
            logger.exception("Detailed error:")

def main():
    analyzer = FundingPerformanceAnalyzer()
    
    # Fetch historical top picks
    picks_df = analyzer.fetch_historical_picks(weeks=8)
    if picks_df.empty:
        logger.error("No historical picks found")
        return
    
    # Fetch price data
    start_date = picks_df['created_at'].min()
    end_date = picks_df['created_at'].max() + timedelta(days=1)
    symbols = picks_df['symbol'].unique().tolist()
    
    price_df = analyzer.fetch_price_data(
        symbols,
        start_date.strftime("%Y-%m-%d %H:%M:%S"),
        end_date.strftime("%Y-%m-%d %H:%M:%S")
    )
    
    if price_df.empty:
        logger.error("No price data found")
        return
    
    # Calculate performance
    performance_df = analyzer.calculate_returns(picks_df, price_df)
    
    if not performance_df.empty:
        # Create standard visualizations
        analyzer.create_performance_visualizations(performance_df)
        
        # Analyze top performers
        top_performers = analyzer.analyze_top_performers(performance_df)
        
        # Create detailed charts for top 5 assets
        for symbol in top_performers.head(5).index.get_level_values('symbol'):
            fig = analyzer.create_detailed_asset_chart(performance_df, price_df, symbol)
            if fig:
                fig.show()
                
                # Print detailed analysis for this symbol
                symbol_data = performance_df[performance_df['symbol'] == symbol]
                print(f"\n=== Detailed Analysis for {symbol} ===")
                print(f"Total Trades: {len(symbol_data)}")
                print(f"Average Funding Rate: {symbol_data['funding_rate'].mean():.4f}%")
                print(f"Average Return: {symbol_data['return'].mean():.2f}%")
                print(f"Success Rate: {(symbol_data['successful'].mean() * 100):.1f}%")
                print(f"Best Trade: {symbol_data['return'].max():.2f}%")
                print(f"Worst Trade: {symbol_data['return'].min():.2f}%")
                
                # Calculate correlation between funding rate and returns
                corr = symbol_data['funding_rate'].corr(symbol_data['return'])
                print(f"Funding-Return Correlation: {corr:.3f}")
        
        # Generate analysis summary
        analyzer.generate_analysis_summary(performance_df, price_df)
        
    else:
        logger.error("No performance data to analyze")

if __name__ == "__main__":
    main() 