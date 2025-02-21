import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
import logging
import os
from dotenv import load_dotenv
from supabase import create_client
import ccxt
import aiohttp
import asyncio
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FundingAnalyzer:
    def __init__(self):
        load_dotenv()
        self.binance = ccxt.binance({
            'options': {'defaultType': 'future'},
            'enableRateLimit': True
        })
        self.hyperliquid_api = "https://api.hyperliquid.xyz/info"
        self.supabase = create_client(
            os.getenv("NEXT_PUBLIC_SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        )
        self.common_pairs = ['BTC', 'ETH', 'SOL']  # Add more as needed

    async def fetch_hl_funding_rates(self, symbol: str, start_time: int, end_time: int):
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "type": "fundingHistory",
                    "coin": symbol,
                    "startTime": start_time,
                    "endTime": end_time
                }
                headers = {"Content-Type": "application/json"}
                
                async with session.post(self.hyperliquid_api, json=payload, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    logger.error(f"HL API error: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"HL API error: {e}")
            return []

    def fetch_binance_funding_rates(self, symbol: str, start_time: int, end_time: int):
        all_rates = []
        current_time = start_time

        while current_time < end_time:
            try:
                params = {'endTime': min(current_time + (24 * 3600 * 1000), end_time)}
                rates = self.binance.fetchFundingRateHistory(
                    f"{symbol}/USDT:USDT",
                    current_time,
                    None,  # Let CCXT handle pagination
                    params
                )
                
                if rates:
                    all_rates.extend(rates)
                    # Move to next day
                    current_time = max(rate['timestamp'] for rate in rates) + 1
                else:
                    current_time += 24 * 3600 * 1000
                    
                time.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Binance API error: {e}")
                current_time += 24 * 3600 * 1000  # Skip forward on error

        logger.info(f"Retrieved {len(all_rates)} Binance funding rates")
        return all_rates

    async def get_funding_data(self, symbol: str, start_date: datetime, end_date: datetime):
        start_ts = int(start_date.timestamp() * 1000)
        end_ts = int(end_date.timestamp() * 1000)

        # Get raw data
        hl_rates = await self.fetch_hl_funding_rates(symbol, start_ts, end_ts)
        binance_rates = self.fetch_binance_funding_rates(symbol, start_ts, end_ts)

        # Process HL data
        hl_df = pd.DataFrame(hl_rates)
        if not hl_df.empty:
            hl_df['timestamp'] = pd.to_datetime(hl_df['time'], unit='ms', utc=True)
            hl_df['hl_rate'] = hl_df['fundingRate'].astype(float)
            hl_df = hl_df[['timestamp', 'hl_rate']]

        # Process Binance data
        binance_df = pd.DataFrame(binance_rates)
        if not binance_df.empty:
            binance_df['timestamp'] = pd.to_datetime(binance_df['timestamp'], unit='ms', utc=True)
            binance_df['binance_rate'] = binance_df['fundingRate'].astype(float)
            binance_df = binance_df[['timestamp', 'binance_rate']]

        # Floor timestamps to 8h intervals for analysis
        if not hl_df.empty:
            hl_df['interval'] = hl_df['timestamp'].dt.floor('8h')
        if not binance_df.empty:
            binance_df['interval'] = binance_df['timestamp'].dt.floor('8h')

        # Merge data
        if not hl_df.empty and not binance_df.empty:
            # Merge on 8h intervals
            funding_df = pd.merge(
                hl_df.groupby('interval')['hl_rate'].mean().reset_index(),
                binance_df.groupby('interval')['binance_rate'].mean().reset_index(),
                on='interval',
                how='inner'
            )
            
            funding_df['rate_diff'] = funding_df['binance_rate'] - funding_df['hl_rate']
            
            # Calculate intervals with significant differentials (95th percentile)
            threshold = np.percentile(abs(funding_df['rate_diff']), 95)
            significant_intervals = funding_df[abs(funding_df['rate_diff']) >= threshold]
            
            logger.info(f"Found {len(significant_intervals)} significant intervals out of {len(funding_df)} total")
            
            return {
                'funding_df': funding_df,
                'significant_df': significant_intervals,
                'threshold': threshold,
                'total_intervals': len(funding_df),
                'significant_intervals': len(significant_intervals)
            }
            
        return None

    def get_price_data(self, symbol: str, start_date: datetime, end_date: datetime):
        try:
            response = (self.supabase
                .schema('crypto_historical')
                .from_('price_history')
                .select("*")
                .eq('symbol', symbol)
                .gte('datetime', start_date.isoformat())
                .lte('datetime', end_date.isoformat())
                .order('datetime', desc=False)
                .execute())

            if response.data:
                df = pd.DataFrame(response.data)
                df['datetime'] = pd.to_datetime(df['datetime']).dt.tz_convert('UTC')
                df['interval'] = df['datetime'].dt.floor('8h')
                return df

        except Exception as e:
            logger.error(f"Error fetching price data: {e}")
        return None

    def analyze_returns(self, funding_data, price_data, windows=[1, 4, 8, 24]):
        if funding_data is None or price_data is None:
            return None

        # Calculate returns for each interval
        price_changes = {}
        for window in windows:
            price_data[f'return_{window}h'] = (
                price_data['close'].shift(-window) / price_data['close'] - 1
            ) * 100

        # Average returns per 8h interval
        returns_df = price_data.groupby('interval')[
            [f'return_{w}h' for w in windows]
        ].mean().reset_index()

        # Merge with funding data
        merged_df = pd.merge(
            funding_data['funding_df'],
            returns_df,
            on='interval',
            how='left'
        )

        # Calculate statistics
        significant_df = funding_data['significant_df']
        stats = {
            'total_intervals': funding_data['total_intervals'],
            'significant_intervals': funding_data['significant_intervals'],
            'threshold': funding_data['threshold'],
            'avg_rate_diff': merged_df['rate_diff'].mean(),
            'max_rate_diff': merged_df['rate_diff'].max(),
            'min_rate_diff': merged_df['rate_diff'].min(),
            'std_rate_diff': merged_df['rate_diff'].std()
        }

        # Calculate return statistics for each window
        for window in windows:
            column = f'return_{window}h'
            stats.update({
                f'avg_{window}h_return_all': merged_df[column].mean(),
                f'avg_{window}h_return_sig': significant_df.merge(
                    returns_df, on='interval', how='left'
                )[column].mean(),
                f'std_{window}h_return': merged_df[column].std()
            })

        return {'data': merged_df, 'stats': stats}

    def create_plots(self, results, symbol: str):
        """Create analysis plots"""
        plots = {}
        
        # Rate differential plot
        diff_fig = go.Figure()
        diff_fig.add_trace(go.Scatter(
            x=results['data']['interval'],
            y=results['data']['rate_diff'],
            mode='markers',
            marker=dict(
                size=8,
                color=abs(results['data']['rate_diff']),
                colorscale='Viridis',
                showscale=True
            )
        ))
        
        threshold = results['stats']['threshold']
        diff_fig.add_hline(y=threshold, line_dash="dash", line_color="red")
        diff_fig.add_hline(y=-threshold, line_dash="dash", line_color="red")
        
        diff_fig.update_layout(
            title=f'Funding Rate Differentials - {symbol}',
            xaxis_title='Time',
            yaxis_title='Rate Differential',
            template='plotly_white'
        )
        
        plots['differential'] = diff_fig
        
        # Return analysis plots
        for window in [1, 4, 8, 24]:
            ret_fig = go.Figure()
            ret_fig.add_trace(go.Scatter(
                x=results['data']['rate_diff'],
                y=results['data'][f'return_{window}h'],
                mode='markers',
                marker=dict(
                    size=8,
                    color=abs(results['data']['rate_diff']),
                    colorscale='RdYlBu',
                    showscale=True
                )
            ))
            
            ret_fig.update_layout(
                title=f'{window}h Return vs Rate Differential',
                xaxis_title='Rate Differential',
                yaxis_title=f'{window}h Return (%)',
                template='plotly_white'
            )
            
            plots[f'return_{window}h'] = ret_fig
            
        return plots

async def main():
    st.set_page_config(page_title="Funding Rate Analysis", layout="wide")
    st.title("Funding Rate Differential Analysis")

    analyzer = FundingAnalyzer()

    # Sidebar controls
    lookback_days = st.sidebar.slider("Lookback Period (days)", 7, 60, 30)
    symbol = st.sidebar.selectbox("Select Symbol", analyzer.common_pairs)

    # Date range
    end_date = datetime(2025, 2, 15)
    start_date = end_date - timedelta(days=lookback_days)

    with st.spinner("Analyzing funding rates..."):
        # Get funding rate data
        funding_data = await analyzer.get_funding_data(symbol, start_date, end_date)
        if funding_data is None:
            st.error("No funding data available")
            return

        # Get price data
        price_data = analyzer.get_price_data(symbol, start_date, end_date)
        if price_data is None:
            st.error("No price data available")
            return

        # Analyze data
        results = analyzer.analyze_returns(funding_data, price_data)
        if results is None:
            st.error("Analysis failed")
            return

        # Display results
        st.header("Summary Statistics")
        stats = results['stats']
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(
                "Significant Intervals",
                f"{stats['significant_intervals']}/{stats['total_intervals']}"
            )
        with col2:
            st.metric("Average Differential", f"{stats['avg_rate_diff']:.4f}%")
        with col3:
            st.metric("Max Differential", f"{stats['max_rate_diff']:.4f}%")
        with col4:
            st.metric("Min Differential", f"{stats['min_rate_diff']:.4f}%")

        # Create and display plots
        plots = analyzer.create_plots(results, symbol)
        
        st.plotly_chart(plots['differential'], use_container_width=True)
        
        st.header("Return Analysis")
        tabs = st.tabs(['1h', '4h', '8h', '24h'])
        for tab, window in zip(tabs, [1, 4, 8, 24]):
            with tab:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(
                        "Average Return (All)",
                        f"{stats[f'avg_{window}h_return_all']:.4f}%"
                    )
                with col2:
                    st.metric(
                        "Average Return (Significant)",
                        f"{stats[f'avg_{window}h_return_sig']:.4f}%"
                    )
                st.plotly_chart(plots[f'return_{window}h'], use_container_width=True)
        
        # Display raw data
        st.header("Raw Data")
        with st.expander("View Complete Dataset"):
            # Format the timestamps for better readability
            display_df = results['data'].copy()
            display_df['interval'] = display_df['interval'].dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # Round numerical columns for cleaner display
            numeric_cols = display_df.select_dtypes(include=[np.number]).columns
            display_df[numeric_cols] = display_df[numeric_cols].round(6)
            
            # Sort by interval descending to show most recent data first
            display_df = display_df.sort_values('interval', ascending=False)
            
            # Display the dataframe
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )

if __name__ == "__main__":
    asyncio.run(main())