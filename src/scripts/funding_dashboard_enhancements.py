"""
Funding Dashboard Enhancements

This module provides enhanced functions for the funding strategy dashboard
without modifying the existing code. It addresses issues with price history
retrieval and adds additional features.
"""

import os
import logging
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from supabase import create_client
import ccxt
import time
import functools
from typing import List, Dict, Optional, Union, Tuple
from plotly.subplots import make_subplots
import requests
from statsmodels.tsa.stattools import acf
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Supabase client
try:
    supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    supabase_key = os.getenv("NEXT_PUBLIC_SUPABASE_KEY")
    supabase = create_client(supabase_url, supabase_key)
except Exception as e:
    logger.error(f"Error initializing Supabase client: {e}")
    supabase = None

# Initialize exchange clients
try:
    binance = ccxt.binance({'enableRateLimit': True})
except Exception as e:
    logger.error(f"Error initializing exchange clients: {e}")
    binance = None

# Cache decorator
def cache_result(ttl=3600):
    """Cache function results with TTL"""
    def decorator(func):
        cache = {}
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = str(args) + str(kwargs)
            current_time = time.time()
            
            if key in cache:
                result, timestamp = cache[key]
                if current_time - timestamp < ttl:
                    return result
            
            result = func(*args, **kwargs)
            cache[key] = (result, current_time)
            return result
            
        return wrapper
    return decorator

@cache_result(ttl=3600)
def get_enhanced_price_history(symbols: list, lookback_hours: int = None) -> pd.DataFrame:
    """
    Enhanced function to get price history with fallback options
    """
    try:
        # Set default lookback if not provided
        if lookback_hours is None or not isinstance(lookback_hours, (int, float)):
            lookback_hours = 72  # Default to 3 days
            
        # Calculate start date
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(hours=lookback_hours)
        
        # Since the crypto_historical table doesn't exist, go directly to the exchange API
        logger.info("Using exchange API for price history data")
        return get_price_from_exchange_api(symbols, lookback_hours)
        
    except Exception as e:
        logger.error(f"Error in get_enhanced_price_history: {e}")
        return pd.DataFrame()

def get_price_from_exchange_api(symbols: list, lookback_hours: int = 72) -> pd.DataFrame:
    """
    Get price history directly from exchange APIs using concurrent requests
    """
    try:
        if not symbols:
            logger.warning("No symbols provided for price history")
            return pd.DataFrame()
            
        # Initialize Binance client
        binance = ccxt.binance({
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future',
                'adjustForTimeDifference': True
            }
        })
        
        # Calculate time range
        end_time = int(time.time() * 1000)
        start_time = end_time - (lookback_hours * 60 * 60 * 1000)
        
        all_price_data = []
        
        # Use ThreadPoolExecutor for concurrent requests
        with ThreadPoolExecutor(max_workers=min(10, len(symbols))) as executor:
            # Create futures for Binance requests
            binance_futures = {
                executor.submit(fetch_binance_price, binance, symbol, start_time, end_time): symbol 
                for symbol in symbols
            }
            
            # Process Binance results as they complete
            for future in as_completed(binance_futures):
                symbol = binance_futures[future]
                try:
                    result = future.result()
                    if result is not None and not result.empty:
                        all_price_data.append(result)
                        logger.info(f"Retrieved {len(result)} price points for {symbol} from Binance")
                    else:
                        logger.warning(f"No price data retrieved for {symbol} from Binance")
                except Exception as e:
                    logger.warning(f"Error fetching price data for {symbol} from Binance: {e}")
            
            # Create futures for Hyperliquid requests for symbols that failed with Binance
            failed_symbols = [s for s in symbols if not any(df['symbol'].iloc[0] == s for df in all_price_data if not df.empty)]
            
            if failed_symbols:
                hyperliquid_futures = {
                    executor.submit(get_hyperliquid_price_history, symbol, lookback_hours): symbol 
                    for symbol in failed_symbols
                }
                
                # Process Hyperliquid results as they complete
                for future in as_completed(hyperliquid_futures):
                    symbol = hyperliquid_futures[future]
                    try:
                        result = future.result()
                        if result is not None and not result.empty:
                            all_price_data.append(result)
                            logger.info(f"Retrieved {len(result)} price points for {symbol} from Hyperliquid")
                        else:
                            logger.warning(f"No price data retrieved for {symbol} from Hyperliquid")
                    except Exception as e:
                        logger.warning(f"Error fetching price data for {symbol} from Hyperliquid: {e}")
        
        # Combine all data
        if all_price_data:
            combined_df = pd.concat(all_price_data, ignore_index=True)
            return combined_df
        else:
            logger.warning("No price data retrieved from any exchange")
            return pd.DataFrame()
            
    except Exception as e:
        logger.error(f"Error in get_price_from_exchange_api: {e}")
        return pd.DataFrame()

def fetch_binance_price(binance, symbol, start_time, end_time):
    """Helper function to fetch price data from Binance for a single symbol"""
    try:
        # Format symbol for Binance
        binance_symbol = f"{symbol}/USDT"
        
        # Fetch OHLCV data
        ohlcv = binance.fetch_ohlcv(
            binance_symbol,
            timeframe='1h',
            since=start_time,
            limit=1000  # Most exchanges limit to 1000 candles per request
        )
        
        if ohlcv:
            # Convert to DataFrame
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
            df['symbol'] = symbol
            df['exchange'] = 'Binance'
            df['price'] = df['close']
            
            return df
        else:
            return pd.DataFrame()
    except Exception as e:
        logger.warning(f"Error in fetch_binance_price for {symbol}: {e}")
        return pd.DataFrame()

def get_hyperliquid_price_history(symbol: str, lookback_hours: int = 72) -> pd.DataFrame:
    """
    Get price history for a symbol from Hyperliquid
    """
    try:
        # Calculate time range
        end_time = int(time.time())
        start_time = end_time - (lookback_hours * 60 * 60)
        
        # Hyperliquid API endpoint for candles
        url = "https://api.hyperliquid.xyz/info"
        
        # Request payload for candles
        payload = {
            "type": "candleSnapshot",
            "coin": symbol,
            "interval": "1h",
            "startTime": start_time,
            "endTime": end_time
        }
        
        # Headers
        headers = {
            "Content-Type": "application/json"
        }
        
        # Make the API call with timeout
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        # Check if the request was successful
        if response.status_code != 200:
            logger.error(f"Failed to fetch Hyperliquid candles: HTTP {response.status_code}")
            return pd.DataFrame()
        
        # Parse the response
        data = response.json()
        
        if not data or not isinstance(data, list):
            logger.error("Invalid response format from Hyperliquid API for candles")
            return pd.DataFrame()
        
        # Convert to DataFrame
        candles = []
        for candle in data:
            try:
                timestamp = int(candle[0]) * 1000  # Convert to milliseconds
                open_price = float(candle[1])
                high_price = float(candle[2])
                low_price = float(candle[3])
                close_price = float(candle[4])
                volume = float(candle[5])
                
                candles.append({
                    'timestamp': timestamp,
                    'open': open_price,
                    'high': high_price,
                    'low': low_price,
                    'close': close_price,
                    'volume': volume,
                    'datetime': pd.to_datetime(timestamp, unit='ms', utc=True),
                    'symbol': symbol,
                    'exchange': 'Hyperliquid',
                    'price': close_price
                })
            except Exception as e:
                logger.warning(f"Error processing Hyperliquid candle: {e}")
                continue
        
        if candles:
            return pd.DataFrame(candles)
        else:
            return pd.DataFrame()
        
    except Exception as e:
        logger.error(f"Error in get_hyperliquid_price_history: {e}")
        return pd.DataFrame()

@cache_result(ttl=3600)
def get_enhanced_funding_data(lookback_hours=None):
    """
    Enhanced function to get funding rate data with fallback options
    """
    try:
        # Set default lookback if not provided
        if lookback_hours is None or not isinstance(lookback_hours, (int, float)):
            lookback_hours = 72  # Default to 3 days
        
        # Calculate start date
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(hours=lookback_hours)
        
        # Try to get data from funding_rate_data
        try:
            logger.info(f"Fetching funding data from Supabase for the last {lookback_hours} hours")
            
            # Query in batches to handle large datasets
            BATCH_SIZE = 1000
            all_data = []
            last_id = 0
            
            while True:
                query = supabase.table('funding_rate_data') \
                    .select('*') \
                    .gte('timestamp', start_date.isoformat()) \
                    .lte('timestamp', end_date.isoformat()) \
                    .order('id') \
                    .gt('id', last_id) \
                    .limit(BATCH_SIZE)
                
                result = query.execute()
                
                if not result.data:
                    break
                
                all_data.extend(result.data)
                last_id = result.data[-1]['id']
                
                if len(result.data) < BATCH_SIZE:
                    break
            
            if all_data:
                logger.info(f"Retrieved {len(all_data)} records from funding_rate_data")
                df = pd.DataFrame(all_data)
                
                # Rename columns to match expected format
                column_mapping = {
                    'coin': 'symbol',
                    'predicted_funding_rate': 'predicted_rate'
                }
                
                # Only rename columns that exist
                rename_cols = {k: v for k, v in column_mapping.items() if k in df.columns}
                df = df.rename(columns=rename_cols)
                
                # Ensure all required columns exist
                required_columns = ['symbol', 'exchange', 'timestamp', 'funding_rate']
                
                # Check if we need to map 'coin' to 'symbol' if the rename didn't happen
                if 'symbol' not in df.columns and 'coin' in df.columns:
                    df['symbol'] = df['coin']
                
                # Convert timestamp columns
                timestamp_columns = ['timestamp', 'next_funding_time']
                for col in timestamp_columns:
                    if col in df.columns:
                        df[col] = pd.to_datetime(df[col])
                
                # Check if any required columns are missing
                missing_columns = [col for col in required_columns if col not in df.columns]
                if missing_columns:
                    logger.warning(f"Missing required columns in funding_rate_data: {missing_columns}")
                    
                    # Try to derive missing columns
                    if 'timestamp' not in df.columns and 'created_at' in df.columns:
                        df['timestamp'] = pd.to_datetime(df['created_at'])
                    
                    if 'symbol' not in df.columns and 'coin' in df.columns:
                        df['symbol'] = df['coin']
                
                # Final check for required columns
                missing_columns = [col for col in required_columns if col not in df.columns]
                if missing_columns:
                    logger.error(f"Still missing required columns after fixes: {missing_columns}")
                    # Continue anyway, the main function will handle this
                
                return df
                
        except Exception as e:
            logger.warning(f"Error fetching from funding_rate_data: {e}")
        
        # If we couldn't get data from the table, try to get it from the exchange API
        logger.info("Falling back to exchange API for funding data")
        return get_funding_from_exchange_api(lookback_hours)
            
    except Exception as e:
        logger.error(f"Error in get_enhanced_funding_data: {e}")
        return pd.DataFrame()

def get_funding_from_exchange_api(lookback_hours=72):
    """Get funding data from exchange API using concurrent requests"""
    try:
        # Initialize Binance client
        try:
            binance = ccxt.binance({
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'future',
                    'adjustForTimeDifference': True
                }
            })
            logger.info("Binance client initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Binance client: {e}")
            binance = None
        
        all_rates = []
        
        # Get funding rates from Binance if client is available
        if binance:
            try:
                # Load markets first
                binance.load_markets()
                markets = [s for s in binance.symbols if s.endswith(':USDT')]
                
                # Use ThreadPoolExecutor for concurrent requests
                with ThreadPoolExecutor(max_workers=min(10, len(markets))) as executor:
                    # Create futures for Binance requests
                    binance_futures = {
                        executor.submit(fetch_binance_funding_rate, binance, symbol): symbol 
                        for symbol in markets
                    }
                    
                    # Process results as they complete
                    for future in as_completed(binance_futures):
                        try:
                            result = future.result()
                            if result:
                                all_rates.append(result)
                        except Exception as e:
                            symbol = binance_futures[future]
                            logger.warning(f"Error processing Binance funding rate for {symbol}: {e}")
                
                logger.info(f"Retrieved {len(all_rates)} funding rates from Binance")
            except Exception as e:
                logger.error(f"Error getting Binance funding rates: {e}")
        
        # Get funding rates from Hyperliquid
        try:
            hyperliquid_rates = get_hyperliquid_funding_rates()
            if hyperliquid_rates:
                all_rates.extend(hyperliquid_rates)
                logger.info(f"Retrieved {len(hyperliquid_rates)} funding rates from Hyperliquid")
        except Exception as e:
            logger.error(f"Error getting Hyperliquid funding rates: {e}")
        
        if not all_rates:
            logger.error("Failed to get funding rates from any exchange")
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(all_rates)
        
        # Ensure all required columns exist
        required_columns = ['symbol', 'exchange', 'funding_rate']
        
        # Add timestamp column if not present
        if 'timestamp' not in df.columns:
            df['timestamp'] = datetime.now(timezone.utc)
        
        # Check for missing required columns
        for col in required_columns:
            if col not in df.columns:
                if col == 'symbol' and 'coin' in df.columns:
                    df['symbol'] = df['coin']
                elif col == 'funding_rate' and 'rate' in df.columns:
                    df['funding_rate'] = df['rate']
                else:
                    logger.warning(f"Missing required column {col} in API data, adding empty column")
                    df[col] = None
        
        # Convert timestamp columns to datetime
        datetime_columns = ['timestamp', 'next_funding_time']
        for col in datetime_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Fill any NaN values in required columns
        for col in required_columns:
            if col in df.columns and df[col].isna().any():
                if col == 'funding_rate':
                    df[col] = df[col].fillna(0)
                elif col == 'symbol' or col == 'exchange':
                    df = df.dropna(subset=[col])
        
        return df
        
    except Exception as e:
        logger.error(f"Error in get_funding_from_exchange_api: {e}")
        return pd.DataFrame()

def fetch_binance_funding_rate(binance, symbol):
    """Helper function to fetch funding rate from Binance for a single symbol"""
    try:
        # Extract base symbol (remove :USDT)
        base_symbol = symbol.split(':')[0]
        
        # Get funding info
        try:
            funding_info = binance.fetch_funding_rate(symbol)
            
            # Calculate next funding time if missing
            next_funding_time = None
            if 'nextFundingTime' in funding_info and funding_info['nextFundingTime']:
                next_funding_time = datetime.fromtimestamp(funding_info['nextFundingTime'] / 1000, tz=timezone.utc)
            else:
                # Calculate approximate next funding time (Binance funding is every 8 hours)
                current_time = datetime.now(timezone.utc)
                hours_to_next = 8 - (current_time.hour % 8)
                next_time = current_time.replace(minute=0, second=0, microsecond=0) + timedelta(hours=hours_to_next)
                next_funding_time = next_time
            
            # Format the data
            return {
                'exchange': 'Binance',
                'symbol': base_symbol,
                'funding_rate': funding_info['fundingRate'],
                'next_funding_time': next_funding_time,
                'timestamp': datetime.now(timezone.utc)
            }
        except Exception as e:
            # Try alternative method to get funding rate
            try:
                ticker = binance.fetch_ticker(symbol)
                if 'info' in ticker and 'lastFundingRate' in ticker['info']:
                    funding_rate = float(ticker['info']['lastFundingRate'])
                    
                    # Calculate approximate next funding time
                    current_time = datetime.now(timezone.utc)
                    hours_to_next = 8 - (current_time.hour % 8)
                    next_time = current_time.replace(minute=0, second=0, microsecond=0) + timedelta(hours=hours_to_next)
                    
                    return {
                        'exchange': 'Binance',
                        'symbol': base_symbol,
                        'funding_rate': funding_rate,
                        'next_funding_time': next_time,
                        'timestamp': datetime.now(timezone.utc)
                    }
            except Exception as ticker_error:
                logger.warning(f"Error getting Binance ticker for {symbol}: {ticker_error}")
                return None
    except Exception as e:
        logger.warning(f"Error processing Binance funding rate for {symbol}: {e}")
        return None

def get_hyperliquid_funding_rates():
    """Get funding rates from Hyperliquid using direct API call"""
    try:
        formatted_rates = []
        
        try:
            # Use direct API call
            url = "https://api.hyperliquid.xyz/info"
            
            # Request payload
            payload = {
                "type": "metaAndAssetCtxs"
            }
            
            # Headers
            headers = {
                "Content-Type": "application/json"
            }
            
            # Make the API call with timeout
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            
            # Check if the request was successful
            if response.status_code != 200:
                logger.error(f"Failed to fetch Hyperliquid data: HTTP {response.status_code}")
                return []
            
            # Parse the response
            data = response.json()
            
            # Extract universe (metadata) and asset contexts
            if not data or len(data) < 2:
                logger.error("Invalid response format from Hyperliquid API")
                return []
                
            # Validate universe data
            if not isinstance(data[0], dict) or 'universe' not in data[0]:
                logger.error("Invalid universe data in Hyperliquid API response")
                return []
                
            # Validate asset contexts data
            if not isinstance(data[1], list):
                logger.error("Invalid asset contexts data in Hyperliquid API response")
                return []
                
            universe = data[0].get('universe', [])
            asset_contexts = data[1]
            
            logger.info(f"Got {len(universe)} assets in universe and {len(asset_contexts)} asset contexts")
            
            # Map asset names to their contexts
            for i, asset_ctx in enumerate(asset_contexts):
                try:
                    if i < len(universe):
                        asset_name = universe[i].get('name')
                    else:
                        logger.warning(f"Asset context at index {i} has no corresponding universe entry")
                        continue
                        
                    if not asset_name:
                        continue
                        
                    # Get current funding rate
                    funding_rate = float(asset_ctx.get('funding', 0))
                    
                    # Get mark price
                    mark_price = float(asset_ctx.get('markPx', 0))
                    
                    # Calculate next funding time (Hyperliquid funding occurs hourly)
                    current_time = time.time()
                    next_hour = current_time - (current_time % 3600) + 3600
                    
                    formatted_rates.append({
                        'exchange': 'Hyperliquid',
                        'symbol': asset_name,
                        'funding_rate': funding_rate,
                        'next_funding_time': datetime.fromtimestamp(next_hour, tz=timezone.utc),
                        'timestamp': datetime.now(timezone.utc)
                    })
                except Exception as e:
                    logger.warning(f"Error processing Hyperliquid rate for asset at index {i}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error in Hyperliquid API call: {e}")
            return []
        
        return formatted_rates
    
    except Exception as e:
        logger.error(f"Error getting Hyperliquid funding rates: {e}")
        return []

def create_price_funding_correlation_chart(price_df, funding_df, symbol):
    """Create a chart showing correlation between price and funding rates"""
    try:
        if price_df.empty or funding_df.empty:
            return None
            
        # Filter data for the selected symbol
        price_data = price_df[price_df['symbol'] == symbol].copy()
        funding_data = funding_df[funding_df['symbol'] == symbol].copy()
        
        if price_data.empty or funding_data.empty:
            return None
        
        # Determine timestamp columns
        price_time_col = 'datetime'
        if price_time_col not in price_data.columns:
            # Try alternative column names
            for col in ['timestamp', 'created_at', 'time']:
                if col in price_data.columns:
                    price_time_col = col
                    break
        
        funding_time_col = 'timestamp'
        if funding_time_col not in funding_data.columns:
            # Try alternative column names
            for col in ['created_at', 'datetime', 'time']:
                if col in funding_data.columns:
                    funding_time_col = col
                    break
        
        # Check if we found valid timestamp columns
        if price_time_col not in price_data.columns:
            logger.error(f"No valid timestamp column found in price data for {symbol}")
            return None
            
        if funding_time_col not in funding_data.columns:
            logger.error(f"No valid timestamp column found in funding data for {symbol}")
            return None
            
        # Ensure datetime columns are in the right format
        price_data[price_time_col] = pd.to_datetime(price_data[price_time_col])
        funding_data[funding_time_col] = pd.to_datetime(funding_data[funding_time_col])
        
        # Resample price data to hourly
        price_data = price_data.set_index(price_time_col)
        price_hourly = price_data['price'].resample('1H').last().reset_index()
        
        # Resample funding data to hourly
        funding_data = funding_data.set_index(funding_time_col)
        funding_hourly = funding_data['funding_rate'].resample('1H').last().reset_index()
        
        # Merge the data
        merged_df = pd.merge_asof(
            price_hourly.sort_values(price_time_col),
            funding_hourly.sort_values(funding_time_col),
            left_on=price_time_col,
            right_on=funding_time_col,
            direction='nearest'
        )
        
        # Create the figure
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Add price line
        fig.add_trace(
            go.Scatter(
                x=merged_df[price_time_col],
                y=merged_df['price'],
                name='Price',
                line=dict(color='blue')
            ),
            secondary_y=False
        )
        
        # Add funding rate line
        fig.add_trace(
            go.Scatter(
                x=merged_df[price_time_col],
                y=merged_df['funding_rate'] * 100,  # Convert to percentage
                name='Funding Rate (%)',
                line=dict(color='red')
            ),
            secondary_y=True
        )
        
        # Calculate correlation
        correlation = merged_df['price'].corr(merged_df['funding_rate'])
        
        # Update layout
        fig.update_layout(
            title=f"{symbol} Price vs Funding Rate (Correlation: {correlation:.2f})",
            xaxis_title="Date",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            template="plotly_dark",
            height=500
        )
        
        # Update y-axes titles
        fig.update_yaxes(title_text="Price", secondary_y=False)
        fig.update_yaxes(title_text="Funding Rate (%)", secondary_y=True)
        
        return fig
        
    except Exception as e:
        logger.error(f"Error in create_price_funding_correlation_chart: {e}")
        return None

def display_enhanced_market_overview(funding_data):
    """Display enhanced market overview with additional metrics"""
    try:
        if funding_data.empty:
            st.warning("No funding data available for market overview")
            return
            
        st.subheader("📊 Enhanced Market Overview")
        
        # Get the timestamp column (could be 'timestamp' or 'created_at')
        timestamp_col = 'timestamp'
        if timestamp_col not in funding_data.columns and 'created_at' in funding_data.columns:
            timestamp_col = 'created_at'
        
        if timestamp_col not in funding_data.columns:
            st.warning("No timestamp column found in funding data. Some metrics may not be available.")
        else:
            # Calculate latest timestamp
            latest_timestamp = funding_data[timestamp_col].max()
            time_since_update = datetime.now(timezone.utc) - pd.to_datetime(latest_timestamp)
            
            # Display last update time
            st.info(f"Last data update: {time_since_update.total_seconds() / 60:.1f} minutes ago")
        
        # Calculate market-wide metrics
        total_markets = funding_data['symbol'].nunique()
        total_exchanges = funding_data['exchange'].nunique()
        
        # Calculate average funding rates by exchange
        exchange_rates = funding_data.groupby('exchange')['funding_rate'].mean() * 100  # Convert to percentage
        
        # Calculate volatility of funding rates
        funding_volatility = funding_data.groupby('symbol')['funding_rate'].std() * 100  # Convert to percentage
        avg_volatility = funding_volatility.mean()
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Markets", f"{total_markets}")
            
        with col2:
            st.metric("Total Exchanges", f"{total_exchanges}")
            
        with col3:
            st.metric("Avg. Funding Rate", f"{funding_data['funding_rate'].mean() * 100:.4f}%")
            
        with col4:
            st.metric("Funding Volatility", f"{avg_volatility:.4f}%")
            
        # Display exchange comparison
        st.subheader("Exchange Funding Rate Comparison")
        
        exchange_fig = px.bar(
            exchange_rates.reset_index(),
            x='exchange',
            y='funding_rate',
            color='exchange',
            labels={'funding_rate': 'Average Funding Rate (%)', 'exchange': 'Exchange'},
            title="Average Funding Rate by Exchange"
        )
        
        exchange_fig.update_layout(template="plotly_dark")
        st.plotly_chart(exchange_fig, use_container_width=True)
        
        # Display funding rate distribution
        st.subheader("Funding Rate Distribution")
        
        # Create histogram
        hist_fig = px.histogram(
            funding_data,
            x='funding_rate',
            nbins=50,
            title="Current Funding Rate Distribution",
            labels={'funding_rate': 'Funding Rate'},
            color_discrete_sequence=['blue']
        )
        
        # Update layout
        hist_fig.update_layout(
            xaxis_title="Funding Rate",
            yaxis_title="Count",
            template="plotly_dark"
        )
        
        # Add vertical line at zero
        hist_fig.add_vline(
            x=0,
            line_dash="dash",
            line_color="red",
            annotation_text="Zero Line",
            annotation_position="top right"
        )
        
        st.plotly_chart(hist_fig, use_container_width=True)
        
        # Display top volatile assets
        st.subheader("Top Volatile Assets")
        
        top_volatile = funding_volatility.nlargest(10).reset_index()
        top_volatile.columns = ['Symbol', 'Funding Volatility (%)']
        
        volatile_fig = px.bar(
            top_volatile,
            x='Symbol',
            y='Funding Volatility (%)',
            color='Funding Volatility (%)',
            color_continuous_scale='Viridis',
            title="Top 10 Assets by Funding Rate Volatility"
        )
        
        volatile_fig.update_layout(template="plotly_dark")
        st.plotly_chart(volatile_fig, use_container_width=True)
        
        # Display top positive and negative funding rates
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Highest Funding Rates")
            
            # Get top positive funding rates
            top_positive = funding_data.sort_values('funding_rate', ascending=False).head(10)
            
            # Format for display
            top_positive_display = top_positive[['symbol', 'exchange', 'funding_rate']].copy()
            top_positive_display['funding_rate'] = top_positive_display['funding_rate'] * 100  # Convert to percentage
            
            # Display table
            st.dataframe(
                top_positive_display.style.format({'funding_rate': '{:.4f}%'}),
                use_container_width=True
            )
            
        with col2:
            st.subheader("Lowest Funding Rates")
            
            # Get top negative funding rates
            top_negative = funding_data.sort_values('funding_rate').head(10)
            
            # Format for display
            top_negative_display = top_negative[['symbol', 'exchange', 'funding_rate']].copy()
            top_negative_display['funding_rate'] = top_negative_display['funding_rate'] * 100  # Convert to percentage
            
            # Display table
            st.dataframe(
                top_negative_display.style.format({'funding_rate': '{:.4f}%'}),
                use_container_width=True
            )
        
    except Exception as e:
        logger.error(f"Error in display_enhanced_market_overview: {e}")
        st.error(f"Error displaying enhanced market overview: {e}")
        # Fall back to basic display
        try:
            from src.scripts.funding_strategy_dashboard import display_market_overview
            display_market_overview(funding_data)
        except Exception as fallback_error:
            logger.error(f"Error in fallback display_market_overview: {fallback_error}")
            st.error("Could not display market overview. Please check the data format.")

def display_funding_price_analysis(funding_data, price_data):
    """Display analysis of funding rates vs price movements"""
    try:
        if funding_data.empty:
            st.warning("No funding data available for analysis")
            return
            
        st.subheader("🔄 Funding Rate vs Price Analysis")
        
        # Check if price data is available
        if price_data is None or price_data.empty:
            st.warning("No price data available for correlation analysis")
            st.info("Displaying funding rate analysis only")
            has_price_data = False
        else:
            has_price_data = True
        
        # Get unique symbols
        symbols = funding_data['symbol'].unique().tolist()
        
        # Let user select a symbol
        selected_symbol = st.selectbox(
            "Select Symbol for Analysis",
            options=symbols,
            index=0 if 'BTC' in symbols else 0
        )
        
        # Create correlation chart if price data is available
        if has_price_data:
            correlation_chart = create_price_funding_correlation_chart(
                price_data, 
                funding_data, 
                selected_symbol
            )
            
            if correlation_chart:
                st.plotly_chart(correlation_chart, use_container_width=True)
            else:
                st.warning(f"Insufficient data to create correlation chart for {selected_symbol}")
        else:
            st.info("Price data is required to display correlation chart. Only showing funding rate statistics.")
            
        # Calculate funding rate statistics for the selected symbol
        symbol_data = funding_data[funding_data['symbol'] == selected_symbol]
        
        if not symbol_data.empty:
            # Calculate statistics
            avg_rate = symbol_data['funding_rate'].mean() * 100  # Convert to percentage
            max_rate = symbol_data['funding_rate'].max() * 100
            min_rate = symbol_data['funding_rate'].min() * 100
            volatility = symbol_data['funding_rate'].std() * 100
            
            # Display statistics
            st.subheader(f"{selected_symbol} Funding Rate Statistics")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Average Rate", f"{avg_rate:.4f}%")
                
            with col2:
                st.metric("Maximum Rate", f"{max_rate:.4f}%")
                
            with col3:
                st.metric("Minimum Rate", f"{min_rate:.4f}%")
                
            with col4:
                st.metric("Volatility", f"{volatility:.4f}%")
                
            # Create histogram of funding rates
            hist_fig = px.histogram(
                symbol_data,
                x='funding_rate',
                nbins=20,
                title=f"{selected_symbol} Funding Rate Distribution",
                labels={'funding_rate': 'Funding Rate'},
                color_discrete_sequence=['blue']
            )
            
            hist_fig.update_layout(template="plotly_dark")
            st.plotly_chart(hist_fig, use_container_width=True)
            
            # Display funding rate over time if timestamp column exists
            timestamp_col = None
            for col in ['timestamp', 'created_at', 'datetime']:
                if col in symbol_data.columns:
                    timestamp_col = col
                    break
                    
            if timestamp_col:
                # Create time series chart
                time_data = symbol_data.copy()
                time_data[timestamp_col] = pd.to_datetime(time_data[timestamp_col])
                time_data = time_data.sort_values(by=timestamp_col)
                
                time_fig = px.line(
                    time_data,
                    x=timestamp_col,
                    y='funding_rate',
                    title=f"{selected_symbol} Funding Rate Over Time",
                    labels={'funding_rate': 'Funding Rate', timestamp_col: 'Time'},
                    color_discrete_sequence=['green']
                )
                
                # Convert y-axis to percentage
                time_fig.update_layout(
                    yaxis_tickformat='.2%',
                    template="plotly_dark"
                )
                
                st.plotly_chart(time_fig, use_container_width=True)
            else:
                st.warning("No timestamp data available to display funding rate over time")
        else:
            st.warning(f"No funding data available for {selected_symbol}")
            
    except Exception as e:
        logger.error(f"Error in display_funding_price_analysis: {e}")
        st.error(f"Error displaying funding price analysis: {e}")

def display_volatility_clustering_analysis(volatility_df: pd.DataFrame):
    """
    Display volatility clustering analysis results
    """
    try:
        if volatility_df.empty:
            st.warning("No data available for volatility clustering analysis")
            return
            
        st.subheader("Volatility Clustering Analysis")
        
        # Summary metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            high_vol = (volatility_df['volatility'] > volatility_df['volatility'].median()).sum()
            st.metric(
                "High Volatility Markets",
                f"{high_vol}/{len(volatility_df)}",
                help="Markets with above-median volatility"
            )
            
        with col2:
            if 'vol_persistence' in volatility_df.columns:
                avg_persistence = volatility_df['vol_persistence'].mean()
                st.metric(
                    "Average Persistence",
                    f"{avg_persistence:.2f}",
                    help="Mean volatility persistence across markets"
                )
            else:
                st.metric(
                    "Average Persistence",
                    "N/A",
                    help="Volatility persistence data not available"
                )
            
        with col3:
            if 'clustering_score' in volatility_df.columns:
                strong_cluster = (volatility_df['clustering_score'] > volatility_df['clustering_score'].median()).sum()
                st.metric(
                    "Strong Clustering",
                    f"{strong_cluster}/{len(volatility_df)}",
                    help="Markets with strong volatility clustering"
                )
            else:
                st.metric(
                    "Strong Clustering",
                    "N/A",
                    help="Clustering score data not available"
                )
            
        # Interactive filters
        col1, col2 = st.columns(2)
        with col1:
            sort_options = ['Volatility']
            if 'vol_persistence' in volatility_df.columns:
                sort_options.append('Persistence')
            if 'clustering_score' in volatility_df.columns:
                sort_options.append('Clustering Score')
                
            sort_by = st.selectbox(
                "Sort by",
                sort_options,
                key='vol_sort'
            )
        with col2:
            min_vol = st.slider(
                "Minimum Volatility",
                min_value=0.0,
                max_value=float(volatility_df['volatility'].max()),
                value=0.0,
                key='vol_filter'
            )
            
        # Filter and sort data
        filtered_df = volatility_df[volatility_df['volatility'] >= min_vol].copy()
        
        sort_map = {
            'Volatility': 'volatility',
            'Persistence': 'vol_persistence',
            'Clustering Score': 'clustering_score'
        }
        
        if sort_by in sort_map and sort_map[sort_by] in filtered_df.columns:
            filtered_df = filtered_df.sort_values(sort_map[sort_by], ascending=False)
        
        # Display results table
        if not filtered_df.empty:
            # Format the DataFrame for display
            display_df = filtered_df.copy()
            
            # Ensure all required columns exist
            for col in ['volatility', 'vol_persistence', 'vol_trend', 'clustering_score']:
                if col not in display_df.columns:
                    display_df[col] = None
            
            # Format the DataFrame
            format_dict = {}
            if 'volatility' in display_df.columns:
                format_dict['volatility'] = '{:.2f}%'
            if 'vol_persistence' in display_df.columns:
                format_dict['vol_persistence'] = '{:.2f}'
            if 'vol_trend' in display_df.columns:
                format_dict['vol_trend'] = '{:.2f}%'
            if 'clustering_score' in display_df.columns:
                format_dict['clustering_score'] = '{:.2f}'
            
            st.dataframe(
                display_df.style.format(format_dict),
                use_container_width=True
            )
            
            # Visualization
            st.subheader("Volatility Patterns")
            
            if 'vol_persistence' in display_df.columns and 'volatility' in display_df.columns:
                fig = px.scatter(
                    display_df,
                    x='vol_persistence',
                    y='volatility',
                    color='symbol',
                    hover_data=['symbol', 'vol_trend'] if 'vol_trend' in display_df.columns else ['symbol'],
                    title='Volatility Clustering Map'
                )
                
                fig.update_layout(
                    xaxis_title="Volatility Persistence",
                    yaxis_title="Current Volatility (%)",
                    height=500
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Insufficient data for volatility clustering visualization")
        else:
            st.info("No data matches the current filters")
            
    except Exception as e:
        logger.error(f"Error in display_volatility_clustering_analysis: {e}")
        st.error("Error displaying volatility clustering analysis")

def display_arbitrage_efficiency_analysis(arbitrage_df: pd.DataFrame):
    """
    Display arbitrage efficiency analysis results
    """
    try:
        if arbitrage_df.empty:
            st.warning("No data available for arbitrage efficiency analysis")
            return
            
        st.subheader("Arbitrage Efficiency Analysis")
        
        # Check if required columns exist
        required_columns = ['symbol', 'efficiency_score', 'funding_volatility', 'convergence_speed']
        missing_columns = [col for col in required_columns if col not in arbitrage_df.columns]
        
        if missing_columns:
            st.warning(f"Missing data columns: {', '.join(missing_columns)}")
            st.info("Limited analysis available due to missing data")
        
        # Summary metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if 'efficiency_score' in arbitrage_df.columns:
                efficient_markets = (arbitrage_df['efficiency_score'] > arbitrage_df['efficiency_score'].median()).sum()
                st.metric(
                    "Efficient Markets",
                    f"{efficient_markets}/{len(arbitrage_df)}",
                    help="Markets with above-median efficiency"
                )
            else:
                st.metric("Efficient Markets", "N/A", help="Efficiency score data not available")
            
        with col2:
            if 'efficiency_score' in arbitrage_df.columns:
                avg_efficiency = arbitrage_df['efficiency_score'].mean()
                st.metric(
                    "Average Efficiency",
                    f"{avg_efficiency:.2f}",
                    help="Mean efficiency score across markets"
                )
            else:
                st.metric("Average Efficiency", "N/A", help="Efficiency score data not available")
            
        with col3:
            if 'convergence_speed' in arbitrage_df.columns:
                fast_convergence = (arbitrage_df['convergence_speed'] > arbitrage_df['convergence_speed'].median()).sum()
                st.metric(
                    "Fast Convergence",
                    f"{fast_convergence}/{len(arbitrage_df)}",
                    help="Markets with above-median convergence speed"
                )
            else:
                st.metric("Fast Convergence", "N/A", help="Convergence speed data not available")
        
        # Display results table
        format_dict = {}
        for col in arbitrage_df.columns:
            if col in ['funding_volatility', 'convergence_speed', 'efficiency_score']:
                format_dict[col] = '{:.4f}'
        
        st.dataframe(
            arbitrage_df.style.format(format_dict),
            use_container_width=True
        )
        
        # Visualization
        if all(col in arbitrage_df.columns for col in ['funding_volatility', 'convergence_speed', 'efficiency_score']):
            st.subheader("Efficiency Analysis")
            
            fig = px.scatter(
                arbitrage_df,
                x='funding_volatility',
                y='convergence_speed',
                color='efficiency_score',
                hover_data=['symbol'],
                title='Market Efficiency Map'
            )
            
            fig.update_layout(
                xaxis_title="Funding Volatility",
                yaxis_title="Convergence Speed",
                coloraxis_colorbar_title="Efficiency Score",
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        logger.error(f"Error in display_arbitrage_efficiency_analysis: {e}")
        st.error("Error displaying arbitrage efficiency analysis")

def display_funding_reversal_analysis(reversal_df: pd.DataFrame):
    """
    Display funding reversal analysis results
    """
    try:
        if reversal_df.empty:
            st.warning("No data available for funding reversal analysis")
            return
            
        st.subheader("Funding Rate Reversal Analysis")
        
        # Check if required columns exist
        required_columns = ['symbol', 'reversal_probability', 'current_rate', 'trend', 'momentum']
        missing_columns = [col for col in required_columns if col not in reversal_df.columns]
        
        if missing_columns:
            st.warning(f"Missing data columns: {', '.join(missing_columns)}")
            st.info("Limited analysis available due to missing data")
        
        # Summary metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if 'reversal_probability' in reversal_df.columns:
                high_prob = (reversal_df['reversal_probability'] > 0.7).sum()
                st.metric(
                    "High Probability Reversals",
                    f"{high_prob}/{len(reversal_df)}",
                    help="Markets with >70% reversal probability"
                )
            else:
                st.metric("High Probability Reversals", "N/A", help="Reversal probability data not available")
            
        with col2:
            if 'reversal_probability' in reversal_df.columns:
                avg_prob = reversal_df['reversal_probability'].mean()
                st.metric(
                    "Average Probability",
                    f"{avg_prob:.2%}",
                    help="Mean reversal probability across markets"
                )
            else:
                st.metric("Average Probability", "N/A", help="Reversal probability data not available")
            
        with col3:
            if 'momentum' in reversal_df.columns:
                strong_momentum = (abs(reversal_df['momentum']) > reversal_df['momentum'].std()).sum()
                st.metric(
                    "Strong Momentum",
                    f"{strong_momentum}/{len(reversal_df)}",
                    help="Markets with significant momentum"
                )
            else:
                st.metric("Strong Momentum", "N/A", help="Momentum data not available")
        
        # Filter for high probability reversals if possible
        if 'reversal_probability' in reversal_df.columns:
            high_prob_df = reversal_df[reversal_df['reversal_probability'] > 0.5].sort_values('reversal_probability', ascending=False)
            
            if not high_prob_df.empty:
                st.subheader("Potential Reversals")
                
                format_dict = {}
                if 'current_rate' in high_prob_df.columns:
                    format_dict['current_rate'] = '{:.4%}'
                if 'trend' in high_prob_df.columns:
                    format_dict['trend'] = '{:.4f}'
                if 'momentum' in high_prob_df.columns:
                    format_dict['momentum'] = '{:.4f}'
                if 'reversal_probability' in high_prob_df.columns:
                    format_dict['reversal_probability'] = '{:.2%}'
                
                st.dataframe(
                    high_prob_df.style.format(format_dict),
                    use_container_width=True
                )
                
                # Visualization
                if all(col in high_prob_df.columns for col in ['trend', 'momentum', 'reversal_probability']):
                    fig = px.scatter(
                        high_prob_df,
                        x='trend',
                        y='momentum',
                        color='reversal_probability',
                        hover_data=['symbol', 'current_rate'] if 'current_rate' in high_prob_df.columns else ['symbol'],
                        title='Reversal Probability Map'
                    )
                    
                    fig.update_layout(
                        xaxis_title="Current Trend",
                        yaxis_title="Momentum",
                        coloraxis_colorbar_title="Reversal Probability",
                        height=500
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No high-probability reversals detected at this time")
        else:
            st.dataframe(reversal_df, use_container_width=True)
            
    except Exception as e:
        logger.error(f"Error in display_funding_reversal_analysis: {e}")
        st.error("Error displaying funding reversal analysis")

def analyze_volatility_clustering(df: pd.DataFrame) -> pd.DataFrame:
    """
    Analyze volatility clustering using funding rate volatility
    """
    try:
        if df.empty:
            logger.warning("Empty DataFrame provided to analyze_volatility_clustering")
            return pd.DataFrame()
            
        results = []
        for symbol in df['symbol'].unique():
            try:
                symbol_data = df[df['symbol'] == symbol].copy()
                if len(symbol_data) < 24:  # Minimum data points needed
                    continue
                
                # Calculate funding rate volatility
                symbol_data['returns'] = symbol_data['funding_rate'].pct_change() * 100
                symbol_data = symbol_data.dropna()
                
                if len(symbol_data) >= 24:
                    # Calculate volatility metrics
                    volatility = symbol_data['returns'].std()
                    vol_trend = (symbol_data['returns'].rolling(window=6).std().iloc[-1] / 
                                symbol_data['returns'].rolling(window=6).std().mean() - 1) * 100
                    
                    # Calculate autocorrelation as a measure of persistence
                    try:
                        acf_values = pd.Series(acf(symbol_data['returns'], nlags=5))
                        vol_persistence = acf_values[1:].mean()  # Average of lags 1-5
                    except Exception as e:
                        logger.warning(f"Error calculating ACF for {symbol}: {e}")
                        vol_persistence = 0.5  # Default value
                    
                    # Calculate clustering score
                    clustering_score = vol_persistence * volatility
                    
                    results.append({
                        'symbol': symbol,
                        'volatility': volatility,
                        'vol_persistence': vol_persistence,
                        'vol_trend': vol_trend,
                        'clustering_score': clustering_score
                    })
            except Exception as e:
                logger.warning(f"Error in volatility analysis for {symbol}: {e}")
                continue
        
        return pd.DataFrame(results)
    
    except Exception as e:
        logger.error(f"Error in analyze_volatility_clustering: {e}")
        return pd.DataFrame()

def analyze_arbitrage_efficiency(df: pd.DataFrame) -> pd.DataFrame:
    """
    Analyze arbitrage efficiency using funding rate convergence
    """
    try:
        if df.empty:
            logger.warning("Empty DataFrame provided to analyze_arbitrage_efficiency")
            return pd.DataFrame()
            
        results = []
        for symbol in df['symbol'].unique():
            try:
                # Get data for this symbol across exchanges
                symbol_data = df[df['symbol'] == symbol].copy()
                
                # Need at least 2 exchanges for arbitrage analysis
                exchanges = symbol_data['exchange'].unique()
                if len(exchanges) < 2 or len(symbol_data) < 10:
                    continue
                
                # Calculate funding rate volatility
                funding_vol = symbol_data['funding_rate'].std()
                
                # Calculate mean absolute deviation from the mean funding rate
                mean_rate = symbol_data.groupby('timestamp')['funding_rate'].mean()
                deviations = symbol_data.groupby(['timestamp', 'exchange'])['funding_rate'].apply(
                    lambda x: abs(x - mean_rate[x.name[0]])
                ).reset_index()
                
                # Calculate convergence speed (inverse of mean deviation)
                mean_deviation = deviations['funding_rate'].mean()
                convergence_speed = 1 / (mean_deviation + 1e-10)  # Avoid division by zero
                
                # Calculate efficiency score
                efficiency_score = convergence_speed / (funding_vol + 1e-10)
                
                results.append({
                    'symbol': symbol,
                    'funding_volatility': funding_vol,
                    'convergence_speed': convergence_speed,
                    'efficiency_score': efficiency_score,
                    'exchange_count': len(exchanges)
                })
                
            except Exception as e:
                logger.warning(f"Error in arbitrage efficiency analysis for {symbol}: {e}")
                continue
        
        return pd.DataFrame(results)
    
    except Exception as e:
        logger.error(f"Error in analyze_arbitrage_efficiency: {e}")
        return pd.DataFrame()

def predict_funding_reversals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Predict funding rate reversals based on trend and momentum
    """
    try:
        if df.empty:
            logger.warning("Empty DataFrame provided to predict_funding_reversals")
            return pd.DataFrame()
            
        results = []
        for symbol in df['symbol'].unique():
            try:
                symbol_data = df[df['symbol'] == symbol].copy()
                if len(symbol_data) < 24:  # Minimum data points needed
                    continue
                
                # Sort by timestamp
                symbol_data = symbol_data.sort_values('timestamp')
                
                # Calculate current rate (average across exchanges)
                current_rates = symbol_data.groupby('exchange')['funding_rate'].last()
                current_rate = current_rates.mean()
                
                # Calculate trend (slope of recent funding rates)
                recent_data = symbol_data.groupby('timestamp')['funding_rate'].mean().tail(12)
                if len(recent_data) < 6:
                    continue
                    
                x = np.arange(len(recent_data))
                y = recent_data.values
                trend = np.polyfit(x, y, 1)[0] * 100  # Scale for readability
                
                # Calculate momentum (rate of change of the trend)
                half_point = len(recent_data) // 2
                if half_point > 0:
                    first_half_trend = np.polyfit(np.arange(half_point), recent_data.values[:half_point], 1)[0]
                    second_half_trend = np.polyfit(np.arange(half_point), recent_data.values[half_point:], 1)[0]
                    momentum = second_half_trend - first_half_trend
                else:
                    momentum = 0
                
                # Calculate reversal probability
                # Higher when trend and momentum have opposite signs
                trend_momentum_opposite = (trend * momentum) < 0
                trend_magnitude = abs(trend)
                momentum_magnitude = abs(momentum)
                
                if trend_momentum_opposite:
                    reversal_probability = min(0.9, (0.5 + 0.2 * trend_magnitude + 0.3 * momentum_magnitude))
                else:
                    reversal_probability = max(0.1, (0.5 - 0.2 * trend_magnitude - 0.3 * momentum_magnitude))
                
                results.append({
                    'symbol': symbol,
                    'current_rate': current_rate,
                    'trend': trend,
                    'momentum': momentum,
                    'reversal_probability': reversal_probability
                })
                
            except Exception as e:
                logger.warning(f"Error in funding reversal prediction for {symbol}: {e}")
                continue
        
        return pd.DataFrame(results)
    
    except Exception as e:
        logger.error(f"Error in predict_funding_reversals: {e}")
        return pd.DataFrame()

def enhance_dashboard():
    """Add enhanced features to the dashboard"""
    try:
        import streamlit as st
        
        # Check if funding data is available
        if 'funding_data' not in st.session_state or st.session_state.funding_data is None or st.session_state.funding_data.empty:
            st.warning("No funding data available. Please load data first.")
            return
        
        # Create a new tab for enhanced features
        st.subheader("Enhanced Analysis")
        
        # Create tabs for different enhanced analyses
        enhanced_tabs = st.tabs([
            "Price-Funding Correlation", 
            "Volatility Analysis", 
            "Arbitrage Efficiency", 
            "Funding Reversals"
        ])
        
        # Tab 1: Price-Funding Correlation
        with enhanced_tabs[0]:
            st.subheader("Price and Funding Rate Correlation")
            
            # Get top symbols by funding rate
            top_symbols = st.session_state.funding_data.groupby('symbol')['funding_rate'].mean().abs().nlargest(10).index.tolist()
            
            # Let user select a symbol
            selected_symbol = st.selectbox(
                "Select Symbol for Analysis",
                top_symbols,
                key="enhanced_symbol_select"
            )
            
            if selected_symbol:
                # Get price history for the selected symbol
                try:
                    price_df = st.session_state.get_enhanced_price_history([selected_symbol], lookback_hours=168)
                    
                    if not price_df.empty:
                        # Create correlation chart
                        st.session_state.create_price_funding_correlation_chart(
                            price_df, 
                            st.session_state.funding_data, 
                            selected_symbol
                        )
                    else:
                        st.warning(f"No price data available for {selected_symbol}")
                except Exception as e:
                    logger.error(f"Error getting price history for {selected_symbol}: {e}")
                    st.error(f"Error retrieving price data: {str(e)}")
        
        # Tab 2: Volatility Analysis
        with enhanced_tabs[1]:
            try:
                # Run volatility clustering analysis
                volatility_df = st.session_state.analyze_volatility_clustering(st.session_state.funding_data)
                
                # Display the results
                st.session_state.display_volatility_clustering_analysis(volatility_df)
            except Exception as e:
                logger.error(f"Error in volatility analysis: {e}")
                st.error(f"Error in volatility analysis: {str(e)}")
        
        # Tab 3: Arbitrage Efficiency
        with enhanced_tabs[2]:
            try:
                # Run arbitrage efficiency analysis
                arbitrage_df = st.session_state.analyze_arbitrage_efficiency(st.session_state.funding_data)
                
                # Display the results
                st.session_state.display_arbitrage_efficiency_analysis(arbitrage_df)
            except Exception as e:
                logger.error(f"Error in arbitrage efficiency analysis: {e}")
                st.error(f"Error in arbitrage efficiency analysis: {str(e)}")
        
        # Tab 4: Funding Reversals
        with enhanced_tabs[3]:
            try:
                # Run funding reversal prediction
                reversal_df = st.session_state.predict_funding_reversals(st.session_state.funding_data)
                
                # Display the results
                st.session_state.display_funding_reversal_analysis(reversal_df)
            except Exception as e:
                logger.error(f"Error in funding reversal analysis: {e}")
                st.error(f"Error in funding reversal analysis: {str(e)}")
        
    except Exception as e:
        logger.error(f"Error enhancing dashboard: {e}")
        st.error(f"Error enhancing dashboard: {str(e)}")

# Main function to initialize the enhancements
def init_enhancements():
    """Initialize dashboard enhancements"""
    try:
        # Initialize Supabase client
        try:
            supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
            supabase_key = os.getenv("NEXT_PUBLIC_SUPABASE_KEY")
            supabase = create_client(supabase_url, supabase_key)
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Supabase client: {e}")
            supabase = None
        
        # Initialize exchange clients
        try:
            binance = ccxt.binance({
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'future',
                    'adjustForTimeDifference': True
                }
            })
            # Note: We're using direct API calls for Hyperliquid instead of ccxt
            logger.info("Exchange clients initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing exchange clients: {e}")
            binance = None
        
        # Add enhanced functions to session state
        if 'st' in globals():
            import streamlit as st
            
            # Data retrieval functions
            st.session_state.get_enhanced_price_history = get_enhanced_price_history
            st.session_state.get_enhanced_funding_data = get_enhanced_funding_data
            
            # Analysis functions
            st.session_state.analyze_volatility_clustering = analyze_volatility_clustering
            st.session_state.analyze_arbitrage_efficiency = analyze_arbitrage_efficiency
            st.session_state.predict_funding_reversals = predict_funding_reversals
            
            # Visualization functions
            st.session_state.create_price_funding_correlation_chart = create_price_funding_correlation_chart
            st.session_state.display_enhanced_market_overview = display_enhanced_market_overview
            st.session_state.display_funding_price_analysis = display_funding_price_analysis
            st.session_state.display_volatility_clustering_analysis = display_volatility_clustering_analysis
            st.session_state.display_arbitrage_efficiency_analysis = display_arbitrage_efficiency_analysis
            st.session_state.display_funding_reversal_analysis = display_funding_reversal_analysis
            
            # Main enhancement function
            st.session_state.enhance_dashboard = enhance_dashboard
            
            # Patch existing functions with enhanced versions
            def patched_get_price_history(symbols, lookback_hours=None):
                """Patched version of get_price_history that uses enhanced version"""
                try:
                    return get_enhanced_price_history(symbols, lookback_hours)
                except Exception as e:
                    logger.error(f"Error in patched_get_price_history: {e}")
                    # Fall back to original function
                    if 'get_price_history' in globals():
                        return globals()['get_price_history'](symbols, lookback_hours)
                    return pd.DataFrame()
            
            st.session_state.patched_get_price_history = patched_get_price_history
            
            # Patch the global namespace in the main module
            try:
                import sys
                main_module = sys.modules['__main__']
                
                # Add our display functions to the main module's global namespace
                if not hasattr(main_module, 'display_volatility_clustering_analysis'):
                    setattr(main_module, 'display_volatility_clustering_analysis', display_volatility_clustering_analysis)
                    logger.info("Patched display_volatility_clustering_analysis in main module")
                
                if not hasattr(main_module, 'display_arbitrage_efficiency_analysis'):
                    setattr(main_module, 'display_arbitrage_efficiency_analysis', display_arbitrage_efficiency_analysis)
                    logger.info("Patched display_arbitrage_efficiency_analysis in main module")
                
                if not hasattr(main_module, 'display_funding_reversal_analysis'):
                    setattr(main_module, 'display_funding_reversal_analysis', display_funding_reversal_analysis)
                    logger.info("Patched display_funding_reversal_analysis in main module")
                
                # Also patch the analysis functions
                if not hasattr(main_module, 'analyze_volatility_clustering'):
                    setattr(main_module, 'analyze_volatility_clustering', analyze_volatility_clustering)
                    logger.info("Patched analyze_volatility_clustering in main module")
                
                if not hasattr(main_module, 'analyze_arbitrage_efficiency'):
                    setattr(main_module, 'analyze_arbitrage_efficiency', analyze_arbitrage_efficiency)
                    logger.info("Patched analyze_arbitrage_efficiency in main module")
                
                if not hasattr(main_module, 'predict_funding_reversals'):
                    setattr(main_module, 'predict_funding_reversals', predict_funding_reversals)
                    logger.info("Patched predict_funding_reversals in main module")
                
            except Exception as e:
                logger.error(f"Error patching global namespace: {e}")
            
        logger.info("Dashboard enhancements initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing dashboard enhancements: {e}")
        return False

if __name__ == "__main__":
    # This will run if the file is executed directly
    st.title("Funding Dashboard Enhancements")
    st.write("This module provides enhanced functions for the funding strategy dashboard.")
    
    # Initialize enhancements
    init_enhancements()
    
    # Show enhanced dashboard features
    enhance_dashboard() 