import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
import logging
import os
import io
import sys
from dotenv import load_dotenv
from supabase import create_client
import ccxt
import aiohttp
import asyncio
import time
import functools

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize session state for caching
if 'cache' not in st.session_state:
    st.session_state.cache = {}

class FundingAnalyzer:
    def __init__(self):
        load_dotenv()
        
        # Configure logging to see detailed output
        logging.getLogger().setLevel(logging.INFO)
        
        # Initialize both exchange clients with CCXT
        logger.info("Initializing Binance client...")
        self.binance = ccxt.binance({
            'options': {'defaultType': 'future'},
            'enableRateLimit': True
        })
        
        logger.info("Initializing HyperLiquid client...")
        self.hyperliquid = ccxt.hyperliquid({
            'enableRateLimit': True
        })
        
        # Print ccxt version
        logger.info(f"Using ccxt version: {ccxt.__version__}")
        
        supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        # If environment variables are not set, try to use Streamlit secrets (for cloud execution)
        if not supabase_url or not supabase_key:
            try:
                supabase_url = st.secrets["NEXT_PUBLIC_SUPABASE_URL"]
                supabase_key = st.secrets["SUPABASE_SERVICE_ROLE_KEY"]
            except FileNotFoundError:
                raise RuntimeError(
                    "Missing Supabase credentials! Ensure environment variables are set locally, "
                    "or add them to Streamlit Secrets when deploying."
                )
        
        logger.info("Connecting to Supabase...")
        self.supabase = create_client(
            supabase_url,
            supabase_key
        )
        
        # Hard-coded list of pairs available on both exchanges (based on the provided list)
        self.common_pairs = [
            'APT' , 'ANIME', 'CHILLGUY', 'ENA', 'FARTCOIN', 'GAS', 'MEME', 
            'SUI', 'WLD', 'SEI', 'PNUT', 'SAGA', 'CRV', 'COMP', 'BIO', 'BLUR', 'AI16Z'
        ]
        
        # These are all the common pairs on binance and hyperliquid:
        # self.common_pairs = [
        #     'AAVE', 'ACE', 'ADA', 'AI', 'AI16Z', 'AIXBT', 'ALGO', 
        #     'ALT', 'ANIME', 'APE', 'APT', 'AR', 'ARB', 'ARK', 'ATOM', 
        #     'AVAX', 'BADGER', 'BANANA', 'BCH', 'BERA', 'BIGTIME', 
        #     'BIO', 'BLUR', 'BLZ', 'BNB', 'BNT', 'BOME', 'BRETT', 'BSV', 
        #     'BTC', 'CAKE', 'CATI', 'CELO', 'CFX', 'CHILLGUY', 'COMP', 
        #     'CRV', 'CYBER', 'DOGE', 'DOT', 'DYDX', 'DYM', 'EIGEN', 'ENA',
        #     'ENS', 'ETC', 'ETH', 'ETHFI', 'FARTCOIN', 'FET', 'FIL', 'FTM',
        #     'FTT', 'FXS', 'GALA', 'GAS', 'GMT', 'GMX', 'GOAT', 'GRASS', 
        #     'GRIFFAIN', 'HBAR', 'HMSTR', 'ILV', 'IMX', 'INJ', 'IO', 'IOTA', 
        #     'IP', 'JTO', 'JUP', 'KAITO', 'KAS', 'LAYER', 'LDO', 'LINK', 
        #     'LISTA', 'LOOM', 'LTC', 'MANTA', 'MAV', 'MAVIA', 'ME', 
        #     'MELANIA', 'MEME', 'MEW', 'MINA', 'MKR', 'MOODENG', 'MORPHO', 
        #     'MOVE', 'MYRO', 'NEAR', 'NEIROETH', 'NEO', 'NOT', 'NTRN', 
        #     'OGN', 'OM', 'OMNI', 'ONDO', 'OP', 'ORBS', 'ORDI', 'PENDLE', 
        #     'PENGU', 'PEOPLE', 'PIXEL', 'PNUT', 'POL', 'POLYX', 'POPCAT', 
        #     'PYTH', 'RDNT', 'RENDER', 'REZ', 'RSR', 'RUNE', 'S', 'SAGA', 
        #     'SAND', 'SCR', 'SEI', 'SNX', 'SOL', 'SPX', 'STG', 'STRAX', 
        #     'STRK', 'STX', 'SUI', 'SUPER', 'SUSHI', 'TAO', 'TIA', 'TNSR', 
        #     'TON', 'TRB', 'TRUMP', 'TRX', 'TST', 'TURBO', 'UMA', 'UNI', 
        #     'USTC', 'USUAL', 'VINE', 'VIRTUAL', 'VVV', 'W', 'WIF', 'WLD', 
        #     'XAI', 'XLM', 'XRP', 'YGG', 'ZEN', 'ZEREBRO', 'ZETA', 'ZK', 'ZRO']
        
        # Cache the support for each coin to avoid repeated checks
        self.supported_pairs_cache = {}

    @st.cache_data(ttl=3600)  # Cache for 1 hour
    def fetch_funding_rates_cached(_self, exchange, symbol, start_time, end_time):
        """Cached version of funding rate fetching to improve performance"""
        if exchange == 'binance':
            symbol_fmt = f"{symbol}/USDT:USDT"
            client = _self.binance
        else:  # hyperliquid
            # Fix: Use the correct format for HyperLiquid
            symbol_fmt = f"{symbol}/USDC:USDC"
            client = _self.hyperliquid
        
        all_rates = []
        current_time = start_time
        
        while current_time < end_time:
            try:
                batch_end = min(current_time + (7 * 24 * 3600 * 1000), end_time)  # 1 week of data at a time
                
                rates = client.fetchFundingRateHistory(
                    symbol_fmt,
                    current_time,
                    1000,  # Larger limit for fewer API calls
                    {'endTime': batch_end}
                )
                
                if rates:
                    all_rates.extend(rates)
                    if len(rates) > 0:
                        # Move to next batch after the last timestamp
                        current_time = max(rate['timestamp'] for rate in rates) + 1
                    else:
                        # If no data, move forward a week
                        current_time = batch_end + 1
                else:
                    # If no data, move forward a week
                    current_time = batch_end + 1
                
                # Less aggressive rate limiting since we're batching
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"{exchange.capitalize()} API error for {symbol}: {e}")
                # Move forward on error
                current_time = batch_end + 1
        
        logger.info(f"Retrieved {len(all_rates)} {exchange.capitalize()} funding rates for {symbol}")
        return all_rates

    async def get_funding_data(self, symbol, start_date, end_date, threshold=0.0):
        """Get and process funding rate data for both exchanges"""
        cache_key = f"funding_{symbol}_{start_date.isoformat()}_{end_date.isoformat()}"
        
        # Check if we have cached data
        if cache_key in st.session_state.cache:
            data = st.session_state.cache[cache_key]
            # Update threshold dynamically even if using cached data
            significant_intervals = data['funding_df'][abs(data['funding_df']['rate_diff']) >= threshold]
            data['significant_df'] = significant_intervals
            data['threshold'] = threshold
            data['significant_intervals'] = len(significant_intervals)
            data['has_significant_diff'] = len(significant_intervals) > 0
            return data
        
        start_ts = int(start_date.timestamp() * 1000)
        end_ts = int(end_date.timestamp() * 1000)

        # Get raw data using the cached function
        logger.info(f"Fetching funding rates for {symbol} from HyperLiquid...")
        hl_rates = self.fetch_funding_rates_cached('hyperliquid', symbol, start_ts, end_ts)
        
        logger.info(f"Fetching funding rates for {symbol} from Binance...")
        binance_rates = self.fetch_funding_rates_cached('binance', symbol, start_ts, end_ts)
        
        logger.info(f"Retrieved {len(hl_rates)} HyperLiquid rates and {len(binance_rates)} Binance rates")

        # Process HL data
        hl_df = pd.DataFrame(hl_rates)
        if not hl_df.empty:
            hl_df['timestamp'] = pd.to_datetime(hl_df['timestamp'], unit='ms', utc=True)
            # Annualize: Multiply by 100 for percentage, then by 8760 (24*365) for hourly to yearly
            hl_df['hl_rate'] = hl_df['fundingRate'].astype(float) * 100 * 8760
            hl_df = hl_df[['timestamp', 'hl_rate']]
            logger.info(f"Processed {len(hl_df)} HyperLiquid funding rates")
            logger.info(f"HyperLiquid rate range: {hl_df['hl_rate'].min():.4f}% to {hl_df['hl_rate'].max():.4f}%")
        else:
            logger.warning(f"No HyperLiquid funding rates found for {symbol}")

        # Process Binance data
        binance_df = pd.DataFrame(binance_rates)
        if not binance_df.empty:
            binance_df['timestamp'] = pd.to_datetime(binance_df['timestamp'], unit='ms', utc=True)
            # Annualize: Multiply by 100 for percentage, then by 1095 (3*365) for 8-hourly to yearly
            binance_df['binance_rate'] = binance_df['fundingRate'].astype(float) * 100 * 1095
            binance_df = binance_df[['timestamp', 'binance_rate']]
            logger.info(f"Processed {len(binance_df)} Binance funding rates")
            logger.info(f"Binance rate range: {binance_df['binance_rate'].min():.4f}% to {binance_df['binance_rate'].max():.4f}%")
        else:
            logger.warning(f"No Binance funding rates found for {symbol}")

        # Floor timestamps to 8h intervals for analysis
        if not hl_df.empty:
            hl_df['interval'] = hl_df['timestamp'].dt.floor('8h')
            logger.info(f"Unique HyperLiquid intervals: {len(hl_df['interval'].unique())}")
        if not binance_df.empty:
            binance_df['interval'] = binance_df['timestamp'].dt.floor('8h')
            logger.info(f"Unique Binance intervals: {len(binance_df['interval'].unique())}")

        # Merge data - making sure we have both sources of data
        if not hl_df.empty and not binance_df.empty:
            # Merge on 8h intervals with a groupby to handle multiple rates in the same interval
            logger.info("Merging funding rate data...")
            
            # Group and average rates by interval
            hl_grouped = hl_df.groupby('interval')['hl_rate'].mean().reset_index()
            binance_grouped = binance_df.groupby('interval')['binance_rate'].mean().reset_index()
            
            # Inner join to only include intervals with data from both exchanges
            funding_df = pd.merge(
                hl_grouped,
                binance_grouped,
                on='interval',
                how='inner'
            )
            
            if funding_df.empty:
                logger.warning(f"No overlapping intervals found for {symbol}")
                return None
            
            logger.info(f"Found {len(funding_df)} overlapping intervals")
            
            # Calculate rate difference
            funding_df['rate_diff'] = funding_df['binance_rate'] - funding_df['hl_rate']
            
            # Add raw data
            funding_df['raw_hl'] = funding_df['hl_rate']
            funding_df['raw_binance'] = funding_df['binance_rate']
            
            # Identify significant intervals using the provided threshold
            significant_intervals = funding_df[abs(funding_df['rate_diff']) >= threshold]
            
            logger.info(f"{symbol}: Found {len(significant_intervals)} significant intervals with threshold {threshold}% out of {len(funding_df)} total")
            logger.info(f"Rate diff range: {funding_df['rate_diff'].min():.4f}% to {funding_df['rate_diff'].max():.4f}%")
            
            result = {
                'symbol': symbol,
                'funding_df': funding_df,
                'significant_df': significant_intervals,
                'threshold': threshold,
                'total_intervals': len(funding_df),
                'significant_intervals': len(significant_intervals),
                'has_significant_diff': len(significant_intervals) > 0,
                'hl_data': hl_df,
                'binance_data': binance_df
            }
            
            # Cache the result
            st.session_state.cache[cache_key] = result
            return result
            
        logger.warning(f"Insufficient data for {symbol}")
        return None

    def get_price_data(self, symbol, start_date, end_date):
        """Get price data from Supabase"""
        cache_key = f"price_{symbol}_{start_date.isoformat()}_{end_date.isoformat()}"
        
        # Check if we have cached data
        if cache_key in st.session_state.cache:
            return st.session_state.cache[cache_key]
            
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
                
                # Cache the result
                st.session_state.cache[cache_key] = df
                return df

        except Exception as e:
            logger.error(f"Error fetching price data for {symbol}: {e}")
        return None

    def analyze_post_event_behavior(self, funding_data, price_data, windows=[1, 4, 8, 24, 48]):
        """Analyze price behavior after significant funding rate differentials"""
        if funding_data is None or price_data is None or price_data.empty:
            return None
            
        # Get significant events with timestamps
        significant_events = funding_data['significant_df'].copy()
        
        # If there are no significant events with the current threshold but we have data
        # we still want to return the data structure for UI consistency
        if significant_events.empty:
            return {
                'data': funding_data['funding_df'],
                'events': pd.DataFrame(),
                'stats': {
                    'symbol': funding_data['symbol'],
                    'total_intervals': funding_data['total_intervals'],
                    'significant_events': 0,
                    'has_significant_diff': False,
                    'avg_rate_diff': funding_data['funding_df']['rate_diff'].mean() if 'rate_diff' in funding_data['funding_df'].columns else 0,
                    'max_rate_diff': funding_data['funding_df']['rate_diff'].max() if 'rate_diff' in funding_data['funding_df'].columns else 0,
                    'min_rate_diff': funding_data['funding_df']['rate_diff'].min() if 'rate_diff' in funding_data['funding_df'].columns else 0,
                    'threshold': funding_data.get('threshold', 0)
                }
            }

        # Calculate forward-looking returns for each event
        all_event_returns = []
        
        for _, event in significant_events.iterrows():
            event_time = event['interval']
            event_diff = event['rate_diff']
            
            # Find the price at event time
            event_price_idx = price_data['interval'].searchsorted(event_time)
            
            if event_price_idx >= len(price_data):
                continue  # Skip if event is after the last price point
                
            event_price = price_data.iloc[event_price_idx]['close']
            
            # Get future prices for each window
            future_returns = {}
            for window in windows:
                if event_price_idx + window < len(price_data):
                    future_price = price_data.iloc[event_price_idx + window]['close']
                    future_returns[f'return_{window}h'] = ((future_price / event_price) - 1) * 100
                else:
                    future_returns[f'return_{window}h'] = None
            
            # Add event details
            event_data = {
                'event_time': event_time,
                'rate_diff': event_diff,
                'hl_rate': event['hl_rate'],
                'binance_rate': event['binance_rate'],
                'start_price': event_price
            }
            event_data.update(future_returns)
            
            all_event_returns.append(event_data)
        
        # Create events dataframe
        events_df = pd.DataFrame(all_event_returns)
        
        if events_df.empty:
            return {
                'data': funding_data['funding_df'],
                'events': pd.DataFrame(),
                'stats': {
                    'symbol': funding_data['symbol'],
                    'total_intervals': funding_data['total_intervals'],
                    'significant_events': 0,
                    'has_significant_diff': False,
                    'avg_rate_diff': funding_data['funding_df']['rate_diff'].mean(),
                    'max_rate_diff': funding_data['funding_df']['rate_diff'].max(),
                    'min_rate_diff': funding_data['funding_df']['rate_diff'].min(),
                    'threshold': funding_data.get('threshold', 0)
                }
            }
        
        # Calculate statistics
        stats = {
            'symbol': funding_data['symbol'],
            'total_intervals': funding_data['total_intervals'],
            'significant_events': len(events_df),
            'has_significant_diff': len(events_df) > 0,
            'avg_rate_diff': events_df['rate_diff'].mean(),
            'max_rate_diff': events_df['rate_diff'].max(),
            'min_rate_diff': events_df['rate_diff'].min(),
            'threshold': funding_data.get('threshold', 0)
        }
        
        # Calculate return statistics for each window
        for window in windows:
            column = f'return_{window}h'
            valid_returns = events_df[column].dropna()
            
            if not valid_returns.empty:
                stats.update({
                    f'avg_{window}h_return': valid_returns.mean(),
                    f'median_{window}h_return': valid_returns.median(),
                    f'pos_{window}h_return_pct': (valid_returns > 0).mean() * 100,
                    f'count_{window}h_valid': len(valid_returns)
                })
            else:
                stats.update({
                    f'avg_{window}h_return': None,
                    f'median_{window}h_return': None,
                    f'pos_{window}h_return_pct': None,
                    f'count_{window}h_valid': 0
                })
        
        # Calculate additional metrics by direction of funding differential
        positive_diffs = events_df[events_df['rate_diff'] > 0]
        negative_diffs = events_df[events_df['rate_diff'] < 0]
        
        for window in windows:
            column = f'return_{window}h'
            
            # Positive differentials
            pos_returns = positive_diffs[column].dropna()
            if not pos_returns.empty:
                stats.update({
                    f'pos_diff_{window}h_avg': pos_returns.mean(),
                    f'pos_diff_{window}h_win_rate': (pos_returns > 0).mean() * 100,
                    f'pos_diff_{window}h_count': len(pos_returns)
                })
            else:
                stats.update({
                    f'pos_diff_{window}h_avg': None,
                    f'pos_diff_{window}h_win_rate': None,
                    f'pos_diff_{window}h_count': 0
                })
                
            # Negative differentials  
            neg_returns = negative_diffs[column].dropna()
            if not neg_returns.empty:
                stats.update({
                    f'neg_diff_{window}h_avg': neg_returns.mean(),
                    f'neg_diff_{window}h_win_rate': (neg_returns > 0).mean() * 100,
                    f'neg_diff_{window}h_count': len(neg_returns)
                })
            else:
                stats.update({
                    f'neg_diff_{window}h_avg': None,
                    f'neg_diff_{window}h_win_rate': None,
                    f'neg_diff_{window}h_count': 0
                })
        
        return {
            'data': funding_data['funding_df'],
            'events': events_df,
            'stats': stats
        }

    def create_post_event_plots(self, results, symbol):
        """Create plots focusing on post-event price behavior"""
        plots = {}
        stats = results['stats']
        events_df = results['events']
        
        if events_df.empty:
            return {}
        
        # Rate differential distribution
        diff_dist_fig = px.histogram(
            events_df, 
            x='rate_diff',
            nbins=20,
            title=f'Distribution of Funding Rate Differentials - {symbol} (in %)',
            labels={'rate_diff': 'Rate Differential (% annualized)'},
            color_discrete_sequence=['rgba(55, 83, 109, 0.7)']
        )
        diff_dist_fig.update_layout(template='plotly_white', bargap=0.1)
        plots['diff_distribution'] = diff_dist_fig
        
        # Return distribution for different windows
        for window in [1, 4, 8, 24, 48]:
            column = f'return_{window}h'
            
            if column not in events_df.columns or events_df[column].dropna().empty:
                continue
                
            ret_dist_fig = px.histogram(
                events_df.dropna(subset=[column]), 
                x=column,
                nbins=20,
                title=f'Distribution of {window}h Returns After Significant Funding Differential - {symbol}',
                labels={column: f'{window}h Return (%)'},
                color_discrete_sequence=['rgba(83, 109, 55, 0.7)']
            )
            ret_dist_fig.update_layout(template='plotly_white', bargap=0.1)
            ret_dist_fig.add_vline(x=0, line_dash="dash", line_color="red")
            
            plots[f'return_dist_{window}h'] = ret_dist_fig
            
            # Scatter plot of differential vs return
            scatter_fig = px.scatter(
                events_df.dropna(subset=[column]),
                x='rate_diff',
                y=column,
                color='rate_diff',
                color_continuous_scale='RdBu',
                title=f'Rate Differential vs {window}h Return - {symbol}',
                labels={
                    'rate_diff': 'Rate Differential (% annualized)',
                    column: f'{window}h Return (%)'
                }
            )
            scatter_fig.update_layout(template='plotly_white')
            scatter_fig.add_hline(y=0, line_dash="dash", line_color="black")
            scatter_fig.add_vline(x=0, line_dash="dash", line_color="black")
            
            # Add trend line
            scatter_fig.update_traces(marker=dict(size=12, opacity=0.7))
            
            plots[f'scatter_{window}h'] = scatter_fig
            
        # Create cumulative return comparison chart
        if not events_df.empty:
            # Create comparison bars for different time windows
            windows = [1, 4, 8, 24, 48]
            valid_windows = [w for w in windows if f'avg_{w}h_return' in stats and stats[f'avg_{w}h_return'] is not None]
            
            if valid_windows:
                # Create dataframes for positive and negative differential returns
                pos_data = {
                    'window': [f'{w}h' for w in valid_windows],
                    'avg_return': [stats.get(f'pos_diff_{w}h_avg', 0) or 0 for w in valid_windows],
                    'win_rate': [stats.get(f'pos_diff_{w}h_win_rate', 0) or 0 for w in valid_windows],
                    'count': [stats.get(f'pos_diff_{w}h_count', 0) or 0 for w in valid_windows],
                    'diff_type': ['Positive Differential'] * len(valid_windows)
                }
                
                neg_data = {
                    'window': [f'{w}h' for w in valid_windows],
                    'avg_return': [stats.get(f'neg_diff_{w}h_avg', 0) or 0 for w in valid_windows],
                    'win_rate': [stats.get(f'neg_diff_{w}h_win_rate', 0) or 0 for w in valid_windows],
                    'count': [stats.get(f'neg_diff_{w}h_count', 0) or 0 for w in valid_windows],
                    'diff_type': ['Negative Differential'] * len(valid_windows)
                }
                
                compare_df = pd.concat([
                    pd.DataFrame(pos_data),
                    pd.DataFrame(neg_data)
                ])
                
                # Returns by differential direction
                returns_by_direction = px.bar(
                    compare_df,
                    x='window',
                    y='avg_return',
                    color='diff_type',
                    barmode='group',
                    title=f'Average Returns by Funding Differential Direction - {symbol}',
                    labels={
                        'window': 'Time Window',
                        'avg_return': 'Average Return (%)',
                        'diff_type': 'Differential Type'
                    },
                    color_discrete_map={
                        'Positive Differential': 'rgba(22, 96, 167, 0.8)',
                        'Negative Differential': 'rgba(214, 39, 40, 0.8)'
                    },
                    text='avg_return'
                )
                returns_by_direction.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
                returns_by_direction.update_layout(
                    template='plotly_white',
                    uniformtext_minsize=8,
                    uniformtext_mode='hide',
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    )
                )
                returns_by_direction.add_hline(y=0, line_dash="solid", line_color="black")
                plots['returns_by_direction'] = returns_by_direction
                
                # Win rate by differential direction
                winrate_by_direction = px.bar(
                    compare_df,
                    x='window',
                    y='win_rate',
                    color='diff_type',
                    barmode='group',
                    title=f'Win Rate by Funding Differential Direction - {symbol}',
                    labels={
                        'window': 'Time Window',
                        'win_rate': 'Win Rate (%)',
                        'diff_type': 'Differential Type'
                    },
                    color_discrete_map={
                        'Positive Differential': 'rgba(22, 96, 167, 0.8)',
                        'Negative Differential': 'rgba(214, 39, 40, 0.8)'
                    },
                    text='win_rate'
                )
                winrate_by_direction.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
                winrate_by_direction.update_layout(
                    template='plotly_white',
                    uniformtext_minsize=8,
                    uniformtext_mode='hide',
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    )
                )
                winrate_by_direction.add_hline(y=50, line_dash="dash", line_color="black")
                plots['winrate_by_direction'] = winrate_by_direction
            
        return plots


async def main():
    st.set_page_config(page_title="Funding Rate Analysis", layout="wide", page_icon="📊")
    st.title("📊 Funding Rate Differential Analysis")
    st.caption("Analyzing arbitrage opportunities between Binance and HyperLiquid funding rates")

    # Set up log capture for display in the app
    log_output = st.empty()
    
    # Create a handler that will store logs
    log_stream = io.StringIO()
    stream_handler = logging.StreamHandler(log_stream)
    stream_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    stream_handler.setFormatter(formatter)
    
    # Add the handler to the logger
    root_logger = logging.getLogger()
    root_logger.addHandler(stream_handler)
    
    analyzer = FundingAnalyzer()
    
    # Sidebar controls
    st.sidebar.header("Analysis Settings")
    lookback_days = st.sidebar.slider("Lookback Period (days)", 7, 90, 30)
    diff_threshold = st.sidebar.slider("Differential Threshold (%)", 0, 200, 50)
    
    # Debug mode toggle
    debug_mode = st.sidebar.checkbox("Debug Mode", value=False)
    
    # Create tabs for different analysis modes
    tabs = st.tabs(["Detailed Analysis", "Quick Scan", "Debug Logs"])
    
    # Date range
    end_date = datetime(2025, 2, 26)
    start_date = end_date - timedelta(days=lookback_days)
    
    # Use the hard-coded list of supported pairs
    supported_pairs = analyzer.common_pairs
    logger.info(f"Using hard-coded list of supported pairs: {supported_pairs}")
    
    # Update log display
    if debug_mode:
        with tabs[2]:
            st.subheader("Debug Logs")
            st.text(log_stream.getvalue())

    # Detailed Analysis tab (now first tab)
    with tabs[0]:
        st.header("Detailed Analysis")
        
        # Select a specific coin
        selected_coin = st.selectbox("Select Coin", supported_pairs)
        
        analyze_button = st.button("Analyze", key="analyze_button")
        
        if analyze_button and selected_coin:
            with st.spinner(f"Analyzing {selected_coin}..."):
                # Get funding rate data - pass the threshold
                funding_data = await analyzer.get_funding_data(selected_coin, start_date, end_date, diff_threshold)
                
                if funding_data is None:
                    st.error(f"No funding data available for {selected_coin}")
                else:
                    # Get price data
                    price_data = analyzer.get_price_data(selected_coin, start_date, end_date)
                    
                    if price_data is None:
                        st.error(f"No price data available for {selected_coin}")
                    else:
                        # Analyze post-event behavior
                        results = analyzer.analyze_post_event_behavior(funding_data, price_data)
                        
                        if results:
                            stats = results['stats']
                            
                            # Display key statistics
                            st.subheader("Post-Event Behavior Analysis")
                            
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric(
                                    "Significant Events",
                                    f"{stats['significant_events']}"
                                )
                            with col2:
                                st.metric(
                                    "Average Differential", 
                                    f"{stats.get('avg_rate_diff', 0):.2f}%" if stats.get('avg_rate_diff') is not None else "N/A"
                                )
                            with col3:
                                st.metric(
                                    "Max Differential",
                                    f"{stats.get('max_rate_diff', 0):.2f}%" if stats.get('max_rate_diff') is not None else "N/A"
                                )
                            with col4:
                                st.metric(
                                    "Min Differential",
                                    f"{stats.get('min_rate_diff', 0):.2f}%" if stats.get('min_rate_diff') is not None else "N/A"
                                )
                            
                            # Create and display plots
                            plots = analyzer.create_post_event_plots(results, selected_coin)
                            
                            if plots:
                                # Returns by differential direction
                                if 'returns_by_direction' in plots:
                                    st.plotly_chart(plots['returns_by_direction'], use_container_width=True)
                                
                                # Win rate by differential direction
                                if 'winrate_by_direction' in plots:
                                    st.plotly_chart(plots['winrate_by_direction'], use_container_width=True)
                                
                                # Distribution of differentials
                                if 'diff_distribution' in plots:
                                    st.plotly_chart(plots['diff_distribution'], use_container_width=True)
                                
                                # Return distributions and scatterplots by window
                                st.subheader("Return Analysis by Time Window")
                                
                                windows = [1, 4, 8, 24, 48]
                                time_tabs = st.tabs([f"{w}h" for w in windows])
                                
                                for tab, window in zip(time_tabs, windows):
                                    with tab:
                                        col1, col2, col3 = st.columns(3)
                                        
                                        with col1:
                                            st.metric(
                                                "Average Return",
                                                f"{stats.get(f'avg_{window}h_return', 0):.2f}%" if stats.get(f'avg_{window}h_return') is not None else "N/A"
                                            )
                                        with col2:
                                            st.metric(
                                                "Win Rate",
                                                f"{stats.get(f'pos_{window}h_return_pct', 0):.2f}%" if stats.get(f'pos_{window}h_return_pct') is not None else "N/A"
                                            )
                                        with col3:
                                            st.metric(
                                                "Sample Size",
                                                f"{stats.get(f'count_{window}h_valid', 0)}"
                                            )
                                        
                                        if f'scatter_{window}h' in plots:
                                            st.plotly_chart(plots[f'scatter_{window}h'], use_container_width=True)
                                        
                                        if f'return_dist_{window}h' in plots:
                                            st.plotly_chart(plots[f'return_dist_{window}h'], use_container_width=True)
                                
                                # Event details
                                st.subheader("Event Details")
                                if not results['events'].empty:
                                    st.dataframe(
                                        results['events'].sort_values('event_time', ascending=False),
                                        use_container_width=True
                                    )
                                else:
                                    st.info("No significant events found.")
                                    
                                # Raw Data Display
                                st.subheader("Raw Funding Rate Data")
                                data_tabs = st.tabs(["Merged Data", "HyperLiquid Data", "Binance Data"])
                                
                                with data_tabs[0]:
                                    st.caption(f"Merged funding rates with differential calculation (threshold: {diff_threshold}%)")
                                    merged_df = funding_data['funding_df'].copy()
                                    merged_df['interval'] = merged_df['interval'].dt.strftime('%Y-%m-%d %H:%M:%S')
                                    st.dataframe(
                                        merged_df.sort_values('interval', ascending=False),
                                        use_container_width=True,
                                        column_config={
                                            'interval': 'Timestamp',
                                            'hl_rate': 'HyperLiquid Rate (%)',
                                            'binance_rate': 'Binance Rate (%)',
                                            'rate_diff': 'Differential (%)'
                                        }
                                    )
                                    
                                with data_tabs[1]:
                                    st.caption("Raw HyperLiquid funding rates")
                                    if 'hl_data' in funding_data and not funding_data['hl_data'].empty:
                                        hl_df = funding_data['hl_data'].copy()
                                        hl_df['timestamp'] = hl_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
                                        st.dataframe(
                                            hl_df.sort_values('timestamp', ascending=False),
                                            use_container_width=True
                                        )
                                    else:
                                        st.info("No HyperLiquid data available.")
                                        
                                with data_tabs[2]:
                                    st.caption("Raw Binance funding rates")
                                    if 'binance_data' in funding_data and not funding_data['binance_data'].empty:
                                        binance_df = funding_data['binance_data'].copy()
                                        binance_df['timestamp'] = binance_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
                                        st.dataframe(
                                            binance_df.sort_values('timestamp', ascending=False),
                                            use_container_width=True
                                        )
                                    else:
                                        st.info("No Binance data available.")
                            else:
                                st.info(f"No significant events found for {selected_coin} with threshold of {diff_threshold}%.")

    # Quick Scan tab (now second tab)
    with tabs[1]:
        st.header("Quick Scan Results")
        
        # Render a fixed table of all coins with funding rate differentials
        with st.spinner("Calculating results for all coins..."):
            # List to hold results
            all_coin_results = []
            
            # Process each coin without a scan button
            for symbol in supported_pairs:
                try:
                    # Get funding rate data - pass the threshold from UI
                    funding_data = await analyzer.get_funding_data(symbol, start_date, end_date, diff_threshold)
                    if funding_data is None:
                        continue
                    
                    # Get price data for post-event analysis
                    price_data = analyzer.get_price_data(symbol, start_date, end_date)
                    
                    # Analyze post-event behavior regardless of threshold
                    if price_data is not None:
                        results = analyzer.analyze_post_event_behavior(funding_data, price_data)
                        
                        if results:
                            stats = results['stats']
                            significant_count = stats['significant_events']
                            
                            # Include all coins in the table
                            all_coin_results.append({
                                'symbol': symbol,
                                'events': significant_count,
                                'avg_diff': round(stats.get('avg_rate_diff', 0) or 0, 2),
                                'return_8h': round(stats.get('avg_8h_return', 0) or 0, 2),
                                'win_rate_8h': round(stats.get('pos_8h_return_pct', 0) or 0, 2),
                                'pos_return': round(stats.get('pos_diff_8h_avg', 0) or 0, 2),
                                'neg_return': round(stats.get('neg_diff_8h_avg', 0) or 0, 2),
                                'has_events': significant_count > 0
                            })
                        
                except Exception as e:
                    logger.error(f"Error processing {symbol}: {e}")
                    continue
            
            # Show summary of all coins
            if all_coin_results:
                # Convert to DataFrame for display
                results_df = pd.DataFrame(all_coin_results)
                
                # Filter to only show coins with significant events if requested
                show_all = st.checkbox("Show all coins (including those with no significant events)", value=False)
                
                if not show_all:
                    filtered_df = results_df[results_df['has_events']]
                else:
                    filtered_df = results_df
                
                if not filtered_df.empty:
                    # Sort options
                    sort_options = {
                        'Number of events (high to low)': ('events', False),
                        'Average differential (high to low)': ('avg_diff', False),
                        '8h Return (high to low)': ('return_8h', False),
                        '8h Return (low to high)': ('return_8h', True),
                        'Win rate (high to low)': ('win_rate_8h', False)
                    }
                    
                    sort_by = st.selectbox("Sort by", options=list(sort_options.keys()), index=0)
                    sort_column, sort_ascending = sort_options[sort_by]
                    
                    # Sort and display
                    sorted_df = filtered_df.sort_values(sort_column, ascending=sort_ascending)
                    
                    # Display as a table
                    st.dataframe(
                        sorted_df.drop(columns=['has_events']),
                        use_container_width=True,
                        column_config={
                            'symbol': st.column_config.TextColumn('Coin'),
                            'events': st.column_config.NumberColumn('# Events'),
                            'avg_diff': st.column_config.NumberColumn('Avg Diff (%)', format="%.2f%%"),
                            'return_8h': st.column_config.NumberColumn('8h Return (%)', format="%.2f%%"),
                            'win_rate_8h': st.column_config.NumberColumn('Win Rate', format="%.2f%%"),
                            'pos_return': st.column_config.NumberColumn('+ Diff Return', format="%.2f%%"),
                            'neg_return': st.column_config.NumberColumn('- Diff Return', format="%.2f%%")
                        }
                    )
                    
                    # Allow user to select a coin for detailed analysis
                    if len(filtered_df) > 0:
                        st.subheader("Quick Analysis")
                        selected_for_detail = st.selectbox(
                            "Select a coin to view charts",
                            options=sorted_df['symbol'].tolist()
                        )
                        
                        if selected_for_detail:
                            st.info(f"Showing quick analysis for {selected_for_detail}")
                            
                            # Get detailed data for selected coin
                            funding_data = await analyzer.get_funding_data(selected_for_detail, start_date, end_date, diff_threshold)
                            price_data = analyzer.get_price_data(selected_for_detail, start_date, end_date)
                            
                            if funding_data and price_data is not None:
                                results = analyzer.analyze_post_event_behavior(funding_data, price_data)
                                
                                if results:
                                    # Display key stats
                                    stats = results['stats']
                                    
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        st.metric(
                                            "Significant Events",
                                            f"{stats['significant_events']}"
                                        )
                                    with col2:
                                        st.metric(
                                            "Avg 8h Return", 
                                            f"{stats.get('avg_8h_return', 0):.2f}%" if stats.get('avg_8h_return') is not None else "N/A"
                                        )
                                    with col3:
                                        st.metric(
                                            "Win Rate (8h)",
                                            f"{stats.get('pos_8h_return_pct', 0):.2f}%" if stats.get('pos_8h_return_pct') is not None else "N/A"
                                        )
                                    
                                    # Create and display plots
                                    plots = analyzer.create_post_event_plots(results, selected_for_detail)
                                    
                                    if 'returns_by_direction' in plots:
                                        st.plotly_chart(plots['returns_by_direction'], use_container_width=True)
                                    
                                    if 'winrate_by_direction' in plots:
                                        st.plotly_chart(plots['winrate_by_direction'], use_container_width=True)
                                    
                                    # Show the events data
                                    with st.expander("View Event Details"):
                                        st.dataframe(
                                            results['events'].sort_values('event_time', ascending=False) if not results['events'].empty else pd.DataFrame(),
                                            use_container_width=True
                                        )
                                    
                                    # Raw Data Display
                                    st.subheader("Raw Funding Rate Data")
                                    data_tabs = st.tabs(["Merged Data", "HyperLiquid Data", "Binance Data"])
                                    
                                    with data_tabs[0]:
                                        st.caption(f"Merged funding rates with differential calculation (threshold: {diff_threshold}%)")
                                        merged_df = funding_data['funding_df'].copy()
                                        merged_df['interval'] = merged_df['interval'].dt.strftime('%Y-%m-%d %H:%M:%S')
                                        st.dataframe(
                                            merged_df.sort_values('interval', ascending=False),
                                            use_container_width=True,
                                            column_config={
                                                'interval': 'Timestamp',
                                                'hl_rate': 'HyperLiquid Rate (%)',
                                                'binance_rate': 'Binance Rate (%)',
                                                'rate_diff': 'Differential (%)'
                                            }
                                        )
                                        
                                    with data_tabs[1]:
                                        st.caption("Raw HyperLiquid funding rates")
                                        if 'hl_data' in funding_data and not funding_data['hl_data'].empty:
                                            hl_df = funding_data['hl_data'].copy()
                                            hl_df['timestamp'] = hl_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
                                            st.dataframe(
                                                hl_df.sort_values('timestamp', ascending=False),
                                                use_container_width=True
                                            )
                                        else:
                                            st.info("No HyperLiquid data available.")
                                            
                                    with data_tabs[2]:
                                        st.caption("Raw Binance funding rates")
                                        if 'binance_data' in funding_data and not funding_data['binance_data'].empty:
                                            binance_df = funding_data['binance_data'].copy()
                                            binance_df['timestamp'] = binance_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
                                            st.dataframe(
                                                binance_df.sort_values('timestamp', ascending=False),
                                                use_container_width=True
                                            )
                                        else:
                                            st.info("No Binance data available.")
                            else:
                                st.error(f"Could not get complete data for {selected_for_detail}")
                else:
                    st.info(f"No coins found with significant funding rate differentials >= {diff_threshold}%")
            else:
                st.error("Failed to process any coins.")

if __name__ == "__main__":
    asyncio.run(main())