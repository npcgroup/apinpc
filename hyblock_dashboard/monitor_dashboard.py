#!/usr/bin/env python3
"""
Hyblock Data Collection Monitoring Dashboard

This script provides a Streamlit dashboard for monitoring the status of data collection.
"""

import os
import sys
import json
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time

# Try to import MCP tools if available
try:
    from mcp__query import mcp__query
except ImportError:
    # This will be handled in the execute_mcp_query function
    pass

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.database import connect_to_database, execute_query, get_logger

# Set up logger
logger = get_logger("monitor_dashboard")

# MCP Query Support
def execute_mcp_query(query, params=None):
    """
    Execute a query using MCP and return the results as a DataFrame.
    
    Args:
        query (str): The SQL query to execute
        params (dict, optional): Parameters for the query
        
    Returns:
        pandas.DataFrame: The query results as a DataFrame, or None if there was an error
    """
    try:
        # Log the query being executed
        logger.info(f"Executing MCP query: {query}")
        
        # Try to use the mcp__query function if it's available
        if 'mcp__query' in globals():
            try:
                logger.info("Using MCP query function")
                result = mcp__query(sql=query)
                
                # If we get a result, process it
                if result is not None:
                    # Convert result to DataFrame if it's not already
                    if isinstance(result, pd.DataFrame):
                        df = result
                    elif isinstance(result, list):
                        df = pd.DataFrame(result)
                    elif isinstance(result, dict) and 'rows' in result:
                        df = pd.DataFrame(result['rows'])
                    elif isinstance(result, str):
                        try:
                            # Try to parse as JSON
                            data = json.loads(result)
                            if isinstance(data, list):
                                df = pd.DataFrame(data)
                            elif isinstance(data, dict) and 'rows' in data:
                                df = pd.DataFrame(data['rows'])
                            else:
                                df = pd.DataFrame([data])
                        except json.JSONDecodeError:
                            logger.error(f"Failed to parse MCP result as JSON: {result}")
                            return _execute_fallback_query(query, params)
                    else:
                        logger.error(f"Unexpected MCP result format: {type(result)}")
                        return _execute_fallback_query(query, params)
                    
                    # Process dataframe - convert timestamps with explicit format
                    for col in df.columns:
                        if 'time' in col.lower() or 'date' in col.lower():
                            try:
                                # Try common timestamp formats
                                if df[col].dtype == 'object':
                                    # Sample the first value to check format
                                    sample = df[col].dropna().iloc[0] if not df[col].dropna().empty else None
                                    if sample and isinstance(sample, str):
                                        if 'T' in sample and ('+' in sample or 'Z' in sample):
                                            # ISO format
                                            df[col] = pd.to_datetime(df[col], format='ISO8601', errors='coerce')
                                        elif '-' in sample and ':' in sample:
                                            # Standard SQL format: YYYY-MM-DD HH:MM:SS
                                            df[col] = pd.to_datetime(df[col], format='%Y-%m-%d %H:%M:%S', errors='coerce')
                                        else:
                                            # Fall back to infer
                                            df[col] = pd.to_datetime(df[col], errors='coerce')
                                    else:
                                        df[col] = pd.to_datetime(df[col], errors='coerce')
                            except Exception:
                                pass
                    
                    return df
            except Exception as e:
                logger.error(f"Error using MCP query function: {e}")
        
        # Fall back to direct database connection
        return _execute_fallback_query(query, params)
    except Exception as e:
        logger.error(f"Error executing MCP query: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None

def _execute_fallback_query(query, params=None):
    """
    Execute a query directly via database connection.
    
    Args:
        query (str): The SQL query to execute
        params (dict, optional): Parameters for the query
        
    Returns:
        pandas.DataFrame: The query results as a DataFrame, or None if there was an error
    """
    try:
        logger.info("Using direct database connection for query")
        # Connect to database
        conn = connect_to_database()
        if not conn:
            logger.error("Failed to connect to database")
            return None
        
        # Execute query
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        # Get results
        results = cursor.fetchall()
        
        # Get column names from cursor
        column_names = [desc[0] for desc in cursor.description]
        
        # Close connection
        conn.close()
        
        if not results:
            logger.warning("Query returned no results")
            return pd.DataFrame(columns=column_names)
        
        # Create DataFrame
        df = pd.DataFrame(results, columns=column_names)
        
        # Convert timestamp columns with explicit format
        for col in df.columns:
            if 'time' in col.lower() or 'date' in col.lower():
                try:
                    # For SQL timestamp columns, use specific format
                    if df[col].dtype == 'object':
                        df[col] = pd.to_datetime(df[col], format='%Y-%m-%d %H:%M:%S', errors='coerce')
                    else:
                        df[col] = pd.to_datetime(df[col], errors='coerce')
                except Exception:
                    pass
                    
        return df
    except Exception as e:
        logger.error(f"Error executing database query: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None

# Page configuration
st.set_page_config(
    page_title="Hyblock Data Collection Monitor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom CSS
st.markdown("""
    <style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        margin: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #0068c9;
    }
    .metric-label {
        font-size: 14px;
        color: #555;
    }
    .data-quality-high {
        color: #00cc66;
        font-weight: bold;
    }
    .data-quality-medium {
        color: #ffcc00;
        font-weight: bold;
    }
    .data-quality-low {
        color: #ff3300;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# Title and description
st.title("🔍 Hyblock Data Collection Monitor")
st.markdown("Monitor the status of data collection from the Hyblock API")

# Function to get collection statistics
def get_collection_stats():
    """Get collection statistics from the database."""
    try:
        query = """
            SELECT 
                endpoint, 
                COUNT(*) as record_count,
                MAX(timestamp) as latest_timestamp,
                MIN(timestamp) as earliest_timestamp
            FROM 
                hyblock_data
            GROUP BY 
                endpoint
            ORDER BY 
                record_count DESC
        """
        
        # Use the MCP query function
        df = execute_mcp_query(query)
    
        if df is not None and not df.empty:
            return df
        else:
            logger.error("No data returned from collection stats query")
            return None
    
    except Exception as e:
        logger.error(f"Error getting collection stats: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None

# Function to get endpoint coverage
def get_endpoint_coverage():
    """Get endpoint coverage statistics."""
    try:
        query = """
            SELECT 
                endpoint,
                COUNT(DISTINCT coin) as coin_count,
                COUNT(DISTINCT exchange) as exchange_count,
                COUNT(DISTINCT timeframe) as timeframe_count,
                COUNT(*) as record_count
            FROM 
                hyblock_data
            GROUP BY 
                endpoint
            ORDER BY 
                record_count DESC
        """
        
        return execute_mcp_query(query)
    except Exception as e:
        logger.error(f"Error getting endpoint coverage: {e}")
        return None

# Function to get exchange coverage
def get_exchange_coverage():
    """Get exchange coverage statistics."""
    try:
        query = """
            SELECT 
                exchange, 
                COUNT(DISTINCT endpoint) as endpoint_count,
                COUNT(DISTINCT coin) as coin_count,
                COUNT(DISTINCT timeframe) as timeframe_count,
                COUNT(*) as record_count
            FROM 
                hyblock_data
            GROUP BY 
                exchange
            ORDER BY 
                record_count DESC
        """
        
        return execute_mcp_query(query)
    except Exception as e:
        logger.error(f"Error getting exchange coverage: {e}")
        return None

# Function to get coin coverage
def get_coin_coverage():
    """Get coin coverage statistics."""
    try:
        query = """
            SELECT 
                coin, 
                COUNT(DISTINCT endpoint) as endpoint_count,
                COUNT(DISTINCT exchange) as exchange_count,
                COUNT(DISTINCT timeframe) as timeframe_count,
                COUNT(*) as record_count
            FROM 
                hyblock_data
            GROUP BY 
                coin
            ORDER BY 
                record_count DESC
        """
        
        return execute_mcp_query(query)
    except Exception as e:
        logger.error(f"Error getting coin coverage: {e}")
        return None

# Function to get timeframe coverage
def get_timeframe_coverage():
    """Get timeframe coverage statistics."""
    try:
        query = """
            SELECT 
                timeframe, 
                COUNT(DISTINCT endpoint) as endpoint_count,
                COUNT(DISTINCT exchange) as exchange_count,
                COUNT(DISTINCT coin) as coin_count,
                COUNT(*) as record_count
            FROM 
                hyblock_data
            GROUP BY 
                timeframe
            ORDER BY 
                record_count DESC
        """
        
        return execute_mcp_query(query)
    except Exception as e:
        logger.error(f"Error getting timeframe coverage: {e}")
        return None
    
# Function to get coverage analysis
def get_coverage_analysis():
    """Get coverage analysis across all dimensions."""
    try:
        query = """
        SELECT 
                endpoint, exchange, coin, timeframe,
                COUNT(*) as record_count,
                MAX(timestamp) as latest_timestamp,
                MIN(timestamp) as earliest_timestamp
        FROM 
            hyblock_data
        GROUP BY 
                endpoint, exchange, coin, timeframe
            ORDER BY 
                endpoint, exchange, coin, timeframe
        """
        
        return execute_mcp_query(query)
    except Exception as e:
        logger.error(f"Error getting coverage analysis: {e}")
        return None

# Function to get recent errors
def get_recent_errors():
    """Get recent errors from the database."""
    try:
        # Log file path (adjust this based on your actual log file location)
        log_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs", "data_collector.log")
        
        # Check if the file exists
        if not os.path.exists(log_file):
            return None
        
        # Read the last 1000 lines of the log file
        with open(log_file, "r") as f:
            lines = f.readlines()[-1000:]
        
        # Filter for error and warning lines
        error_lines = [line for line in lines if " ERROR " in line or " WARNING " in line]
        
        # Parse the error lines
        errors = []
        for line in error_lines:
            try:
                # Extract timestamp
                timestamp_str = line.split(" - ")[0]
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S,%f")
                
                # Extract level
                level = "ERROR" if " ERROR " in line else "WARNING"
                
                # Extract message
                message = line.split(" - ")[-1].strip()
                
                errors.append({
                    "timestamp": timestamp,
                    "level": level,
                    "message": message
                })
            except Exception:
                continue
        
        # Convert to DataFrame
        if errors:
            df = pd.DataFrame(errors)
            df = df.sort_values("timestamp", ascending=False)
            return df
        else:
            return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error getting recent errors: {e}")
        return None

# Function to display collection status
def display_collection_status():
    """Display the collection status page."""
    st.header("📊 Collection Status")
    st.markdown("Overview of data collection across different endpoints")
    
    # Get collection stats
    stats = get_collection_stats()
    
    if stats is not None and not stats.empty:
        # Ensure all required columns exist
        required_columns = ['endpoint', 'record_count', 'latest_timestamp', 'earliest_timestamp']
        missing_columns = [col for col in required_columns if col not in stats.columns]
        
        if missing_columns:
            st.error(f"Missing required columns in collection stats: {', '.join(missing_columns)}")
            return
        
        # Ensure timestamp columns are datetime objects
        for col in ['latest_timestamp', 'earliest_timestamp']:
            if col in stats.columns and not pd.api.types.is_datetime64_any_dtype(stats[col]):
                try:
                    stats[col] = pd.to_datetime(stats[col], errors='coerce')
                except:
                    st.error(f"Could not convert {col} to datetime")
                    return
        
        # Calculate overall statistics
        total_records = stats['record_count'].sum()
        latest_collection = stats['latest_timestamp'].max()
        earliest_collection = stats['earliest_timestamp'].min()
        
        # Display metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Records", f"{total_records:,}")
        with col2:
            try:
                latest_str = latest_collection.strftime("%Y-%m-%d %H:%M") if not pd.isna(latest_collection) else "N/A"
                st.metric("Latest Collection", latest_str)
            except:
                st.metric("Latest Collection", "Error formatting date")
        with col3:
            try:
                earliest_str = earliest_collection.strftime("%Y-%m-%d") if not pd.isna(earliest_collection) else "N/A"
                st.metric("Data Since", earliest_str)
            except:
                st.metric("Data Since", "Error formatting date")
        
        # Display the stats table
        st.subheader("Collection by Endpoint")
        
        # Safely format the timestamps for display
        try:
            stats['latest_timestamp_str'] = stats['latest_timestamp'].apply(
                lambda x: x.strftime("%Y-%m-%d %H:%M") if not pd.isna(x) else "N/A"
            )
            stats['earliest_timestamp_str'] = stats['earliest_timestamp'].apply(
                lambda x: x.strftime("%Y-%m-%d") if not pd.isna(x) else "N/A"
            )
        except Exception as e:
            logger.error(f"Error formatting timestamps: {e}")
            stats['latest_timestamp_str'] = "Error"
            stats['earliest_timestamp_str'] = "Error"
        
        # Calculate age in hours
        try:
            stats['age_hours'] = stats['latest_timestamp'].apply(
                lambda x: (pd.Timestamp.now() - x).total_seconds() / 3600 if not pd.isna(x) else float('inf')
            )
            stats['age_status'] = stats['age_hours'].apply(
                lambda x: "🟢 Recent" if x < 1 else "🟡 Stale" if x < 24 else "🔴 Old"
            )
        except Exception as e:
            logger.error(f"Error calculating age: {e}")
            stats['age_status'] = "⚠️ Unknown"
        
        # Format for display
        display_stats = stats[['endpoint', 'record_count', 'latest_timestamp_str', 'earliest_timestamp_str', 'age_status']]
        display_stats.columns = ['Endpoint', 'Records', 'Latest Update', 'Since', 'Status']
        
        st.dataframe(display_stats)
        
        # Create a chart of records by endpoint
        st.subheader("Records by Endpoint")
        fig = px.bar(stats, x='endpoint', y='record_count', title='Total Records by Endpoint')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("Failed to load collection statistics or no data available")

# Function to display endpoint coverage
def display_endpoint_coverage():
    """Display the endpoint coverage page."""
    st.header("🌐 Endpoint Coverage")
    st.markdown("Coverage of different endpoints across coins and exchanges")
    
    # Get endpoint coverage
    coverage = get_endpoint_coverage()
    
    if coverage is not None:
        st.dataframe(coverage)
    else:
        st.error("Failed to load endpoint coverage data")

# Function to display exchange coverage
def display_exchange_coverage():
    """Display the exchange coverage page."""
    st.header("🏛️ Exchange Coverage")
    st.markdown("Coverage of different exchanges across endpoints and coins")
        
    # Get exchange coverage
    coverage = get_exchange_coverage()
    
    if coverage is not None:
        st.dataframe(coverage)
    else:
        st.error("Failed to load exchange coverage data")

# Function to display coin coverage
def display_coin_coverage():
    """Display the coin coverage page."""
    st.header("🪙 Coin Coverage")
    st.markdown("Coverage of different coins across endpoints and exchanges")
        
    # Get coin coverage
    coverage = get_coin_coverage()
    
    if coverage is not None:
        st.dataframe(coverage)
    else:
        st.error("Failed to load coin coverage data")

# Function to display timeframe coverage
def display_timeframe_coverage():
    """Display the timeframe coverage page."""
    st.header("⏱️ Timeframe Coverage")
    st.markdown("Coverage of different timeframes across endpoints, coins, and exchanges")
        
    # Get timeframe coverage
    coverage = get_timeframe_coverage()
    
    if coverage is not None:
        st.dataframe(coverage)
    else:
        st.error("Failed to load timeframe coverage data")

# Function to display data quality
def display_data_quality():
    """Display the data quality page."""
    st.header("✅ Data Quality")
    st.markdown("Quality metrics for collected data")
    
    st.info("Data quality analysis is under development")

# Function to display recent errors
def display_recent_errors():
    """Display the recent errors page."""
    st.header("⚠️ Recent Errors")
    st.markdown("Recent errors and warnings from the collection process")
        
    # Get recent errors
    errors = get_recent_errors()
    
    if errors is not None and not errors.empty:
        st.dataframe(errors)
    else:
        st.success("No recent errors found")

# Main dashboard
def main():
    """Main function for the dashboard"""
    # Sidebar navigation
    st.sidebar.title("Hyblock Data Monitor")
    
    # Add navigation options
    pages = ["Collection Status", "Endpoint Coverage", "Exchange Coverage", "Coin Coverage", "Timeframe Coverage", "Data Quality", "Recent Errors"]
    page = st.sidebar.radio("Navigation", pages)
    
    # Add link to the main dashboard for collection recommendations
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Related Dashboards")
    st.sidebar.markdown("""
    For collection recommendations and gap analysis, visit:
    - [Hyblock Data Dashboard - Collector Recommendations](/)
    """)
    
    # Display the selected page
    if page == "Collection Status":
        display_collection_status()
    elif page == "Endpoint Coverage":
        display_endpoint_coverage()
    elif page == "Exchange Coverage":
        display_exchange_coverage()
    elif page == "Coin Coverage":
        display_coin_coverage()
    elif page == "Timeframe Coverage":
        display_timeframe_coverage()
    elif page == "Data Quality":
        display_data_quality()
    elif page == "Recent Errors":
        display_recent_errors()
    
    # Add footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("v1.0.0 - Hyblock Data Collection Monitor")

if __name__ == "__main__":
    main() 