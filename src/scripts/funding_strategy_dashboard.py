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
from hmmlearn.hmm import GaussianHMM
import sys
from pathlib import Path
from funding_dif import FundingDifferentialAnalyzer
from plotly.subplots import make_subplots
import ccxt
from scipy.signal import savgol_filter
from statsmodels.tsa.regime_switching.markov_regression import MarkovRegression
from statsmodels.tsa.stattools import acf, pacf
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from scipy.stats import norm
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import time
import hashlib
import functools
from concurrent.futures import ThreadPoolExecutor, as_completed
from arch import arch_model
import ruptures as rpt
from itertools import combinations

# Try to import the enhanced functions
try:
    from funding_dashboard_enhancements import (
        display_volatility_clustering_analysis,
        display_arbitrage_efficiency_analysis,
        display_funding_reversal_analysis,
        analyze_volatility_clustering,
        analyze_arbitrage_efficiency,
        predict_funding_reversals
    )
    FUNCTIONS_IMPORTED = True
    logging.info("Successfully imported enhanced functions")
except ImportError:
    FUNCTIONS_IMPORTED = False
    logging.warning("Could not import enhanced functions, will use session state or fallbacks")
    
    # Define fallback functions
    def analyze_volatility_clustering(df: pd.DataFrame) -> pd.DataFrame:
        """
        Fallback implementation of analyze_volatility_clustering
        """
        try:
            if df.empty:
                return pd.DataFrame()
                
            results = []
            for symbol in df['symbol'].unique():
                try:
                    symbol_data = df[df['symbol'] == symbol].copy()
                    if len(symbol_data) < 24:  # Minimum data points needed
                        continue
                    
                    # Calculate simple volatility metrics
                    volatility = symbol_data['funding_rate'].std() * 100
                    vol_trend = 0  # Default value
                    vol_persistence = 0.5  # Default value
                    
                    results.append({
                        'symbol': symbol,
                        'volatility': volatility,
                        'vol_persistence': vol_persistence,
                        'vol_trend': vol_trend,
                        'clustering_score': vol_persistence * volatility
                    })
                except Exception as e:
                    logging.warning(f"Error in volatility analysis for {symbol}: {e}")
                    continue
            
            return pd.DataFrame(results)
        
        except Exception as e:
            logging.error(f"Error in analyze_volatility_clustering: {e}")
            return pd.DataFrame()

    def display_volatility_clustering_analysis(volatility_df: pd.DataFrame):
        """
        Fallback implementation of display_volatility_clustering_analysis
        """
        try:
            if volatility_df.empty:
                st.warning("No data available for volatility clustering analysis")
                return
                
            st.subheader("Volatility Clustering Analysis")
            
            # Display a simple table
            st.write("Volatility Analysis Results:")
            st.dataframe(volatility_df)
            
        except Exception as e:
            logging.error(f"Error in display_volatility_clustering_analysis: {e}")
            st.error("Error displaying volatility clustering analysis")

    def analyze_arbitrage_efficiency(df: pd.DataFrame) -> pd.DataFrame:
        """
        Fallback implementation of analyze_arbitrage_efficiency
        """
        try:
            if df.empty:
                return pd.DataFrame()
                
            results = []
            for symbol in df['symbol'].unique():
                try:
                    # Get data for this symbol across exchanges
                    symbol_data = df[df['symbol'] == symbol].copy()
                    
                    # Need at least 2 exchanges for arbitrage analysis
                    exchanges = symbol_data['exchange'].unique()
                    if len(exchanges) < 2:
                        continue
                    
                    # Calculate simple metrics
                    funding_vol = symbol_data['funding_rate'].std()
                    convergence_speed = 1.0  # Default value
                    efficiency_score = 0.5  # Default value
                    
                    results.append({
                        'symbol': symbol,
                        'funding_volatility': funding_vol,
                        'convergence_speed': convergence_speed,
                        'efficiency_score': efficiency_score,
                        'exchange_count': len(exchanges)
                    })
                    
                except Exception as e:
                    logging.warning(f"Error in arbitrage efficiency analysis for {symbol}: {e}")
                    continue
            
            return pd.DataFrame(results)
        
        except Exception as e:
            logging.error(f"Error in analyze_arbitrage_efficiency: {e}")
            return pd.DataFrame()

    def display_arbitrage_efficiency_analysis(arbitrage_df: pd.DataFrame):
        """
        Fallback implementation of display_arbitrage_efficiency_analysis
        """
        try:
            if arbitrage_df.empty:
                st.warning("No data available for arbitrage efficiency analysis")
                return
                
            st.subheader("Arbitrage Efficiency Analysis")
            
            # Display a simple table
            st.write("Arbitrage Efficiency Results:")
            st.dataframe(arbitrage_df)
            
        except Exception as e:
            logging.error(f"Error in display_arbitrage_efficiency_analysis: {e}")
            st.error("Error displaying arbitrage efficiency analysis")

    def predict_funding_reversals(df: pd.DataFrame) -> pd.DataFrame:
        """
        Fallback implementation of predict_funding_reversals
        """
        try:
            if df.empty:
                return pd.DataFrame()
                
            results = []
            for symbol in df['symbol'].unique():
                try:
                    symbol_data = df[df['symbol'] == symbol].copy()
                    if len(symbol_data) < 24:  # Minimum data points needed
                        continue
                    
                    # Calculate simple metrics
                    current_rate = symbol_data['funding_rate'].mean()
                    trend = 0  # Default value
                    momentum = 0  # Default value
                    reversal_probability = 0.5  # Default value
                    
                    results.append({
                        'symbol': symbol,
                        'current_rate': current_rate,
                        'trend': trend,
                        'momentum': momentum,
                        'reversal_probability': reversal_probability
                    })
                    
                except Exception as e:
                    logging.warning(f"Error in funding reversal prediction for {symbol}: {e}")
                    continue
            
            return pd.DataFrame(results)
        
        except Exception as e:
            logging.error(f"Error in predict_funding_reversals: {e}")
            return pd.DataFrame()

    def display_funding_reversal_analysis(reversal_df: pd.DataFrame):
        """
        Fallback implementation of display_funding_reversal_analysis
        """
        try:
            if reversal_df.empty:
                st.warning("No data available for funding reversal analysis")
                return
                
            st.subheader("Funding Rate Reversal Analysis")
            
            # Display a simple table
            st.write("Funding Reversal Results:")
            st.dataframe(reversal_df)
            
        except Exception as e:
            logging.error(f"Error in display_funding_reversal_analysis: {e}")
            st.error("Error displaying funding reversal analysis")

# Import enhancements if available
try:
    from funding_dashboard_enhancements import (
        init_enhancements,
        enhance_dashboard,
        get_enhanced_price_history,
        get_enhanced_funding_data
    )
    ENHANCEMENTS_AVAILABLE = True
    logging.info("Funding dashboard enhancements loaded successfully")
except ImportError:
    ENHANCEMENTS_AVAILABLE = False
    logging.warning("Funding dashboard enhancements not available")

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase = create_client(
    os.getenv("NEXT_PUBLIC_SUPABASE_URL"),
    os.getenv("NEXT_PUBLIC_SUPABASE_KEY")
)

# Constants
CACHE_TTL = 3600  # 1 hour cache
DEFAULT_LOOKBACK_HOURS = 72  # 3 days default lookback
MIN_DATA_POINTS = 48  # Minimum number of data points for analysis
BATCH_SIZE = 1000  # Batch size for data fetching

def cache_result(ttl=CACHE_TTL):
    """
    Cache decorator with improved error handling and key generation
    """
    def decorator(func):
        cache = {}
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Create a cache key based on function name, args, and kwargs
                key_parts = [func.__name__]
                key_parts.extend([str(arg) for arg in args])
                key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
                cache_key = hashlib.md5("|".join(key_parts).encode()).hexdigest()
                
                # Check if result is in cache and not expired
                if cache_key in cache:
                    result, timestamp = cache[cache_key]
                    if time.time() - timestamp < ttl:
                        return result
                
                # Calculate result and store in cache
                result = func(*args, **kwargs)
                cache[cache_key] = (result, time.time())
                
                # Clean up old cache entries
                current_time = time.time()
                expired_keys = [
                    k for k, (_, t) in cache.items()
                    if current_time - t >= ttl
                ]
                for k in expired_keys:
                    del cache[k]
                
                return result
                
            except Exception as e:
                logger.error(f"Cache error in {func.__name__}: {e}")
                # If cache fails, just execute the function
                return func(*args, **kwargs)
            
        return wrapper
    return decorator

# Add st.cache_data decorator to data loading functions
@st.cache_data(ttl=3600)
def get_funding_data(lookback_hours=None):
    """
    Get funding rate data with optimized batch processing
    """
    try:
        # Set default lookback if not provided
        if lookback_hours is None:
            lookback_hours = 72  # Default to 3 days
        
        # Calculate start date
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(hours=lookback_hours)
        
        # Query in larger chunks with pagination
        BATCH_SIZE = 1000
        all_data = []
        last_id = None
        
        while True:
            query = supabase.table('funding_market_snapshots') \
                .select('*') \
                .gte('created_at', start_date.isoformat()) \
                .lte('created_at', end_date.isoformat()) \
                .order('id', desc=False)
            
            if last_id:
                query = query.gt('id', last_id)
            
            query = query.limit(BATCH_SIZE)
            
            try:
                batch_data = query.execute()
                if not batch_data.data:
                    break
                    
                all_data.extend(batch_data.data)
                last_id = batch_data.data[-1]['id']
                
                if len(batch_data.data) < BATCH_SIZE:
                    break
            except Exception as e:
                logger.error(f"Error fetching funding data batch: {e}")
                if not all_data:  # If we haven't got any data yet, raise the error
                    raise
                break  # Otherwise, use what we have
        
        if not all_data:
            logger.warning("No funding data retrieved")
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(all_data)
        
        # Optimize DataFrame
        df['created_at'] = pd.to_datetime(df['created_at'])
        df['funding_rate'] = pd.to_numeric(df['funding_rate'], errors='coerce')
        df['symbol'] = df['symbol'].astype('category')
        df['exchange'] = df['exchange'].astype('category')
        
        # Remove duplicates and sort
        df = df.drop_duplicates(subset=['symbol', 'exchange', 'created_at'])
        df = df.sort_values(['symbol', 'created_at'])
        
        return df
    
    except Exception as e:
        logger.error(f"Error in get_funding_data: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_price_history(symbols: list, lookback_hours: int = None) -> pd.DataFrame:
    """
    Get price history for multiple symbols in batches
    """
    try:
        if not symbols:
            return pd.DataFrame()

        # Set default lookback if not provided
        if lookback_hours is None:
            lookback_hours = 72

        end_date = datetime.now()
        start_date = end_date - timedelta(hours=lookback_hours)

        # Split symbols into batches of 50
        symbol_batches = [symbols[i:i + 50] for i in range(0, len(symbols), 50)]
        all_price_data = []

        for symbol_batch in symbol_batches:
            try:
                query = supabase.table('crypto_historical.price_history') \
                    .select('*') \
                    .in_('symbol', symbol_batch) \
                    .gte('datetime', start_date.isoformat()) \
                    .lte('datetime', end_date.isoformat())
                
                batch_data = query.execute()
                all_price_data.extend(batch_data.data)
            except Exception as e:
                logger.error(f"Error fetching price data batch for symbols {symbol_batch}: {e}")

        if not all_price_data:
            logger.warning("No price data retrieved")
            return pd.DataFrame()

        # Convert to DataFrame
        df = pd.DataFrame(all_price_data)
        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df.sort_values('datetime')
        
        return df

    except Exception as e:
        logger.error(f"Error in get_price_history: {e}")
        return pd.DataFrame()

def analyze_price_data(price_df: pd.DataFrame) -> pd.DataFrame:
    """
    Analyze price data with robust error handling
    """
    try:
        if price_df.empty:
            return pd.DataFrame()
        
        results = []
        symbols = price_df['symbol'].unique()
        
        for symbol in symbols:
            try:
                symbol_data = price_df[price_df['symbol'] == symbol].copy()
                
                if len(symbol_data) < 2:
                    continue
                
                # Calculate returns and volatility
                symbol_data['returns'] = symbol_data['close'].pct_change()
                
                # Basic metrics
                current_price = symbol_data['close'].iloc[-1]
                price_change = symbol_data['returns'].sum() * 100
                volatility = symbol_data['returns'].std() * np.sqrt(365) * 100
                
                # Calculate moving averages
                for window in [24, 72]:
                    symbol_data[f'ma_{window}h'] = symbol_data['close'].rolling(
                        window=window,
                        min_periods=max(2, window//4)
                    ).mean()
                
                # Trend indicators
                ma_24h = symbol_data['ma_24h'].iloc[-1]
                ma_72h = symbol_data['ma_72h'].iloc[-1]
                trend = 'Bullish' if ma_24h > ma_72h else 'Bearish'
                
                # Momentum and volatility metrics
                momentum = symbol_data['returns'].tail(24).mean() * 100
                vol_trend = symbol_data['returns'].rolling(24).std().diff().iloc[-1]
                vol_regime = 'Increasing' if vol_trend > 0 else 'Decreasing'
                
                results.append({
                    'symbol': symbol,
                    'current_price': current_price,
                    'price_change_pct': price_change,
                    'volatility': volatility,
                    'momentum': momentum,
                    'trend': trend,
                    'volatility_regime': vol_regime,
                    'ma_24h': ma_24h,
                    'ma_72h': ma_72h
                })
            
            except Exception as e:
                logger.error(f"Error analyzing price data for {symbol}: {e}")
                continue
        
        return pd.DataFrame(results) if results else pd.DataFrame()
    
    except Exception as e:
        logger.error(f"Error in analyze_price_data: {e}")
        return pd.DataFrame()

def analyze_sentiment(df):
    sentiment_df = df.groupby('symbol').agg({
        'funding_rate': ['mean', 'std'],
        'opportunity_score': 'mean'
    }).reset_index()
    
    sentiment_df.columns = ['symbol', 'avg_funding', 'funding_std', 'avg_score']
    sentiment_df['sentiment'] = sentiment_df.apply(
        lambda x: 'Bullish' if x['avg_funding'] > x['funding_std'] 
        else 'Bearish' if x['avg_funding'] < -x['funding_std']
        else 'Neutral',
        axis=1
    )
    return sentiment_df

def calculate_performance(df):
    """Calculate historical performance metrics"""
    if df.empty:
        return {"24h": None, "48h": None, "72h": None}
    
    current_price = df['close'].iloc[0]
    metrics = {}
    
    for hours in [24, 48, 72]:
        try:
            past_price = df['close'][df.index <= df.index[0] - timedelta(hours=hours)].iloc[0]
            perf = ((current_price - past_price) / past_price) * 100
            metrics[f"{hours}h"] = round(perf, 2)
        except (IndexError, KeyError):
            metrics[f"{hours}h"] = None
            
    return metrics

def calculate_il(price_change_pct):
    """
    Calculate Impermanent Loss given a price change percentage
    
    Args:
        price_change_pct (float): Price change in percentage
    
    Returns:
        float: Impermanent Loss in percentage
    """
    # Convert percentage to ratio
    price_ratio = 1 + (price_change_pct / 100)
    
    # IL formula: 2 * sqrt(price_ratio) / (1 + price_ratio) - 1
    il = (2 * np.sqrt(price_ratio) / (1 + price_ratio)) - 1
    
    # Convert to percentage and make it negative (as IL is a loss)
    return -il * 100

def analyze_il_risk(price_df, funding_df):
    """
    Analyze Impermanent Loss risk vs Funding Rate returns
    """
    if price_df.empty or funding_df.empty:
        return {}
        
    # Calculate price volatility
    price_volatility = price_df['price_change'].std()
    
    # Calculate potential IL scenarios
    scenarios = {
        'low': calculate_il(price_volatility),
        'medium': calculate_il(price_volatility * 2),
        'high': calculate_il(price_volatility * 3)
    }
    
    # Calculate expected funding returns
    avg_funding_rate = funding_df['funding_rate'].mean() * 100 * 3 * 365  # Annualized
    
    return {
        'il_scenarios': scenarios,
        'expected_funding_apy': avg_funding_rate,
        'breakeven_days': abs(scenarios['medium'] / (avg_funding_rate/365)) if avg_funding_rate != 0 else float('inf'),
        'risk_ratio': abs(avg_funding_rate / scenarios['medium']) if scenarios['medium'] != 0 else float('inf')
    }

def display_il_analysis(symbol, price_df, funding_df):
    """
    Display IL analysis in the dashboard
    """
    st.subheader(f"Impermanent Loss Analysis for {symbol}")
    
    il_analysis = analyze_il_risk(price_df, funding_df)
    
    if not il_analysis:
        st.warning("Insufficient data for IL analysis")
        return
        
    # Create columns for metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Expected Funding APY",
            f"{il_analysis['expected_funding_apy']:.2f}%"
        )
    
    with col2:
        st.metric(
            "Potential IL (Medium)",
            f"{il_analysis['il_scenarios']['medium']:.2f}%"
        )
    
    with col3:
        st.metric(
            "Breakeven Days",
            f"{il_analysis['breakeven_days']:.1f} days"
        )
    
    with col4:
        st.metric(
            "Risk/Reward Ratio",
            f"{il_analysis['risk_ratio']:.2f}x"
        )
    
    # Create IL scenarios chart
    scenarios_df = pd.DataFrame([
        {'Scenario': k, 'IL': v} 
        for k, v in il_analysis['il_scenarios'].items()
    ])
    
    fig = px.bar(
        scenarios_df,
        x='Scenario',
        y='IL',
        title='IL Scenarios vs Expected Funding Returns',
        color='Scenario',
        color_discrete_map={
            'low': 'green',
            'medium': 'yellow',
            'high': 'red'
        }
    )
    
    # Add funding return line
    fig.add_hline(
        y=il_analysis['expected_funding_apy'],
        line_dash="dash",
        line_color="blue",
        annotation_text="Expected Funding Return"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Add risk assessment
    risk_level = (
        'Low' if il_analysis['risk_ratio'] > 3 
        else 'High' if il_analysis['risk_ratio'] < 1 
        else 'Medium'
    )
    
    st.markdown(f"""
    ### Risk Assessment
    
    - **Risk Level**: {risk_level}
    - **Breakeven Analysis**: Need {il_analysis['breakeven_days']:.1f} days of funding to cover medium IL scenario
    - **Volatility Impact**: {price_df['price_change'].std():.2f}% daily price volatility
    
    **Recommendation:**
    {
        'Consider position - funding returns outweigh IL risk significantly' if risk_level == 'Low'
        else 'Careful consideration needed - moderate risk/reward profile' if risk_level == 'Medium'
        else 'High risk - funding returns may not compensate for IL risk'
    }
    """)

def display_symbol_analysis(symbol: str, funding_data: pd.DataFrame, analysis_results: pd.DataFrame):
    """
    Display detailed analysis for a single symbol
    
    Args:
        symbol: Trading symbol to analyze
        funding_data: Raw funding rate data
        analysis_results: Processed analysis results
    """
    st.subheader(f"{symbol} Analysis")
    
    try:
        # Get symbol specific data
        symbol_funding = funding_data[funding_data['symbol'] == symbol].copy()
        symbol_analysis = analysis_results[analysis_results['symbol'] == symbol].copy()
        
        if symbol_funding.empty or symbol_analysis.empty:
            st.warning(f"No data available for {symbol}")
            return
            
        # Create columns for metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            current_rate = symbol_funding['funding_rate'].iloc[-1] * 100
            st.metric(
                "Current Funding Rate",
                f"{current_rate:.4f}%",
                f"Updated {symbol_funding['created_at'].iloc[-1]:%Y-%m-%d %H:%M} UTC"
            )
        
        with col2:
            mean_rate = symbol_analysis['mean_funding_rate'].iloc[-1]
            st.metric(
                "Average Funding Rate",
                f"{mean_rate:.4f}%",
                f"Volatility: {symbol_analysis['funding_volatility'].iloc[-1]:.4f}%"
            )
        
        with col3:
            regime = symbol_analysis['regime'].iloc[-1]
            confidence = symbol_analysis['confidence_score'].iloc[-1]
            st.metric(
                "Market Regime",
                regime.title(),
                f"Confidence: {confidence:.1f}%"
            )
        
        # Create funding rate trend chart
        st.subheader("Funding Rate History")
        fig = go.Figure()
        
        # Add funding rate line
        fig.add_trace(go.Scatter(
            x=symbol_funding['created_at'],
            y=symbol_funding['funding_rate'] * 100,
            name='Funding Rate',
            mode='lines',
            line=dict(color='blue'),
            hovertemplate="<b>%{x}</b><br>" +
                        "Rate: %{y:.4f}%<extra></extra>"
        ))
        
        # Add moving average
        ma_period = 24  # 24 data points moving average
        symbol_funding['MA'] = (
            symbol_funding['funding_rate']
            .rolling(window=ma_period, min_periods=1)
            .mean()
        ) * 100
        
        fig.add_trace(go.Scatter(
            x=symbol_funding['created_at'],
            y=symbol_funding['MA'],
            name=f'{ma_period}-Period MA',
            mode='lines',
            line=dict(color='red', dash='dash'),
            hovertemplate="<b>%{x}</b><br>" +
                        "MA: %{y:.4f}%<extra></extra>"
        ))
        
        fig.update_layout(
            title=f"{symbol} Funding Rate Trend",
            xaxis_title="Time",
            yaxis_title="Funding Rate (%)",
            hovermode='x unified',
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Add volatility analysis
        st.subheader("Volatility Analysis")
        
        # Calculate rolling volatility
        symbol_funding['volatility'] = (
            symbol_funding['funding_rate']
            .rolling(window=24)
            .std()
        ) * 100
        
        fig_vol = go.Figure()
        
        fig_vol.add_trace(go.Scatter(
            x=symbol_funding['created_at'],
            y=symbol_funding['volatility'],
            name='Volatility',
            fill='tozeroy',
            line=dict(color='orange'),
            hovertemplate="<b>%{x}</b><br>" +
                        "Volatility: %{y:.4f}%<extra></extra>"
        ))
        
        fig_vol.update_layout(
            title=f"{symbol} Funding Rate Volatility",
            xaxis_title="Time",
            yaxis_title="Volatility (%)",
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_vol, use_container_width=True)
        
        # Add funding rate distribution
        st.subheader("Funding Rate Distribution")
        
        fig_dist = go.Figure()
        
        fig_dist.add_trace(go.Histogram(
            x=symbol_funding['funding_rate'] * 100,
            nbinsx=50,
            name='Distribution',
            hovertemplate="Rate: %{x:.4f}%<br>" +
                        "Count: %{y}<extra></extra>"
        ))
        
        fig_dist.update_layout(
            title=f"{symbol} Funding Rate Distribution",
            xaxis_title="Funding Rate (%)",
            yaxis_title="Count",
            showlegend=False
        )
        
        st.plotly_chart(fig_dist, use_container_width=True)
        
    except Exception as e:
        logger.error(f"Error analyzing {symbol}: {e}")
        st.error(f"Error analyzing {symbol}. Please try again later.")

def display_price_analysis(funding_data: pd.DataFrame):
    """
    Display price analysis with improved error handling and performance
    """
    try:
        if funding_data.empty:
            st.warning("No funding data available for price analysis")
            return
            
        # Get unique symbols from funding data
        symbols = funding_data['symbol'].unique().tolist()
        
        # Fetch price data for all symbols at once
        with st.spinner('Fetching price data...'):
            price_df = get_price_history(symbols)
            
        if price_df.empty:
            st.warning("No price data available for analysis")
            return
            
        # Analyze price data
        analysis_df = analyze_price_data(price_df)
        
        if analysis_df.empty:
            st.warning("Could not generate price analysis")
            return
            
        # Display summary metrics
        st.subheader("Market Overview")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            bullish_count = (analysis_df['trend'] == 'Bullish').sum()
            st.metric("Bullish Assets", f"{bullish_count}/{len(analysis_df)}")
            
        with col2:
            avg_volatility = analysis_df['volatility'].mean()
            st.metric("Average Volatility", f"{avg_volatility:.2f}%")
            
        with col3:
            high_momentum = (analysis_df['momentum'].abs() > 1).sum()
            st.metric("High Momentum Assets", f"{high_momentum}/{len(analysis_df)}")
        
        # Create interactive price charts
        st.subheader("Price Analysis by Asset")
        
        # Add filters
        col1, col2 = st.columns(2)
        with col1:
            selected_trend = st.selectbox(
                "Filter by Trend",
                ['All', 'Bullish', 'Bearish']
            )
        with col2:
            sort_by = st.selectbox(
                "Sort by",
                ['Price Change', 'Volatility', 'Momentum']
            )
            
        # Filter and sort data
        filtered_df = analysis_df.copy()
        if selected_trend != 'All':
            filtered_df = filtered_df[filtered_df['trend'] == selected_trend]
            
        sort_map = {
            'Price Change': 'price_change_pct',
            'Volatility': 'volatility',
            'Momentum': 'momentum'
        }
        filtered_df = filtered_df.sort_values(sort_map[sort_by], ascending=False)
        
        # Display interactive table
        st.dataframe(
            filtered_df.style.format({
                'current_price': '${:,.2f}',
                'price_change_pct': '{:,.2f}%',
                'volatility': '{:,.2f}%',
                'momentum': '{:,.2f}%',
                'ma_24h': '${:,.2f}',
                'ma_72h': '${:,.2f}'
            }).background_gradient(
                subset=['price_change_pct', 'volatility', 'momentum'],
                cmap='RdYlGn'
            ),
            use_container_width=True
        )
        
        # Display charts for top/bottom performers
        st.subheader("Top and Bottom Performers")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("Top 5 Performers")
            top_5 = filtered_df.head(5)
            fig = create_performance_chart(price_df, top_5['symbol'].tolist(), "Top 5 Price Performance")
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            st.write("Bottom 5 Performers")
            bottom_5 = filtered_df.tail(5)
            fig = create_performance_chart(price_df, bottom_5['symbol'].tolist(), "Bottom 5 Price Performance")
            st.plotly_chart(fig, use_container_width=True)
            
    except Exception as e:
        logger.error(f"Error in display_price_analysis: {e}")
        st.error("An error occurred while displaying price analysis")

def create_performance_chart(price_df: pd.DataFrame, symbols: list, title: str) -> go.Figure:
    """
    Create a performance comparison chart
    """
    try:
        fig = go.Figure()
        
        for symbol in symbols:
            symbol_data = price_df[price_df['symbol'] == symbol].copy()
            if len(symbol_data) < 2:
                continue
                
            # Calculate percentage change from first price
            symbol_data['pct_change'] = (
                symbol_data['close'] / symbol_data['close'].iloc[0] - 1
            ) * 100
            
            fig.add_trace(
                go.Scatter(
                    x=symbol_data['datetime'],
                    y=symbol_data['pct_change'],
                    name=symbol,
                    mode='lines'
                )
            )
            
        fig.update_layout(
            title=title,
            xaxis_title="Time",
            yaxis_title="Price Change (%)",
            hovermode='x unified',
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            )
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"Error creating performance chart: {e}")
        return go.Figure()

def display_arbitrage_opportunities(df_analysis, min_spread):
    """Arbitrage Opportunities Tab"""
    st.subheader("Funding Rate Arbitrage Opportunities")
    
    opportunities = calculate_arbitrage_opportunities(df_analysis, min_spread)
    
    if not opportunities.empty:
        st.dataframe(
            opportunities.style.format({
                'rate_diff': '{:.4f}%',
                'estimated_apy': '{:.2f}%',
                'confidence_score': '{:.2f}'
            }).background_gradient(subset=['estimated_apy'], cmap='RdYlGn')
        )
    else:
        st.info("No arbitrage opportunities found meeting the minimum spread criteria")

def display_strategy_signals(df_analysis):
    """Strategy Signals Tab"""
    st.subheader("Trading Strategy Signals")
    
    # Filter for high confidence signals
    high_conf_signals = df_analysis[
        (df_analysis['confidence_score'] > 70) &
        (df_analysis['period'] == '24h')
    ].copy()
    
    if not high_conf_signals.empty:
        # Display signals
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Bullish Signals")
            bullish = high_conf_signals[high_conf_signals['sentiment'] == 'bullish']
            if not bullish.empty:
                st.dataframe(bullish[['symbol', 'mean_funding_rate', 'confidence_score']])
            else:
                st.info("No high-confidence bullish signals")
        
        with col2:
            st.markdown("### Bearish Signals")
            bearish = high_conf_signals[high_conf_signals['sentiment'] == 'bearish']
            if not bearish.empty:
                st.dataframe(bearish[['symbol', 'mean_funding_rate', 'confidence_score']])
            else:
                st.info("No high-confidence bearish signals")
    else:
        st.info("No high-confidence signals found")

def analyze_funding_trends(df: pd.DataFrame) -> pd.DataFrame:
    """
    Analyze funding rate trends with improved error handling
    """
    try:
        if df.empty:
            logger.warning("Empty DataFrame provided for analysis")
            return pd.DataFrame()
            
        analysis_results = []
        lookback_periods = [24, 72, 168]  # 1 day, 3 days, 1 week
        
        current_time = pd.Timestamp.now(tz='UTC')
        
        for symbol in df['symbol'].unique():
            symbol_data = df[df['symbol'] == symbol].copy()
            
            # Calculate metrics for different periods
            for hours in lookback_periods:
                period_start = current_time - pd.Timedelta(hours=hours)
                period_data = symbol_data[
                    symbol_data['created_at'] >= period_start
                ].copy()
                
                if len(period_data) >= 3:  # Minimum data points for analysis
                    try:
                        # Calculate funding rate metrics
                        mean_rate = period_data['funding_rate'].mean()
                        rate_std = period_data['funding_rate'].std()
                        
                        if pd.isna(mean_rate) or pd.isna(rate_std):
                            logger.warning(f"Invalid metrics for {symbol} in {hours}h period")
                            continue
                        
                        # Calculate trend
                        rates = period_data['funding_rate'].values
                        trend = 'up' if rates[-1] > rates[0] else 'down' if rates[-1] < rates[0] else 'sideways'
                        
                        # Calculate volatility regime
                        vol_percentiles = np.percentile(
                            period_data['funding_rate'].abs(), 
                            [20, 40, 60, 80]
                        )
                        regime = (
                            'very_low' if abs(mean_rate) <= vol_percentiles[0]
                            else 'low' if abs(mean_rate) <= vol_percentiles[1]
                            else 'medium' if abs(mean_rate) <= vol_percentiles[2]
                            else 'high' if abs(mean_rate) <= vol_percentiles[3]
                            else 'very_high'
                        )
                        
                        # Calculate sentiment
                        sentiment = (
                            'bullish' if mean_rate > rate_std
                            else 'bearish' if mean_rate < -rate_std
                            else 'neutral'
                        )
                        
                        # Calculate confidence score
                        confidence_score = calculate_confidence_score(mean_rate, rate_std, len(period_data))
                        
                        analysis_results.append({
                            'symbol': symbol,
                            'period': f'{hours}h',
                            'mean_funding_rate': mean_rate,
                            'funding_volatility': rate_std,
                            'trend': trend,
                            'regime': regime,
                            'sentiment': sentiment,
                            'confidence_score': confidence_score,
                            'sample_size': len(period_data)
                        })
                        
                    except Exception as e:
                        logger.warning(f"Error analyzing {symbol} for {hours}h period: {e}")
                        continue
        
        if not analysis_results:
            logger.warning("No analysis results generated")
            return pd.DataFrame()
            
        result_df = pd.DataFrame(analysis_results)
        
        # Sort by absolute mean funding rate
        result_df = result_df.sort_values(
            by='mean_funding_rate',
            key=abs,
            ascending=False
        )
        
        logger.info(f"Analysis completed for {len(result_df)} records")
        return result_df
        
    except Exception as e:
        logger.error(f"Error in analyze_funding_trends: {e}")
        return pd.DataFrame()

def analyze_top_opportunities(df_analysis: pd.DataFrame, n_top: int = 10) -> pd.DataFrame:
    """
    Analyze and identify top funding rate opportunities
    
    Args:
        df_analysis: DataFrame with analysis results
        n_top: Number of top opportunities to return (default: 10)
    
    Returns:
        DataFrame with top opportunities
    """
    try:
        if df_analysis.empty:
            return pd.DataFrame()
        
        # Check if 'period' column exists
        if 'period' in df_analysis.columns:
            # Get latest period data
            latest_data = df_analysis[df_analysis['period'] == '24h'].copy()
            
            # If no 24h period data, use all data
            if latest_data.empty:
                latest_data = df_analysis.copy()
                logger.warning("No 24h period data found, using all available data")
        else:
            # If no period column, use all data
            latest_data = df_analysis.copy()
            logger.warning("No period column found in analysis data, using all available data")
        
        # Check if 'mean_funding_rate' column exists
        if 'mean_funding_rate' not in latest_data.columns:
            # Try to calculate it from funding_rate if available
            if 'funding_rate' in latest_data.columns:
                latest_data['mean_funding_rate'] = latest_data.groupby('symbol')['funding_rate'].transform('mean')
                logger.info("Calculated mean_funding_rate from funding_rate column")
            elif 'avg_funding_rate' in latest_data.columns:
                latest_data['mean_funding_rate'] = latest_data['avg_funding_rate']
                logger.info("Using avg_funding_rate as mean_funding_rate")
            else:
                logger.error("Cannot calculate mean_funding_rate, no suitable columns found")
                return pd.DataFrame()
        
        # Check if 'confidence_score' column exists
        if 'confidence_score' not in latest_data.columns:
            latest_data['confidence_score'] = 50  # Default value
            logger.warning("No confidence_score column found, using default value")
        
        # Check if 'funding_volatility' column exists
        if 'funding_volatility' not in latest_data.columns:
            if 'funding_rate' in latest_data.columns:
                latest_data['funding_volatility'] = latest_data.groupby('symbol')['funding_rate'].transform('std') * 100
                logger.info("Calculated funding_volatility from funding_rate column")
            else:
                latest_data['funding_volatility'] = 0  # Default value
                logger.warning("No funding_volatility column found and cannot calculate, using default value")
        
        # Calculate opportunity score
        latest_data['opportunity_score'] = (
            abs(latest_data['mean_funding_rate']) * 
            (latest_data['confidence_score'] / 100) * 
            (1 + latest_data['funding_volatility'] / 100)
        )
        
        # Get top opportunities
        top_opps = latest_data.nlargest(n_top, 'opportunity_score')
        
        # Add opportunity type
        top_opps['opportunity_type'] = np.where(
            top_opps['mean_funding_rate'] > 0,
            'Short',
            'Long'
        )
        
        # Calculate expected APR
        top_opps['expected_apr'] = abs(top_opps['mean_funding_rate'] * 365)
        
        return top_opps
        
    except Exception as e:
        logger.error(f"Error analyzing top opportunities: {e}")
        return pd.DataFrame()

def calculate_annualized_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate annualized metrics for funding rates
    """
    df = df.copy()
    
    # Convert funding rates to annualized percentages (8h funding periods)
    df['annualized_funding'] = df['funding_rate'] * 100 * 3 * 365  # Convert to annual percentage
    df['annualized_volatility'] = df['funding_volatility'] * np.sqrt(365 * 3)  # Annualize volatility
    
    return df

def get_current_price(symbol: str = 'BTC') -> float:
    """Get real-time price from CCXT"""
    try:
        # Initialize Binance client
        binance = ccxt.binance()
        
        # Clean symbol and add USDT suffix if needed
        clean_symbol = symbol.upper().replace('PERP', '').strip()
        if not clean_symbol.endswith('USDT'):
            clean_symbol += 'USDT'
            
        # Fetch current ticker
        ticker = binance.fetch_ticker(clean_symbol)
        return ticker['last']
        
    except Exception as e:
        logger.error(f"Error fetching current price for {symbol}: {e}")
        return None

def create_price_funding_chart(price_df: pd.DataFrame, funding_data: pd.DataFrame, symbol: str):
    """Create price chart with complete funding rate history overlay"""
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Add price line
    fig.add_trace(
        go.Scatter(
            x=price_df['datetime'],
            y=price_df['close'],
            name='Price',
            line=dict(color='#1f77b4', width=2)
        ),
        secondary_y=False
    )
    
    # Add moving averages
    for ma, color in [('24h_ma', '#ff7f0e'), ('72h_ma', '#2ca02c')]:
        fig.add_trace(
            go.Scatter(
                x=price_df['datetime'],
                y=price_df[ma],
                name=f"{ma.upper()}",
                line=dict(color=color, dash='dash'),
                opacity=0.7
            ),
            secondary_y=False
        )
    
    # Add funding rates for each exchange with proper timezone handling
    for exchange, color in [('binance', '#f0b90b'), ('hyperliquid', '#3498db')]:
        exchange_data = funding_data[funding_data['exchange'] == exchange].copy()
        if not exchange_data.empty:
            # Handle timezone conversion properly
            if exchange_data['created_at'].dt.tz is None:
                exchange_data['created_at'] = pd.to_datetime(exchange_data['created_at']).dt.tz_localize('UTC')
            else:
                exchange_data['created_at'] = pd.to_datetime(exchange_data['created_at']).dt.tz_convert('UTC')
            
            # Calculate annualized funding rate
            exchange_data['annualized_rate'] = exchange_data['funding_rate'] * 100 * 3 * 365
            
            # Add funding rate line
            fig.add_trace(
                go.Scatter(
                    x=exchange_data['created_at'],
                    y=exchange_data['annualized_rate'],
                    name=f"{exchange.title()} Funding",
                    line=dict(color=color, width=1.5),
                    hovertemplate=(
                        "<b>%{x}</b><br>" +
                        "Rate: %{y:.2f}%/year<br>" +
                        "<extra></extra>"
                    )
                ),
                secondary_y=True
            )
    
    # Update layout with proper date range handling
    try:
        min_date = min(
            price_df['datetime'].min() if not price_df.empty else pd.Timestamp.max,
            funding_data['created_at'].min() if not funding_data.empty else pd.Timestamp.max
        )
        max_date = max(
            price_df['datetime'].max() if not price_df.empty else pd.Timestamp.min,
            funding_data['created_at'].max() if not funding_data.empty else pd.Timestamp.min
        )
        
        # Ensure dates are timezone-aware
        if min_date.tz is None:
            min_date = min_date.tz_localize('UTC')
        if max_date.tz is None:
            max_date = max_date.tz_localize('UTC')
            
        fig.update_layout(
            title=f"{symbol} Price and Historical Funding Rates",
            xaxis_title="Date",
            xaxis=dict(
                range=[min_date, max_date],
                type='date'
            ),
            hovermode='x unified',
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            ),
            height=500
        )
    except Exception as e:
        logger.error(f"Error setting date range for {symbol}: {e}")
        # Use default layout if date range setting fails
        fig.update_layout(
            title=f"{symbol} Price and Historical Funding Rates",
            xaxis_title="Date",
            hovermode='x unified',
            showlegend=True,
            height=500
        )
    
    # Update y-axes labels
    fig.update_yaxes(title_text="Price (USD)", secondary_y=False)
    fig.update_yaxes(title_text="Annualized Funding Rate (%)", secondary_y=True)
    
    return fig

def calculate_confidence_score(mean_rate: float, rate_std: float, sample_size: int) -> float:
    """
    Calculate confidence score with proper error handling
    """
    try:
        base_score = 50  # Base confidence score
        
        # Handle rate significance
        if rate_std > 0:
            rate_score = min(25, abs(mean_rate) / rate_std * 25)
        else:
            rate_score = 0 if mean_rate == 0 else 25
            
        # Handle data coverage
        coverage_score = min(25, sample_size / 24 * 25)  # Normalize by 24 data points
        
        return min(100, max(0, base_score + rate_score + coverage_score))
        
    except Exception as e:
        logger.warning(f"Error calculating confidence score: {e}")
        return 50.0  # Return neutral score on error

def display_funding_analysis(df_analysis):
    """Display funding analysis with combined price analysis"""
    st.subheader("Market Analysis")
    
    # Get unique symbols from funding data
    symbols = df_analysis['symbol'].unique()
    
    # Add symbol selector
    selected_symbol = st.selectbox(
        "Select Asset for Analysis",
        symbols,
        index=0 if len(symbols) > 0 else None
    )
    
    if selected_symbol:
        create_combined_analysis(selected_symbol)

def create_exchange_funding_chart(funding_data: pd.DataFrame, symbol: str):
    """Create chart comparing funding rates across exchanges"""
    fig = go.Figure()
    
    colors = {
        'binance': 'rgb(240, 185, 11)',  # Binance yellow
        'hyperliquid': 'rgb(52, 152, 219)'  # Hyperliquid blue
    }
    
    for exchange in ['binance', 'hyperliquid']:
        exchange_data = funding_data[
            (funding_data['symbol'] == symbol) & 
            (funding_data['exchange'].str.lower() == exchange)
        ].copy()
        
        if not exchange_data.empty:
            # Calculate annualized funding rate
            exchange_data['annualized_rate'] = exchange_data['funding_rate'] * 100 * 3 * 365
            
            fig.add_trace(go.Scatter(
                x=exchange_data['created_at'],
                y=exchange_data['annualized_rate'],
                name=f"{exchange.title()}",
                line=dict(color=colors[exchange]),
                hovertemplate=(
                    "<b>%{x}</b><br>" +
                    "Rate: %{y:.2f}%/year<br>" +
                    "<extra></extra>"
                )
            ))
    
    fig.update_layout(
        title=f"{symbol} Exchange Funding Rate Comparison",
        xaxis_title="Time",
        yaxis_title="Annualized Funding Rate (%)",
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        )
    )
    
    return fig

def create_price_analysis(symbol: str):
    """Create comprehensive price analysis section"""
    with st.expander(f"📈 {symbol} Price Analysis", expanded=True):
        col1, col2 = st.columns([1, 3])
        
        # Get price data
        price_df = get_price_history(symbol, datetime.now() - timedelta(days=30))
        
        if not price_df.empty:
            with col1:
                st.metric("Current Price", f"${price_df['close'].iloc[-1]:,.2f}")
                st.metric("24h Volume", f"${price_df['volume'].iloc[-1]:,.0f}")
                st.metric("30d High", f"${price_df['close'].max():,.2f}")
                st.metric("30d Low", f"${price_df['close'].min():,.2f}")
            
            with col2:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=price_df['datetime'],
                    y=price_df['close'],
                    name='Price',
                    line=dict(color='#636EFA')
                ))
                fig.add_trace(go.Scatter(
                    x=price_df['datetime'],
                    y=price_df['24h_ma'],
                    name='24h MA',
                    line=dict(color='#FFA15A', dash='dot')
                ))
                fig.add_trace(go.Scatter(
                    x=price_df['datetime'],
                    y=price_df['72h_ma'],
                    name='72h MA',
                    line=dict(color='#00CC96', dash='dash')
                ))
                fig.update_layout(
                    title=f"{symbol} Price Trend",
                    xaxis_title="Date",
                    yaxis_title="Price (USD)",
                    hovermode="x unified",
                    showlegend=True,
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning(f"No price data available for {symbol}")

def create_funding_analysis(symbol: str, funding_data: pd.DataFrame):
    """Create funding rate analysis section"""
    with st.expander(f"📊 {symbol} Funding Analysis"):
        col1, col2 = st.columns([1, 3])
        
        # Filter funding data
        symbol_funding = funding_data[funding_data['symbol'] == symbol]
        
        if not symbol_funding.empty:
            with col1:
                binance_rate = symbol_funding[
                    symbol_funding['exchange'] == 'binance'
                ]['funding_rate'].iloc[-1] * 100 * 3 * 365
                
                hl_rate = symbol_funding[
                    symbol_funding['exchange'] == 'hyperliquid'
                ]['funding_rate'].iloc[-1] * 100 * 3 * 365
                
                st.metric("Binance Annualized", f"{binance_rate:.2f}%")
                st.metric("Hyperliquid Annualized", f"{hl_rate:.2f}%")
                st.metric("Rate Difference", f"{abs(binance_rate - hl_rate):.2f}%")
            
            with col2:
                fig = go.Figure()
                
                for exchange in ['binance', 'hyperliquid']:
                    exchange_data = symbol_funding[symbol_funding['exchange'] == exchange]
                    if not exchange_data.empty:
                        fig.add_trace(go.Scatter(
                            x=exchange_data['created_at'],
                            y=exchange_data['funding_rate'] * 100 * 3 * 365,
                            name=exchange.capitalize(),
                            mode='lines+markers',
                            line=dict(width=2)
                        ))
                
                fig.update_layout(
                    title="Funding Rate Comparison",
                    yaxis_title="Annualized Rate (%)",
                    xaxis_title="Date",
                    hovermode="x unified",
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning(f"No funding data available for {symbol}")

def display_asset_analysis(top_opps: pd.DataFrame, funding_data: pd.DataFrame):
    """Display combined price and funding analysis"""
    st.subheader("Asset-Specific Analysis")
    
    # Check if top_opps is empty
    if top_opps.empty:
        st.warning("No top opportunities found to display. Try adjusting the lookback period or refresh the data.")
        return
    
    # Check if 'symbol' column exists
    if 'symbol' not in top_opps.columns:
        st.error("Symbol information is missing from the analysis data.")
        logger.error("Symbol column missing from top opportunities data")
        return
    
    # Get unique symbols
    unique_symbols = top_opps['symbol'].unique()
    
    # Check if there are any symbols
    if len(unique_symbols) == 0:
        st.warning("No symbols found in the top opportunities data.")
        return
    
    # Create tabs for each asset
    tabs = st.tabs([f" {symbol} " for symbol in unique_symbols])
    
    for idx, symbol in enumerate(unique_symbols):
        with tabs[idx]:
            # Price Analysis Section
            create_price_analysis(symbol)
            
            # Funding Analysis Section
            create_funding_analysis(symbol, funding_data)
            
            # Add spacing between sections
            st.markdown("---")

def create_combined_analysis(symbol: str, lookback_days: int = None):
    """Create comprehensive price and funding analysis for a symbol"""
    try:
        # Create tabs for different analysis views
        overview_tab, price_tab, funding_tab = st.tabs(["Overview", "Price Analysis", "Funding Analysis"])
        
        # Fetch all historical data
        start_date = datetime(2024, 2, 1, tzinfo=timezone.utc)
        price_df = get_price_history(symbol, start_date)
        
        # Get all funding data and filter for the symbol
        all_funding_data = get_funding_data()
        symbol_funding = all_funding_data[all_funding_data['symbol'] == symbol].copy()
        
        # Sort funding data by timestamp
        symbol_funding = symbol_funding.sort_values('created_at')
        
        with overview_tab:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if not price_df.empty:
                    current_price = price_df['close'].iloc[-1]
                    price_change = None
                    if len(price_df) >= 24:
                        price_24h_ago = price_df['close'].iloc[-24]
                        price_change = ((current_price - price_24h_ago) / price_24h_ago * 100)
                    
                    st.metric(
                        "Current Price",
                        f"${current_price:,.2f}",
                        f"{price_change:.2f}%" if price_change is not None else None
                    )
                    if not price_df.empty:
                        st.metric("24h Volume", f"${price_df['volume'].iloc[-1]:,.0f}")
                
            with col2:
                if not symbol_funding.empty:
                    latest_binance = symbol_funding[
                        symbol_funding['exchange'] == 'binance'
                    ].sort_values('created_at').iloc[-1:]
                    
                    if not latest_binance.empty:
                        binance_rate = latest_binance['funding_rate'].iloc[0] * 100 * 3 * 365
                        st.metric("Binance Funding (Ann.)", f"{binance_rate:.2f}%")
                
            with col3:
                if not symbol_funding.empty:
                    latest_hl = symbol_funding[
                        symbol_funding['exchange'] == 'hyperliquid'
                    ].sort_values('created_at').iloc[-1:]
                    
                    if not latest_hl.empty:
                        hl_rate = latest_hl['funding_rate'].iloc[0] * 100 * 3 * 365
                        st.metric("Hyperliquid Funding (Ann.)", f"{hl_rate:.2f}%")
                        
                        if 'binance_rate' in locals():
                            rate_diff = abs(binance_rate - hl_rate)
                            st.metric("Funding Differential", f"{rate_diff:.2f}%")

        with price_tab:
            if not price_df.empty:
                # Create combined price and funding chart with all historical data
                fig = create_price_funding_chart(price_df, symbol_funding, symbol)
                st.plotly_chart(fig, use_container_width=True)
                
                # Add funding rate statistics
                st.subheader("Funding Rate Statistics")
                col1, col2, col3 = st.columns(3)
                
                for exchange, col in [('binance', col1), ('hyperliquid', col2)]:
                    with col:
                        exchange_data = symbol_funding[symbol_funding['exchange'] == exchange]
                        if not exchange_data.empty:
                            rates = exchange_data['funding_rate'] * 100 * 3 * 365  # Annualized
                            st.metric(f"{exchange.title()} Avg Rate", f"{rates.mean():.2f}%/year")
                            st.metric(f"{exchange.title()} Max Rate", f"{rates.max():.2f}%/year")
                            st.metric(f"{exchange.title()} Min Rate", f"{rates.min():.2f}%/year")
                
                with col3:
                    if len(symbol_funding['created_at'].unique()) > 0:
                        days_of_data = (symbol_funding['created_at'].max() - 
                                      symbol_funding['created_at'].min()).days
                        st.metric("Historical Data", f"{days_of_data} days")
                        st.metric("Data Points", len(symbol_funding))
            else:
                st.warning("No price data available")

        with funding_tab:
            if not symbol_funding.empty:
                # Funding rate comparison chart
                fig = go.Figure()
                
                for exchange, color in [('binance', '#f0b90b'), ('hyperliquid', '#3498db')]:
                    exchange_data = symbol_funding[symbol_funding['exchange'] == exchange]
                    if not exchange_data.empty:
                        fig.add_trace(go.Scatter(
                            x=exchange_data['created_at'],
                            y=exchange_data['funding_rate'] * 100 * 3 * 365,
                            name=exchange.capitalize(),
                            line=dict(color=color, width=2),
                            mode='lines+markers'
                        ))
                
                fig.update_layout(
                    title="Funding Rate Comparison",
                    xaxis_title="Date",
                    yaxis_title="Annualized Rate (%)",
                    hovermode='x unified',
                    height=500
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Funding statistics
                col1, col2 = st.columns(2)
                
                for exchange, col in [('binance', col1), ('hyperliquid', col2)]:
                    with col:
                        exchange_data = symbol_funding[symbol_funding['exchange'] == exchange]
                        if not exchange_data.empty:
                            rates = exchange_data['funding_rate'] * 100 * 3 * 365
                            st.metric(f"{exchange.capitalize()} Avg Rate", f"{rates.mean():.2f}%")
                            st.metric(f"{exchange.capitalize()} Max Rate", f"{rates.max():.2f}%")
                            st.metric(f"{exchange.capitalize()} Min Rate", f"{rates.min():.2f}%")
                            st.metric(f"{exchange.capitalize()} Volatility", f"{rates.std():.2f}%")
                
    except Exception as e:
        logger.error(f"Error in combined analysis for {symbol}: {e}")
        st.error(f"Error analyzing {symbol}")

@st.cache_data(ttl=3600)
def analyze_term_structure(funding_data: pd.DataFrame) -> pd.DataFrame:
    """
    Analyze funding rate term structure with improved error handling
    """
    try:
        if funding_data.empty:
            logger.warning("Empty funding data provided for term structure analysis")
            return pd.DataFrame()
            
        results = []
        symbols = funding_data['symbol'].unique()
        
        for symbol in symbols:
            try:
                # Get data for this symbol
                symbol_data = funding_data[funding_data['symbol'] == symbol].copy()
                
                # Forward fill missing values
                symbol_data['funding_rate'] = symbol_data['funding_rate'].ffill()
                
                if len(symbol_data) < MIN_DATA_POINTS:
                    continue
                    
                # Calculate term structure metrics
                current_rate = symbol_data['funding_rate'].iloc[-1]
                mean_rate = symbol_data['funding_rate'].mean()
                std_rate = symbol_data['funding_rate'].std()
                
                # Calculate percentiles
                percentiles = symbol_data['funding_rate'].quantile([0.25, 0.5, 0.75])
                q1, median, q3 = percentiles.values
                
                # Calculate term structure shape
                if current_rate > q3:
                    curve_shape = 'Steep Contango'
                elif current_rate > median:
                    curve_shape = 'Mild Contango'
                elif current_rate < q1:
                    curve_shape = 'Steep Backwardation'
                elif current_rate < median:
                    curve_shape = 'Mild Backwardation'
                else:
                    curve_shape = 'Neutral'
                    
                # Calculate confidence score
                sample_size = len(symbol_data)
                confidence = calculate_confidence_score(mean_rate, std_rate, sample_size)
                
                # Calculate trend metrics
                rates_series = symbol_data['funding_rate']
                trend = np.polyfit(range(len(rates_series)), rates_series, 1)[0]
                trend_strength = abs(trend) / std_rate if std_rate > 0 else 0
                
                # Detect regime changes
                try:
                    # Smooth the rates to reduce noise
                    window = min(24, len(rates_series) // 4)
                    smoothed_rates = rates_series.rolling(window=window, min_periods=1).mean()
                    
                    algo = rpt.Pelt(model="rbf").fit(smoothed_rates.values)
                    change_points = algo.predict(pen=10)
                    regime_changes = len(change_points)
                except Exception as e:
                    logger.warning(f"Change point detection failed for {symbol}: {e}")
                    regime_changes = 0
                
                results.append({
                    'symbol': symbol,
                    'current_rate': current_rate,
                    'mean_rate': mean_rate,
                    'std_rate': std_rate,
                    'q1_rate': q1,
                    'median_rate': median,
                    'q3_rate': q3,
                    'curve_shape': curve_shape,
                    'confidence_score': confidence,
                    'trend': trend,
                    'trend_strength': trend_strength,
                    'regime_changes': regime_changes,
                    'sample_size': sample_size
                })
                
            except Exception as e:
                logger.error(f"Error analyzing term structure for {symbol}: {e}")
                continue
                
        if not results:
            return pd.DataFrame()
            
        # Create DataFrame and sort by confidence score
        df_results = pd.DataFrame(results)
        df_results = df_results.sort_values('confidence_score', ascending=False)
        
        return df_results
        
    except Exception as e:
        logger.error(f"Error in analyze_term_structure: {e}")
        return pd.DataFrame()

def display_term_structure_analysis(term_structure_df: pd.DataFrame):
    """
    Display term structure analysis with improved visualization
    """
    try:
        if term_structure_df.empty:
            st.warning("No data available for term structure analysis")
            return
            
        st.subheader("Term Structure Analysis")
        
        # Summary metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            contango_count = term_structure_df['curve_shape'].str.contains('Contango').sum()
            st.metric(
                "Contango Markets",
                f"{contango_count}/{len(term_structure_df)}",
                help="Markets in contango (funding rates above historical levels)"
            )
            
        with col2:
            avg_confidence = term_structure_df['confidence_score'].mean()
            st.metric(
                "Average Confidence",
                f"{avg_confidence:.2f}",
                help="Mean confidence score across all markets"
            )
            
        with col3:
            high_trend = (term_structure_df['trend_strength'] > 0.5).sum()
            st.metric(
                "Strong Trends",
                f"{high_trend}/{len(term_structure_df)}",
                help="Markets with strong directional trends"
            )
            
        # Interactive filters
        col1, col2 = st.columns(2)
        with col1:
            sort_by = st.selectbox(
                "Sort by",
                ['Confidence Score', 'Current Rate', 'Trend Strength']
            )
        with col2:
            curve_shape = st.selectbox(
                "Filter by Curve Shape",
                ['All'] + list(term_structure_df['curve_shape'].unique())
            )
            
        # Filter and sort data
        filtered_df = term_structure_df.copy()
        if curve_shape != 'All':
            filtered_df = filtered_df[filtered_df['curve_shape'] == curve_shape]
            
        sort_map = {
            'Confidence Score': 'confidence_score',
            'Current Rate': 'current_rate',
            'Trend Strength': 'trend_strength'
        }
        filtered_df = filtered_df.sort_values(sort_map[sort_by], ascending=False)
        
        # Display results table
        st.dataframe(
            filtered_df.style.format({
                'current_rate': '{:.2%}',
                'mean_rate': '{:.2%}',
                'std_rate': '{:.2%}',
                'q1_rate': '{:.2%}',
                'median_rate': '{:.2%}',
                'q3_rate': '{:.2%}',
                'confidence_score': '{:.2f}',
                'trend': '{:.2e}',
                'trend_strength': '{:.2f}',
                'regime_changes': '{:.0f}',
                'sample_size': '{:,.0f}'
            }).background_gradient(
                subset=['confidence_score', 'trend_strength'],
                cmap='RdYlGn'
            ),
            use_container_width=True
        )
        
        # Visualization
        st.subheader("Term Structure Patterns")
        
        # Create scatter plot
        fig = go.Figure()
        
        # Add scatter plot for current rate vs mean rate
        fig.add_trace(
            go.Scatter(
                x=filtered_df['mean_rate'] * 100,  # Convert to percentage
                y=filtered_df['current_rate'] * 100,  # Convert to percentage
                mode='markers+text',
                text=filtered_df['symbol'],
                textposition='top center',
                name='Markets',
                marker=dict(
                    size=10,
                    color=filtered_df['confidence_score'],
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(title='Confidence Score')
                )
            )
        )
        
        # Add diagonal line for reference
        max_rate = max(filtered_df['mean_rate'].max(), filtered_df['current_rate'].max())
        min_rate = min(filtered_df['mean_rate'].min(), filtered_df['current_rate'].min())
        fig.add_trace(
            go.Scatter(
                x=[min_rate * 100, max_rate * 100],
                y=[min_rate * 100, max_rate * 100],
                mode='lines',
                name='Equal Line',
                line=dict(dash='dash', color='gray')
            )
        )
        
        fig.update_layout(
            title="Current vs Mean Funding Rates",
            xaxis_title="Mean Rate (%)",
            yaxis_title="Current Rate (%)",
            hovermode='closest'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Add trading recommendations
        st.subheader("Trading Opportunities")
        
        # Filter for high-confidence opportunities
        opps_df = filtered_df[
            (filtered_df['confidence_score'] > 0.7) &
            (abs(filtered_df['trend_strength']) > 0.5)
        ].head(5)
        
        if not opps_df.empty:
            for _, row in opps_df.iterrows():
                with st.expander(f"{row['symbol']} - {row['curve_shape']}"):
                    st.markdown(f"""
                    **Term Structure Metrics:**
                    - Current Rate: {row['current_rate']*100:.2f}%
                    - Mean Rate: {row['mean_rate']*100:.2f}%
                    - Confidence Score: {row['confidence_score']:.2f}
                    - Trend Strength: {row['trend_strength']:.2f}
                    
                    **Market Analysis:**
                    - {'Rates significantly above historical levels' if row['current_rate'] > row['q3_rate'] else 'Rates significantly below historical levels'}
                    - {'Strong trend detected' if abs(row['trend_strength']) > 0.7 else 'Moderate trend detected'}
                    - {'Multiple regime changes observed' if row['regime_changes'] > 2 else 'Stable regime'}
                    
                    **Trading Implications:**
                    - {'Consider mean reversion strategies' if abs(row['current_rate'] - row['mean_rate']) > row['std_rate'] else 'Consider trend-following strategies'}
                    - {'High confidence setup' if row['confidence_score'] > 0.8 else 'Moderate confidence setup'}
                    - Sample size: {row['sample_size']} data points
                    """)
        else:
            st.info("No high-confidence trading opportunities found in the current data")
            
    except Exception as e:
        logger.error(f"Error in display_term_structure_analysis: {e}")
        st.error("An error occurred while displaying term structure analysis")

def analyze_volatility_clustering(df: pd.DataFrame) -> pd.DataFrame:
    """
    Analyze volatility clustering using GARCH model with fallback to funding rates
    """
    try:
        results = []
        for symbol in df['symbol'].unique():
            try:
                symbol_data = df[df['symbol'] == symbol].copy()
                if len(symbol_data) < 24:  # Minimum data points needed
                    continue
                
                # Use funding rates if price data not available
                symbol_data['returns'] = symbol_data['funding_rate'].pct_change() * 100
                symbol_data = symbol_data.dropna()
                
                if len(symbol_data) >= 24:
                    # Rescale returns to avoid scaling warnings
                    returns_scale = symbol_data['returns'].abs().mean()
                    if returns_scale > 1000:
                        scale_factor = 0.1
                    elif returns_scale < 1:
                        scale_factor = 10
                    else:
                        scale_factor = 1
                    
                    # Apply scaling if needed
                    scaled_returns = symbol_data['returns'] * scale_factor
                    
                    try:
                        # Fit GARCH model with rescaling option
                        model = arch_model(scaled_returns, vol='Garch', p=1, q=1, dist='t', rescale=True)
                        res = model.fit(disp='off')
                        
                        # Get conditional volatility and adjust for scaling
                        conditional_vol = res.conditional_volatility / scale_factor
                        
                        # Calculate volatility clustering metrics
                        vol_persistence = res.params['alpha[1]'] + res.params['beta[1]']
                        current_vol = conditional_vol.iloc[-1]
                        vol_trend = (current_vol / conditional_vol.mean() - 1) * 100
                        
                        results.append({
                            'symbol': symbol,
                            'volatility': current_vol,
                            'vol_persistence': vol_persistence,
                            'vol_trend': vol_trend,
                            'clustering_score': vol_persistence * current_vol
                        })
                    except Exception as e:
                        logger.warning(f"Error fitting GARCH model for {symbol}: {e}")
                        # Try a simpler volatility measure as fallback
                        rolling_std = symbol_data['returns'].rolling(window=12).std()
                        if not rolling_std.empty:
                            current_vol = rolling_std.iloc[-1]
                            vol_trend = (current_vol / rolling_std.mean() - 1) * 100
                            results.append({
                                'symbol': symbol,
                                'volatility': current_vol,
                                'vol_persistence': 0.5,  # Default value
                                'vol_trend': vol_trend,
                                'clustering_score': 0.5 * current_vol
                            })
            except Exception as e:
                logger.warning(f"Error in volatility analysis for {symbol}: {e}")
                continue
        
        return pd.DataFrame(results)
    
    except Exception as e:
        logger.error(f"Error in analyze_arbitrage_efficiency: {e}")
        return pd.DataFrame()

def predict_funding_reversals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Predict potential funding rate reversals
    """
    try:
        results = []
        for symbol in df['symbol'].unique():
            try:
                symbol_data = df[df['symbol'] == symbol].copy()
                if len(symbol_data) < 24:
                    continue
                
                # Calculate funding rate momentum
                symbol_data['funding_momentum'] = symbol_data['funding_rate'].diff()
                
                # Detect trend changes using rolling statistics
                window = 12
                symbol_data['trend_ma'] = symbol_data['funding_rate'].rolling(window=window).mean()
                symbol_data['momentum_ma'] = symbol_data['funding_momentum'].rolling(window=window).mean()
                
                # Calculate reversal signals
                last_momentum = symbol_data['momentum_ma'].iloc[-1]
                last_trend = symbol_data['trend_ma'].iloc[-1]
                current_rate = symbol_data['funding_rate'].iloc[-1]
                
                # Score the reversal probability
                reversal_score = 0
                if last_momentum * last_trend < 0:  # Momentum opposing trend
                    reversal_score = abs(last_momentum / (last_trend + 1e-10))
                
                results.append({
                    'symbol': symbol,
                    'current_rate': current_rate,
                    'trend': last_trend,
                    'momentum': last_momentum,
                    'reversal_probability': min(reversal_score, 1.0)  # Cap at 1.0
                })
                
            except Exception as e:
                logger.warning(f"Error in funding reversal analysis for {symbol}: {e}")
                continue
                
        return pd.DataFrame(results)
    
    except Exception as e:
        logger.error(f"Error in predict_funding_reversals: {e}")
        return pd.DataFrame()

def display_market_overview(funding_data: pd.DataFrame):
    """Display market overview with key metrics"""
    try:
        if funding_data.empty:
            st.warning("No funding data available for market overview")
            return
            
        st.subheader("Market Overview")
        
        # Get the timestamp column (could be 'timestamp' or 'created_at')
        timestamp_col = 'timestamp'
        if timestamp_col not in funding_data.columns and 'created_at' in funding_data.columns:
            timestamp_col = 'created_at'
        
        if timestamp_col not in funding_data.columns:
            st.error("No timestamp column found in funding data")
            return
            
        # Calculate latest timestamp
        latest_timestamp = funding_data[timestamp_col].max()
        time_since_update = datetime.now(timezone.utc) - pd.to_datetime(latest_timestamp)
        
        # Calculate key metrics
        total_symbols = funding_data['symbol'].nunique()
        total_exchanges = funding_data['exchange'].nunique()
        
        # Calculate average funding rate
        avg_funding = funding_data['funding_rate'].mean() * 100  # Convert to percentage
        
        # Calculate funding rate volatility
        funding_volatility = funding_data['funding_rate'].std() * 100  # Convert to percentage
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Assets",
                f"{total_symbols}",
                help="Number of unique assets with funding data"
            )
            
        with col2:
            st.metric(
                "Exchanges",
                f"{total_exchanges}",
                help="Number of exchanges with funding data"
            )
            
        with col3:
            st.metric(
                "Avg Funding Rate",
                f"{avg_funding:.4f}%",
                help="Average funding rate across all assets"
            )
            
        with col4:
            st.metric(
                "Last Update",
                f"{time_since_update.total_seconds() / 60:.1f} min ago",
                help="Time since last data update"
            )
            
        # Display funding rate distribution
        st.subheader("Funding Rate Distribution")
        
        # Create histogram
        fig = px.histogram(
            funding_data,
            x='funding_rate',
            nbins=50,
            title="Current Funding Rate Distribution",
            labels={'funding_rate': 'Funding Rate'},
            color_discrete_sequence=['blue']
        )
        
        # Update layout
        fig.update_layout(
            xaxis_title="Funding Rate",
            yaxis_title="Count",
            template="plotly_dark"
        )
        
        # Add vertical line at zero
        fig.add_vline(
            x=0,
            line_dash="dash",
            line_color="red",
            annotation_text="Zero Line",
            annotation_position="top right"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
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
        logger.error(f"Error in market overview: {e}")
        st.error("Error displaying market overview. Please check the data and try again.")

def main():
    """Main dashboard function with improved error handling and user feedback"""
    try:
        # Initialize enhancements if available
        if 'enhancements_initialized' not in st.session_state and ENHANCEMENTS_AVAILABLE:
            try:
                init_enhancements()
                st.session_state.enhancements_initialized = True
                logging.info("Dashboard enhancements initialized")
            except Exception as e:
                logging.error(f"Error initializing enhancements: {e}")
                st.session_state.enhancements_initialized = False
        
        # Set page config
        st.set_page_config(
            page_title="Funding Strategy Dashboard",
            page_icon="📈",
            layout="wide"
        )

        # Add custom CSS for better UI
        st.markdown("""
            <style>
            .stProgress > div > div > div > div {
                background-color: #1f77b4;
            }
            .stTabs [data-baseweb="tab-list"] {
                gap: 2px;
            }
            .stTabs [data-baseweb="tab"] {
                padding: 10px 20px;
            }
            .stAlert {
                padding: 1rem;
                margin-bottom: 1rem;
            }
            </style>
        """, unsafe_allow_html=True)

        # Initialize session state
        if 'funding_data' not in st.session_state:
            st.session_state.funding_data = None
        if 'term_structure' not in st.session_state:
            st.session_state.term_structure = None
        if 'is_loading' not in st.session_state:
            st.session_state.is_loading = False

        # Dashboard title and description
        st.title("📊 Funding Strategy Dashboard")
        st.markdown("""
        This dashboard analyzes funding rates, price movements, and market regimes to identify trading opportunities.
        """)

        # Sidebar settings
        with st.sidebar:
            st.title("Settings")
            
            # Add data loading options in sidebar
            st.sidebar.title("Data Options")
            
            # Add option to use enhanced data retrieval
            if ENHANCEMENTS_AVAILABLE:
                use_enhanced_data = st.sidebar.checkbox("Use Enhanced Data Retrieval", value=True, 
                                                      help="Use enhanced data retrieval methods with fallbacks to exchange APIs")
            else:
                use_enhanced_data = False
                
            # Add lookback period selection
            lookback_options = {
                "1 Day": 24,
                "3 Days": 72,
                "1 Week": 168,
                "2 Weeks": 336,
                "1 Month": 720
            }
            lookback_period = st.sidebar.selectbox("Lookback Period", list(lookback_options.keys()), index=1)
            lookback_hours = lookback_options[lookback_period]
            
            # Add refresh button
            if st.sidebar.button("🔄 Refresh Data"):
                st.session_state.is_loading = True
                st.session_state.funding_data = None
                st.session_state.term_structure = None
                
            # Load data with progress indicator
            if st.session_state.funding_data is None or st.session_state.is_loading:
                with st.spinner("Loading funding data..."):
                    try:
                        # Use enhanced data retrieval if available and selected
                        if ENHANCEMENTS_AVAILABLE and use_enhanced_data and 'get_enhanced_funding_data' in st.session_state:
                            st.session_state.funding_data = st.session_state.get_enhanced_funding_data(lookback_hours)
                            st.info("Using enhanced data retrieval methods")
                        else:
                            st.session_state.funding_data = get_funding_data(lookback_hours)
                            
                        if not st.session_state.funding_data.empty:
                            # Validate the data has required columns
                            required_columns = ['symbol', 'exchange', 'timestamp', 'funding_rate']
                            missing_columns = [col for col in required_columns if col not in st.session_state.funding_data.columns]
                            
                            if missing_columns:
                                st.error(f"Data is missing required columns: {', '.join(missing_columns)}")
                                logger.error(f"Funding data missing required columns: {missing_columns}")
                                st.session_state.funding_data = None
                            else:
                                st.success(f"Loaded {len(st.session_state.funding_data)} funding rate records")
                                
                                # Calculate term structure
                                st.session_state.term_structure = analyze_term_structure(st.session_state.funding_data)
                                
                                # Log analysis completion
                                logger.info(f"Analysis completed for {len(st.session_state.funding_data)} records")
                        else:
                            st.warning("No funding data available for the selected period")
                            
                    except Exception as e:
                        st.error(f"Error loading data: {str(e)}")
                        logger.error(f"Error loading funding data: {e}")
                        st.session_state.funding_data = None
                        
                st.session_state.is_loading = False

        # Display the main dashboard content
        if st.session_state.funding_data is not None and not st.session_state.funding_data.empty:
            # Display market overview
            display_market_overview(st.session_state.funding_data)
            
            # Create tabs for different analyses
            tabs = st.tabs([
                "Funding Analysis", 
                "Term Structure", 
                "Volatility Clustering",
                "Arbitrage Efficiency",
                "Funding Reversals",
                "Asset Analysis"
            ])
            
            with tabs[0]:
                display_funding_analysis(st.session_state.funding_data)
                
            with tabs[1]:
                if st.session_state.term_structure is not None:
                    display_term_structure_analysis(st.session_state.term_structure)
                else:
                    st.warning("Term structure analysis not available. Please refresh the data.")
                    
            with tabs[2]:
                try:
                    # Try to use the enhanced function from session state if available
                    if ENHANCEMENTS_AVAILABLE and 'analyze_volatility_clustering' in st.session_state:
                        volatility_df = st.session_state.analyze_volatility_clustering(st.session_state.funding_data)
                        st.session_state.display_volatility_clustering_analysis(volatility_df)
                    elif FUNCTIONS_IMPORTED:
                        # Use the directly imported functions
                        volatility_df = analyze_volatility_clustering(st.session_state.funding_data)
                        display_volatility_clustering_analysis(volatility_df)
                    else:
                        # Fall back to the original functions
                        volatility_df = analyze_volatility_clustering(st.session_state.funding_data)
                        display_volatility_clustering_analysis(volatility_df)
                except Exception as e:
                    logger.error(f"Error in volatility clustering analysis: {e}")
                    st.error(f"Error in volatility analysis: {str(e)}")
                
            with tabs[3]:
                try:
                    # Try to use the enhanced function from session state if available
                    if ENHANCEMENTS_AVAILABLE and 'analyze_arbitrage_efficiency' in st.session_state:
                        arbitrage_df = st.session_state.analyze_arbitrage_efficiency(st.session_state.funding_data)
                        st.session_state.display_arbitrage_efficiency_analysis(arbitrage_df)
                    elif FUNCTIONS_IMPORTED:
                        # Use the directly imported functions
                        arbitrage_df = analyze_arbitrage_efficiency(st.session_state.funding_data)
                        display_arbitrage_efficiency_analysis(arbitrage_df)
                    else:
                        # Fall back to the original functions
                        arbitrage_df = analyze_arbitrage_efficiency(st.session_state.funding_data)
                        display_arbitrage_efficiency_analysis(arbitrage_df)
                except Exception as e:
                    logger.error(f"Error in arbitrage efficiency analysis: {e}")
                    st.error(f"Error in arbitrage analysis: {str(e)}")
                
            with tabs[4]:
                try:
                    # Try to use the enhanced function from session state if available
                    if ENHANCEMENTS_AVAILABLE and 'predict_funding_reversals' in st.session_state:
                        reversal_df = st.session_state.predict_funding_reversals(st.session_state.funding_data)
                        st.session_state.display_funding_reversal_analysis(reversal_df)
                    elif FUNCTIONS_IMPORTED:
                        # Use the directly imported functions
                        reversal_df = predict_funding_reversals(st.session_state.funding_data)
                        display_funding_reversal_analysis(reversal_df)
                    else:
                        # Fall back to the original functions
                        reversal_df = predict_funding_reversals(st.session_state.funding_data)
                        display_funding_reversal_analysis(reversal_df)
                except Exception as e:
                    logger.error(f"Error in funding reversal analysis: {e}")
                    st.error(f"Error in reversal analysis: {str(e)}")
                
            with tabs[5]:
                top_opps = analyze_top_opportunities(st.session_state.funding_data)
                display_asset_analysis(top_opps, st.session_state.funding_data)
                
            # Add enhanced features if available
            if ENHANCEMENTS_AVAILABLE and 'enhance_dashboard' in st.session_state:
                try:
                    st.session_state.enhance_dashboard()
                except Exception as e:
                    logger.error(f"Error displaying enhanced features: {e}")
                    st.sidebar.error("Error displaying enhanced features. See logs for details.")
        else:
            st.info("Please load data to view the dashboard.")
            
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        st.error(f"An error occurred: {str(e)}")
        if st.button("Restart Dashboard"):
            st.experimental_rerun()

if __name__ == "__main__":
    main()