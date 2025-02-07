import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pytz
from analysis import fetch_all_records
import json
import os
from pathlib import Path
import hashlib

# Add this function to handle datetime parsing
def safe_parse_datetime(dt_str):
    """Safely parse datetime strings in various formats"""
    if pd.isna(dt_str):
        return None
        
    if isinstance(dt_str, (datetime, pd.Timestamp)):
        return pd.to_datetime(dt_str)
        
    try:
        # Try pandas default parser first with mixed format
        return pd.to_datetime(dt_str, format='mixed', utc=True)
    except:
        try:
            # Try explicit formats
            formats = [
                '%Y-%m-%dT%H:%M:%S%z',
                '%Y-%m-%dT%H:%M:%S.%f%z',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%d %H:%M:%S%z',
                '%Y-%m-%d %H:%M:%S'
            ]
            
            for fmt in formats:
                try:
                    return pd.to_datetime(dt_str, format=fmt)
                except:
                    continue
                    
            # Last resort: try ISO format
            return pd.to_datetime(dt_str, format='ISO8601')
        except Exception as e:
            st.warning(f"Error parsing datetime: {dt_str}, Error: {str(e)}")
            return None

def analyze_market_trends(df):
    """Analyze market trends and provide insights"""
    insights = []
    
    # Funding rate trends
    avg_rate = df['funding_rate'].mean()
    rate_std = df['funding_rate'].std()
    
    insights.append(f"Average funding rate: {avg_rate:.4%} (±{rate_std:.4%})")
    
    # Market direction
    positive_rates = (df['funding_rate'] > 0).mean()
    insights.append(f"Markets with positive funding: {positive_rates:.1%}")
    
    # Volatility
    high_vol_markets = df.groupby('symbol')['funding_rate'].std().nlargest(5)
    insights.append("Most volatile markets:")
    for symbol, vol in high_vol_markets.items():
        insights.append(f"  • {symbol}: {vol:.4%} std dev")
    
    return insights

# Add cache directory configuration
CACHE_DIR = Path("./cache")
CACHE_DIR.mkdir(exist_ok=True)

def get_cache_key(data_type: str) -> str:
    """Generate a cache key based on current date"""
    today = datetime.now(pytz.UTC).strftime('%Y-%m-%d')
    return hashlib.md5(f"{data_type}_{today}".encode()).hexdigest()

def save_to_cache(data: dict, cache_key: str):
    """Save processed data to local cache"""
    try:
        cache_file = CACHE_DIR / f"{cache_key}.json"
        with open(cache_file, 'w') as f:
            json.dump(data, f, default=str)
    except Exception as e:
        st.warning(f"Failed to save cache: {str(e)}")

def load_from_cache(cache_key: str) -> dict:
    """Load data from local cache if available"""
    try:
        cache_file = CACHE_DIR / f"{cache_key}.json"
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                return json.load(f)
    except Exception as e:
        st.warning(f"Failed to load cache: {str(e)}")
    return None

@st.cache_data(ttl=3600)
def store_analysis_results(results: dict):
    """Store analysis results in Supabase"""
    try:
        timestamp = datetime.now(pytz.UTC)
        data = {
            'timestamp': timestamp.isoformat(),
            'results': results
        }
        
        response = supabase.table('funding_analysis_results').insert(data).execute()
        return response.data
    except Exception as e:
        st.error(f"Failed to store results: {str(e)}")
        return None

def get_latest_analysis():
    """Get latest analysis results from Supabase"""
    try:
        response = supabase.table('funding_analysis_results')\
            .select('*')\
            .order('timestamp', desc=True)\
            .limit(1)\
            .execute()
            
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        st.error(f"Failed to fetch latest analysis: {str(e)}")
        return None

# Update load_data function to use caching
@st.cache_data(ttl=3600)
def load_data():
    """Load and process market data with caching"""
    with st.spinner('Loading data...'):
        try:
            # Try to load from cache first
            cache_key = get_cache_key('funding_data')
            cached_data = load_from_cache(cache_key)
            
            if cached_data and isinstance(cached_data.get('processed_data', None), pd.DataFrame):
                st.success("Loaded from cache")
                return cached_data
            
            # If no cache or invalid cache, fetch from Supabase
            dfs = {}
            
            # Fetch each table with error handling
            tables = {
                'funding_market_snapshots': 'Market Snapshots',
                'predicted_funding_rates': 'Predicted Rates',
                'binance_funding_rates': 'Binance Funding',
                'hyperliquid_funding_rates': 'Hyperliquid Funding'
            }
            
            for table_name, display_name in tables.items():
                try:
                    df = fetch_all_records(table_name)
                    if isinstance(df, pd.DataFrame) and not df.empty:
                        # Convert string timestamps to datetime
                        if 'created_at' in df.columns:
                            df['created_at'] = pd.to_datetime(df['created_at'], format='mixed')
                        dfs[table_name] = df
                        st.success(f"Loaded {len(df)} records from {display_name}")
                    else:
                        st.warning(f"No data available for {display_name}")
                except Exception as e:
                    st.warning(f"Error loading {display_name}: {str(e)}")
            
            # Process market snapshots if available
            market_snapshots = dfs.get('funding_market_snapshots')
            if isinstance(market_snapshots, pd.DataFrame) and not market_snapshots.empty:
                df = market_snapshots.copy()
                
                # Convert datetime with error handling
                df['created_at'] = pd.to_datetime(df['created_at'], format='mixed')
                df = df.dropna(subset=['created_at'])
                
                # Convert numeric columns safely
                numeric_cols = ['funding_rate', 'mark_price', 'open_interest']
                for col in numeric_cols:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                
                df = df.dropna(subset=['funding_rate'])
                
                if len(df) == 0:
                    raise ValueError("No valid data after cleaning")
                
                # Add derived columns
                df['hour'] = df['created_at'].dt.hour
                df['day_of_week'] = df['created_at'].dt.day_name()
                df['annualized_rate'] = df['funding_rate'] * 365 * 24
                
                # Calculate market stats
                df['volatility'] = df.groupby('symbol')['funding_rate'].transform('std')
                df['avg_daily_rate'] = df.groupby('symbol')['funding_rate'].transform('mean')
                
                # Store processed data
                dfs['processed_data'] = df
                
                # Save to cache
                save_to_cache(dfs, cache_key)
                
                # Store analysis results
                try:
                    analysis_results = {
                        'market_stats': {
                            'total_markets': int(len(df['symbol'].unique())),
                            'avg_funding_rate': float(df['funding_rate'].mean()),
                            'avg_annualized_rate': float(df['annualized_rate'].mean()),
                            'total_volume': float(df.get('volume_24h', pd.Series([0])).sum())
                        },
                        'top_opportunities': df.nlargest(10, abs(df['funding_rate']))[
                            ['symbol', 'exchange', 'funding_rate', 'annualized_rate']
                        ].to_dict('records'),
                        'market_insights': analyze_market_trends(df)
                    }
                    
                    store_analysis_results(analysis_results)
                except Exception as e:
                    st.warning(f"Error storing analysis results: {str(e)}")
                
                return dfs
            else:
                raise ValueError("No market snapshot data available")
            
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")
            st.error("Please check the data source and try again.")
            return {}

def get_recent_data(df, hours=1):
    """Get recent data with proper timezone handling and validation"""
    try:
        if df is None or df.empty:
            return pd.DataFrame()
            
        utc_now = datetime.now(pytz.UTC)
        cutoff = utc_now - timedelta(hours=hours)
        
        # Ensure created_at is timezone-aware
        if df['created_at'].dt.tz is None:
            df['created_at'] = df['created_at'].dt.tz_localize('UTC')
            
        recent = df[df['created_at'] > cutoff].copy()
        
        if recent.empty:
            st.warning(f"No data found in the last {hours} hours")
            
        return recent
        
    except Exception as e:
        st.error(f"Error filtering recent data: {str(e)}")
        return pd.DataFrame()

# Page setup
st.set_page_config(page_title="Funding Analytics", layout="wide")
st.title("📊 Funding Rate Analytics")

# Load data
dfs = load_data()

if not isinstance(dfs, dict):
    st.error("Invalid data format. Please refresh the page.")
    st.stop()

# Check for processed data
processed_data = dfs.get('processed_data')
if not isinstance(processed_data, pd.DataFrame) or processed_data.empty:
    st.error("No processed data available. Please check the data source.")
    st.stop()

# Navigation
analysis_type = st.sidebar.selectbox(
    "Choose Analysis",
    ["Quick Overview", "Funding Patterns", "Top Opportunities", "Advanced Analysis"]
)

if analysis_type == "Quick Overview":
    if 'processed_data' in dfs and not dfs['processed_data'].empty:
        df = dfs['processed_data']
        
        # Simple metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                "Active Markets", 
                len(df['symbol'].unique())
            )
        with col2:
            current_rate = df.groupby('symbol')['funding_rate'].last().mean()
            st.metric(
                "Average Current Rate", 
                f"{current_rate:.4%}"
            )
        with col3:
            ann_rate = current_rate * 365 * 24
            st.metric(
                "Annualized", 
                f"{ann_rate:.2%}"
            )
        
        # Simple funding rate distribution
        st.subheader("Funding Rate Distribution")
        fig = px.histogram(
            df,
            x='funding_rate',
            nbins=50,
            title="Current Funding Rates"
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        
        # Top 5 positive and negative rates
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Top 5 Positive Rates")
            top_pos = df.nlargest(5, 'funding_rate')[['symbol', 'funding_rate']]
            top_pos['funding_rate'] = top_pos['funding_rate'].apply(lambda x: f"{x:.4%}")
            st.dataframe(top_pos, hide_index=True)
            
        with col2:
            st.subheader("Top 5 Negative Rates")
            top_neg = df.nsmallest(5, 'funding_rate')[['symbol', 'funding_rate']]
            top_neg['funding_rate'] = top_neg['funding_rate'].apply(lambda x: f"{x:.4%}")
            st.dataframe(top_neg, hide_index=True)

elif analysis_type == "Funding Patterns":
    if 'processed_data' in dfs:
        df = dfs['processed_data']
        
        # Daily patterns
        st.subheader("Daily Funding Patterns")
        daily_avg = df.groupby('day_of_week')['funding_rate'].mean().reset_index()
        fig = px.bar(
            daily_avg,
            x='day_of_week',
            y='funding_rate',
            title="Average Funding Rate by Day"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Hourly patterns
        st.subheader("Hourly Funding Patterns")
        hourly_avg = df.groupby('hour')['funding_rate'].mean().reset_index()
        fig = px.line(
            hourly_avg,
            x='hour',
            y='funding_rate',
            title="Average Funding Rate by Hour"
        )
        st.plotly_chart(fig, use_container_width=True)

elif analysis_type == "Top Opportunities":
    if 'processed_data' in dfs and isinstance(dfs['processed_data'], pd.DataFrame):
        df = dfs['processed_data']
        
        try:
            recent = get_recent_data(df)
            
            if not recent.empty:
                st.subheader("Current Top Opportunities")
                
                # Add filters
                col1, col2 = st.columns(2)
                with col1:
                    exchanges = sorted(recent['exchange'].unique())
                    selected_exchange = st.selectbox("Select Exchange", ["All"] + list(exchanges))
                
                with col2:
                    min_rate = st.slider("Minimum Annualized Rate", 
                                       min_value=0.0, 
                                       max_value=100.0, 
                                       value=10.0,
                                       format="%g%%")
                
                # Filter data
                filtered = recent.copy()
                if selected_exchange != "All":
                    filtered = filtered[filtered['exchange'] == selected_exchange]
                
                # Ensure funding_rate is numeric and handle missing values
                filtered['funding_rate'] = pd.to_numeric(filtered['funding_rate'], errors='coerce')
                filtered = filtered.dropna(subset=['funding_rate'])
                
                # Filter by minimum rate
                min_rate_decimal = min_rate / 100
                filtered = filtered[abs(filtered['funding_rate']) * 365 * 24 >= min_rate_decimal]
                
                if not filtered.empty:
                    # Sort by absolute funding rate and get top 10
                    sorted_indices = filtered['funding_rate'].abs().sort_values(ascending=False).index[:10]
                    opportunities = filtered.loc[sorted_indices]
                    
                    # Select and format columns for display
                    display_columns = ['symbol', 'exchange', 'funding_rate', 'annualized_rate', 'volatility']
                    opportunities = opportunities[display_columns].copy()
                    
                    # Format for display
                    display_df = opportunities.copy()
                    for col in ['funding_rate', 'annualized_rate', 'volatility']:
                        if col in display_df.columns:
                            display_df[col] = display_df[col].apply(
                                lambda x: f"{x:.4%}" if pd.notnull(x) else "N/A"
                            )
                    
                    # Display results
                    st.dataframe(
                        display_df,
                        hide_index=True,
                        column_config={
                            "symbol": "Symbol",
                            "exchange": "Exchange",
                            "funding_rate": "Current Rate",
                            "annualized_rate": "Annual Rate",
                            "volatility": "Volatility"
                        }
                    )
                    
                    # Add market insights
                    st.subheader("Market Analysis")
                    
                    # Summary metrics
                    metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
                    with metrics_col1:
                        st.metric(
                            "Average Rate", 
                            f"{filtered['funding_rate'].mean():.4%}"
                        )
                    with metrics_col2:
                        st.metric(
                            "Highest Rate", 
                            f"{filtered['funding_rate'].max():.4%}"
                        )
                    with metrics_col3:
                        st.metric(
                            "Total Opportunities", 
                            len(filtered)
                        )
                    
                    # Risk analysis
                    st.subheader("Risk vs Return Analysis")
                    fig = px.scatter(
                        filtered,
                        x='funding_rate',
                        y='volatility',
                        color='exchange',
                        hover_data=['symbol', 'annualized_rate'],
                        title="Opportunity Risk Profile"
                    )
                    fig.update_layout(
                        xaxis_title="Funding Rate",
                        yaxis_title="Volatility",
                        showlegend=True
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                else:
                    st.warning(f"No opportunities found above {min_rate}% annualized rate")
            else:
                st.warning("No recent data available")
                
        except Exception as e:
            st.error(f"Error processing opportunities: {str(e)}")
            st.error("Please try adjusting the filters or refreshing the data")

elif analysis_type == "Advanced Analysis":
    st.subheader("Advanced Market Analysis")
    
    if 'processed_data' in dfs and not dfs['processed_data'].empty:
        df = dfs['processed_data']
        
        # Market volatility analysis
        st.subheader("Market Volatility")
        volatility = df.groupby('symbol')['funding_rate'].std().sort_values(ascending=False)
        
        fig = px.bar(
            volatility.head(10),
            title="Top 10 Most Volatile Markets"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Exchange comparison if multiple exchanges
        if len(df['exchange'].unique()) > 1:
            st.subheader("Exchange Comparison")
            exchange_stats = df.groupby('exchange').agg({
                'funding_rate': ['mean', 'std', 'count']
            }).round(6)
            
            st.dataframe(exchange_stats)

# Add refresh button
if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.experimental_rerun()

# Show last update time
st.sidebar.markdown("---")
st.sidebar.text(f"Last updated: {datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}")

# Add a function to display historical analysis
def show_historical_analysis():
    st.subheader("Historical Analysis")
    
    try:
        response = supabase.table('funding_analysis_results')\
            .select('*')\
            .order('timestamp', desc=True)\
            .limit(24)\
            .execute()
            
        if response.data:
            # Create time series of key metrics
            historical_data = pd.DataFrame(response.data)
            historical_data['timestamp'] = pd.to_datetime(historical_data['timestamp'])
            
            # Plot key metrics over time
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=historical_data['timestamp'],
                y=[r['results']['market_stats']['avg_funding_rate'] for r in historical_data['results']],
                name='Avg Funding Rate'
            ))
            
            st.plotly_chart(fig, use_container_width=True)
            
    except Exception as e:
        st.error(f"Failed to load historical analysis: {str(e)}")

# Add to the sidebar
st.sidebar.markdown("---")
if st.sidebar.checkbox("Show Historical Analysis"):
    show_historical_analysis() 