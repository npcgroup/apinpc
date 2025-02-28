import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Tuple
import logging
import os
from dotenv import load_dotenv
from supabase import create_client
import ccxt
import aiohttp
import asyncio
import json
import time
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FundingAnalyzer:
    def __init__(self):
        """Initialize the FundingAnalyzer with necessary connections"""
        load_dotenv()
        
        # Initialize exchange connections
        self.binance = ccxt.binance({
            'options': {
                'defaultType': 'future',
            },
            'enableRateLimit': True
        })
        self.hyperliquid_api = "https://api.hyperliquid.xyz/info"
        
        # Connect to Supabase
        self.supabase = create_client(
            os.getenv("NEXT_PUBLIC_SUPABASE_URL"),
            os.getenv("NEXT_PUBLIC_SUPABASE_KEY")
        )
        
        # Common trading pairs
        self.common_pairs = [
            'BTC', 'ETH', 'SOL', 'AVAX', 'BNB', 'ARB', 'OP', 'MATIC',
            'ACE', 'AERGO', 'DOGE', 'XRP', 'ADA', 'NEAR', 'APT', 'SUI', 'INJ'
        ]

    async def fetch_hl_funding_history(self, symbol: str, start_time: int, end_time: int) -> List[Dict]:
        """Fetch historical funding rates from Hyperliquid"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "type": "fundingHistory",
                    "coin": symbol,
                    "startTime": start_time,
                    "endTime": end_time
                }
                headers = {"Content-Type": "application/json"}
                
                async with session.post(
                    self.hyperliquid_api,
                    json=payload,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    else:
                        logger.error(f"Error fetching HL funding for {symbol}: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error in HL API call for {symbol}: {e}")
            return []

    def fetch_binance_funding_history(self, symbol: str, start_time: int, end_time: int) -> List[Dict]:
        """Fetch historical funding rates from Binance"""
        try:
            all_rates = []
            current_start = start_time
            
            while current_start < end_time:
                try:
                    # Fetch in chunks with proper symbol format
                    params = {'endTime': min(current_start + (8 * 3600 * 1000), end_time)}
                    rates = self.binance.fetchFundingRateHistory(
                        f"{symbol}/USDT:USDT",
                        current_start,
                        1000,  # Maximum records per request
                        params
                    )
                    
                    if rates:
                        all_rates.extend(rates)
                        # Update start time for next chunk
                        current_start = max([rate['timestamp'] for rate in rates]) + 1
                    else:
                        break
                        
                    time.sleep(0.1)  # Rate limiting
                    
                except Exception as chunk_error:
                    logger.error(f"Error fetching chunk for {symbol}: {chunk_error}")
                    break
            
            # Format the rates consistently
            formatted_rates = []
            for rate in all_rates:
                formatted_rates.append({
                    'timestamp': rate['timestamp'],
                    'fundingRate': float(rate['fundingRate'])
                })
            
            return formatted_rates
            
        except Exception as e:
            logger.error(f"Error fetching Binance funding for {symbol}: {e}")
            return []

    async def get_historical_funding_rates(self, start_date: datetime, end_date: datetime, 
                                         symbol: str) -> pd.DataFrame:
        """Get historical funding rates from both exchanges"""
        try:
            start_ts = int(start_date.timestamp() * 1000)
            end_ts = int(end_date.timestamp() * 1000)
            
            # Fetch from both exchanges
            hl_rates = await self.fetch_hl_funding_history(symbol, start_ts, end_ts)
            binance_rates = self.fetch_binance_funding_history(symbol, start_ts, end_ts)
            
            # Process Hyperliquid data
            hl_df = pd.DataFrame(hl_rates)
            if not hl_df.empty:
                hl_df['timestamp'] = pd.to_datetime(hl_df['time'], unit='ms')
                hl_df['hl_rate'] = hl_df['fundingRate'].astype(float)
                hl_df = hl_df[['timestamp', 'hl_rate']]
            
            # Process Binance data
            binance_df = pd.DataFrame(binance_rates)
            if not binance_df.empty:
                binance_df['timestamp'] = pd.to_datetime(binance_df['timestamp'], unit='ms')
                binance_df['binance_rate'] = binance_df['fundingRate'].astype(float)
                binance_df = binance_df[['timestamp', 'binance_rate']]
            
            # Merge data
            if not hl_df.empty and not binance_df.empty:
                merged_df = pd.merge(hl_df, binance_df, on='timestamp', how='outer')
                merged_df['rate_diff'] = merged_df['binance_rate'] - merged_df['hl_rate']
                merged_df['symbol'] = symbol
                return merged_df
            
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Error getting historical funding rates: {e}")
            return pd.DataFrame()

    def get_price_history(self, symbol: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Fetch price history from Supabase crypto_historical schema"""
        try:
            # Using the query builder pattern
            response = (self.supabase
                .from_('crypto_historical.price_history')
                .select("*")
                .eq('symbol', symbol)
                .gte('datetime', start_date.isoformat())
                .lte('datetime', end_date.isoformat())
                .order('datetime', desc=False)
                .execute())
            
            if response.data:
                df = pd.DataFrame(response.data)
                df['datetime'] = pd.to_datetime(df['datetime'])
                logger.info(f"Retrieved {len(df)} price records for {symbol}")
                return df
            
            logger.warning(f"No price data found for {symbol}")
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Error fetching price history for {symbol}: {e}")
            logger.error(f"Query details: symbol={symbol}, start={start_date}, end={end_date}")
            return pd.DataFrame()

    def calculate_returns(self, df: pd.DataFrame, windows: List[int]) -> pd.DataFrame:
        """Calculate forward returns for specified hourly windows"""
        for window in windows:
            df[f'return_{window}h'] = (
                df['close'].shift(-window) / df['close'] - 1
            ) * 100
        return df

    async def analyze_symbol(self, symbol: str, start_date: datetime, end_date: datetime, 
                           windows: List[int]) -> Dict:
        """Analyze a single symbol's funding rates and price impact"""
        try:
            # Get funding rates
            funding_df = await self.get_historical_funding_rates(start_date, end_date, symbol)
            if funding_df.empty:
                return None
                
            # Get price history
            price_df = self.get_price_history(symbol, start_date, end_date)
            if price_df.empty:
                return None
                
            # Calculate returns
            price_df = self.calculate_returns(price_df, windows)
            
            # Merge price and funding data
            merged_df = pd.merge_asof(
                funding_df.sort_values('timestamp'),
                price_df.rename(columns={'datetime': 'timestamp'}),
                on='timestamp',
                direction='nearest'
            )
            
            # Calculate statistics
            stats = {
                'symbol': symbol,
                'avg_rate_diff': merged_df['rate_diff'].mean(),
                'max_rate_diff': merged_df['rate_diff'].max(),
                'min_rate_diff': merged_df['rate_diff'].min(),
                'std_rate_diff': merged_df['rate_diff'].std()
            }
            
            # Calculate return statistics for each window
            for window in windows:
                returns = merged_df[f'return_{window}h']
                pos_diff_returns = merged_df[merged_df['rate_diff'] > 0][f'return_{window}h']
                neg_diff_returns = merged_df[merged_df['rate_diff'] < 0][f'return_{window}h']
                
                stats.update({
                    f'avg_return_{window}h': returns.mean(),
                    f'std_return_{window}h': returns.std(),
                    f'pos_diff_return_{window}h': pos_diff_returns.mean(),
                    f'neg_diff_return_{window}h': neg_diff_returns.mean()
                })
            
            return {
                'stats': stats,
                'data': merged_df
            }
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            return None

    def create_differential_plot(self, df: pd.DataFrame, symbol: str) -> go.Figure:
        """Create plot showing funding rate differentials over time"""
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['rate_diff'],
            mode='lines',
            name='Rate Differential',
            line=dict(color='blue')
        ))
        
        fig.update_layout(
            title=f'Funding Rate Differential for {symbol}',
            xaxis_title='Date',
            yaxis_title='Rate Differential (%)',
            template='plotly_white',
            height=400
        )
        
        return fig

    def create_return_scatter(self, df: pd.DataFrame, window: int) -> go.Figure:
        """Create scatter plot of rate differentials vs returns"""
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df['rate_diff'],
            y=df[f'return_{window}h'],
            mode='markers',
            name=f'{window}h Returns',
            marker=dict(
                size=8,
                color=df['rate_diff'],
                colorscale='RdYlBu',
                showscale=True
            )
        ))
        
        fig.update_layout(
            title=f'Rate Differential vs {window}h Returns',
            xaxis_title='Rate Differential (%)',
            yaxis_title=f'Return {window}h (%)',
            template='plotly_white',
            height=400
        )
        
        return fig

async def main():
    st.set_page_config(page_title="Funding Rate Analysis", layout="wide")
    st.title("Funding Rate Differential Analysis")
    
    # Initialize analyzer
    analyzer = FundingAnalyzer()
    
    # Sidebar controls
    st.sidebar.header("Analysis Parameters")
    
    lookback_days = st.sidebar.slider(
        "Lookback Period (days)",
        min_value=7,
        max_value=60,
        value=30
    )
    
    selected_symbol = st.sidebar.selectbox(
        "Select Symbol",
        analyzer.common_pairs
    )
    
    # Date range
    end_date = datetime(2025, 2, 15)  # Last available data
    start_date = end_date - timedelta(days=lookback_days)
    
    st.sidebar.info(f"Analyzing data from {start_date.date()} to {end_date.date()}")
    
    # Analysis windows
    windows = [1, 4, 8, 24]  # hours
    
    # Run analysis
    with st.spinner("Analyzing funding rates and price impact..."):
        results = await analyzer.analyze_symbol(
            selected_symbol, 
            start_date,
            end_date,
            windows
        )
        
    if results:
        # Display summary statistics
        st.header("Summary Statistics")
        stats = results['stats']
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Average Rate Diff", f"{stats['avg_rate_diff']:.4f}%")
        with col2:
            st.metric("Max Rate Diff", f"{stats['max_rate_diff']:.4f}%")
        with col3:
            st.metric("Min Rate Diff", f"{stats['min_rate_diff']:.4f}%")
        with col4:
            st.metric("Std Rate Diff", f"{stats['std_rate_diff']:.4f}%")
        
        # Display plots
        st.header("Analysis Visualizations")
        
        # Rate differential over time
        st.plotly_chart(
            analyzer.create_differential_plot(results['data'], selected_symbol),
            use_container_width=True
        )
        
        # Returns analysis
        st.subheader("Returns Analysis")
        
        # Create tabs for different time windows
        tabs = st.tabs([f"{w}h Returns" for w in windows])
        
        for tab, window in zip(tabs, windows):
            with tab:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric(
                        "Avg Return (Positive Diff)", 
                        f"{stats[f'pos_diff_return_{window}h']:.4f}%"
                    )
                with col2:
                    st.metric(
                        "Avg Return (Negative Diff)",
                        f"{stats[f'neg_diff_return_{window}h']:.4f}%"
                    )
                
                st.plotly_chart(
                    analyzer.create_return_scatter(results['data'], window),
                    use_container_width=True
                )
        
        # Display raw data
        with st.expander("View Raw Data"):
            st.dataframe(results['data'])
    else:
        st.error("No data available for the selected symbol and time period")

if __name__ == "__main__":
    asyncio.run(main())