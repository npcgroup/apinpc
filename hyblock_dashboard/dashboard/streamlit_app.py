import os
import sys
import json
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.database import connect_to_database, execute_query, get_logger

# Set up logger
logger = get_logger("streamlit_dashboard")

# Set page config
st.set_page_config(
    page_title="Hyblock Data Dashboard",
    page_icon="📊",
    layout="wide"
)

# Title
st.title("Hyblock SUI Data Dashboard")

# Function to load endpoints
def load_endpoints():
    try:
        conn = connect_to_database()
        if not conn:
            logger.error("Failed to connect to database")
            return []
        
        query = """
            SELECT DISTINCT endpoint
            FROM hyblock_data
            ORDER BY endpoint
        """
        
        results = execute_query(conn, query)
        conn.close()
        
        if results:
            return [endpoint[0] for endpoint in results]
        
        return []
    
    except Exception as e:
        logger.error(f"Error loading endpoints: {e}")
        return []

# Function to load filters
def load_filters(endpoint, coin):
    try:
        if not endpoint or not coin:
            return [], []
        
        conn = connect_to_database()
        if not conn:
            logger.error("Failed to connect to database")
            return [], []
        
        # Get available exchanges
        exchange_query = """
            SELECT DISTINCT exchange
            FROM hyblock_data
            WHERE endpoint = %s AND coin = %s AND exchange IS NOT NULL
            ORDER BY exchange
        """
        
        exchange_results = execute_query(conn, exchange_query, (endpoint, coin))
        
        # Get available timeframes
        timeframe_query = """
            SELECT DISTINCT timeframe
            FROM hyblock_data
            WHERE endpoint = %s AND coin = %s AND timeframe IS NOT NULL
            ORDER BY timeframe
        """
        
        timeframe_results = execute_query(conn, timeframe_query, (endpoint, coin))
        
        conn.close()
        
        exchanges = [exch[0] for exch in exchange_results if exch[0]]
        timeframes = [tf[0] for tf in timeframe_results if tf[0]]
        
        return exchanges, timeframes
    
    except Exception as e:
        logger.error(f"Error loading filters: {e}")
        return [], []

# Function to load data
def load_data(endpoint, coin, exchange, timeframe, time_range):
    try:
        if not endpoint or not coin:
            return None
        
        # Calculate the time range
        now = datetime.utcnow()
        if time_range == "1h":
            start_time = now - timedelta(hours=1)
        elif time_range == "6h":
            start_time = now - timedelta(hours=6)
        elif time_range == "24h":
            start_time = now - timedelta(hours=24)
        else:  # 7d
            start_time = now - timedelta(days=7)
        
        conn = connect_to_database()
        if not conn:
            logger.error("Failed to connect to database")
            return None
        
        # Build the query
        query = """
            SELECT timestamp, data
            FROM hyblock_data
            WHERE endpoint = %s AND coin = %s
        """
        
        params = [endpoint, coin]
        
        if exchange:
            query += " AND exchange = %s"
            params.append(exchange)
        
        if timeframe:
            query += " AND timeframe = %s"
            params.append(timeframe)
        
        query += " AND timestamp >= %s ORDER BY timestamp"
        params.append(start_time)
        
        results = execute_query(conn, query, params)
        conn.close()
        
        if not results:
            return None
        
        # Process the data
        data_points = []
        for timestamp, data_json in results:
            try:
                data_dict = json.loads(data_json)
                if isinstance(data_dict, dict) and "data" in data_dict:
                    for item in data_dict["data"]:
                        # Add the database timestamp as a reference
                        item["db_timestamp"] = timestamp
                        
                        # Handle timestamp conversion based on type
                        if "timestamp" in item:
                            try:
                                if isinstance(item["timestamp"], (int, float)):
                                    # Check if it's in milliseconds (13 digits) or seconds (10 digits)
                                    if len(str(int(item["timestamp"]))) > 10:
                                        item["timestamp"] = pd.to_datetime(item["timestamp"], unit='ms')
                                    else:
                                        item["timestamp"] = pd.to_datetime(item["timestamp"], unit='s')
                                elif isinstance(item["timestamp"], str):
                                    # Try to parse ISO format string timestamps
                                    try:
                                        item["timestamp"] = pd.to_datetime(item["timestamp"])
                                    except:
                                        # If parsing fails, check if it might be a Unix timestamp in string form
                                        if item["timestamp"].isdigit():
                                            ts_val = int(item["timestamp"])
                                            if len(item["timestamp"]) > 10:
                                                item["timestamp"] = pd.to_datetime(ts_val, unit='ms')
                                            else:
                                                item["timestamp"] = pd.to_datetime(ts_val, unit='s')
                            except Exception as e:
                                logger.error(f"Error converting timestamp {item['timestamp']}: {e}")
                                # If conversion fails, use the database timestamp as a fallback
                                item["timestamp"] = timestamp
                        data_points.append(item)
            except Exception as e:
                logger.error(f"Error processing data: {e}")
        
        if not data_points:
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame(data_points)
        return df
    
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        return None

# Sidebar filters
st.sidebar.header("Filters")

# Endpoint selection
endpoints = load_endpoints()
endpoint = st.sidebar.selectbox("Select Endpoint", options=endpoints, index=0 if endpoints else None)

# Coin selection (hardcoded to SUI for now)
coin = st.sidebar.selectbox("Select Coin", options=["SUI"], index=0)

# Load exchanges and timeframes based on endpoint and coin
exchanges, timeframes = load_filters(endpoint, coin)

# Exchange selection
exchange = st.sidebar.selectbox("Select Exchange", options=exchanges, index=0 if exchanges else None)

# Timeframe selection
timeframe = st.sidebar.selectbox("Select Timeframe", options=timeframes, index=0 if timeframes else None)

# Time range selection
time_range = st.sidebar.radio(
    "Time Range",
    options=["1h", "6h", "24h", "7d"],
    index=2  # Default to 24h
)

# Load data
data = load_data(endpoint, coin, exchange, timeframe, time_range)

# Main content
if data is not None:
    # Display summary statistics
    st.header("Summary Statistics")
    st.dataframe(data.describe())
    
    # Determine which columns to plot
    numeric_columns = data.select_dtypes(include=['number']).columns.tolist()
    
    if numeric_columns:
        # Create time series plot
        st.header("Time Series Data")
        
        # Select column to plot
        plot_column = st.selectbox("Select Column to Plot", options=numeric_columns)
        
        # Create plot
        fig = px.line(
            data,
            x="timestamp",
            y=plot_column,
            title=f"{endpoint} - {coin} - {plot_column}"
        )
        
        # Display plot
        st.plotly_chart(fig, use_container_width=True)
    
    # Display raw data
    st.header("Raw Data")
    st.dataframe(data)
else:
    st.warning("No data available for the selected filters. Please try different filters.")

# Add auto-refresh
st.sidebar.header("Auto Refresh")
auto_refresh = st.sidebar.checkbox("Enable Auto Refresh", value=False)

if auto_refresh:
    refresh_interval = st.sidebar.slider("Refresh Interval (seconds)", min_value=5, max_value=300, value=60)
    st.sidebar.write(f"Dashboard will refresh every {refresh_interval} seconds")
    
    # Add auto-refresh using JavaScript
    st.markdown(
        f"""
        <script>
            setTimeout(function(){{
                window.location.reload();
            }}, {refresh_interval * 1000});
        </script>
        """,
        unsafe_allow_html=True
    ) 