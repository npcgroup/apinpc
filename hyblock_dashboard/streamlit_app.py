import os
import sys
import json
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.database import connect_to_database, execute_query, get_logger

# Set up logger
logger = get_logger("streamlit_dashboard")

# Page configuration
st.set_page_config(
    page_title="Hyblock Data Dashboard",
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
    .st-emotion-cache-16txtl3 h1 {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    .st-emotion-cache-16txtl3 h2 {
        padding-top: 0.5rem;
        padding-bottom: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)

# Title and description
st.title("Hyblock Data Dashboard")
st.markdown("Real-time monitoring of crypto data across multiple exchanges")

# Load endpoints from JSON file
@st.cache_data(persist="disk")
def load_endpoints_from_json():
    try:
        if not os.path.exists('endpoints_hyblock.json'):
            logger.warning("endpoints_hyblock.json file not found")
            return {}
        
        with open('endpoints_hyblock.json', 'r') as f:
            endpoints_data = json.load(f)
        
        # Process the data to extract endpoint information
        endpoints = {}
        for endpoint_name, endpoint_info in endpoints_data.items():
            if isinstance(endpoint_info, dict) and "parameters" in endpoint_info:
                params = endpoint_info["parameters"]
                required_params = []
                
                if "required" in params:
                    required_params = params["required"]
                
                endpoints[endpoint_name] = {
                    "description": endpoint_info.get("description", ""),
                    "required_params": required_params,
                    "parameters": params.get("properties", {})
                }
        
        return endpoints
    except Exception as e:
        logger.error(f"Error loading endpoints from JSON: {e}")
        return {}

# Function to load available endpoints from the database
@st.cache_data(persist="disk")
def load_endpoints():
    try:
        conn = connect_to_database()
        if not conn:
            logger.error("Failed to connect to database")
            return ["No endpoints available"]
        
        query = """
            SELECT DISTINCT endpoint
            FROM hyblock_data
            ORDER BY endpoint
        """
        
        results = execute_query(conn, query)
        conn.close()
        
        if not results:
            return ["No endpoints available"]
        
        endpoints = [result[0] for result in results]
        return endpoints
    except Exception as e:
        logger.error(f"Error loading endpoints: {e}")
        return ["No endpoints available"]

# Function to load available coins from the database
@st.cache_data(persist="disk")
def load_coins(endpoint=None):
    """
    Load available coins from the database, optionally filtered by endpoint
    
    Args:
        endpoint (str, optional): Filter coins that have data for this endpoint
        
    Returns:
        list: List of available coins
    """
    try:
        conn = connect_to_database()
        if not conn:
            logger.error("Failed to connect to database")
            return ["No coins available"]
        
        if endpoint:
            query = """
                SELECT DISTINCT coin
                FROM hyblock_data
                WHERE endpoint = %s
                ORDER BY coin
            """
            results = execute_query(conn, query, (endpoint,))
        else:
            query = """
                SELECT DISTINCT coin
                FROM hyblock_data
                ORDER BY coin
            """
            results = execute_query(conn, query)
            
        conn.close()
        
        if not results:
            return ["No coins available"]
        
        coins = [result[0] for result in results]
        return coins
    except Exception as e:
        logger.error(f"Error loading coins: {e}")
        return ["No coins available"]

# Function to load available filters based on endpoint and coin
@st.cache_data(persist="disk")
def load_filters(endpoint, coin):
    try:
        if not endpoint or not coin or endpoint == "No endpoints available" or coin == "No coins available":
            return ["No exchanges available"], ["No timeframes available"]
        
        conn = connect_to_database()
        if not conn:
            logger.error("Failed to connect to database")
            return ["No exchanges available"], ["No timeframes available"]
        
        # Get available exchanges
        exchange_query = """
            SELECT DISTINCT exchange
            FROM hyblock_data
            WHERE endpoint = %s AND coin = %s
            ORDER BY exchange
        """
        
        exchange_results = execute_query(conn, exchange_query, (endpoint, coin))
        
        # Get available timeframes
        timeframe_query = """
            SELECT DISTINCT timeframe
            FROM hyblock_data
            WHERE endpoint = %s AND coin = %s
            ORDER BY timeframe
        """
        
        timeframe_results = execute_query(conn, timeframe_query, (endpoint, coin))
        conn.close()
        
        if not exchange_results:
            exchanges = ["No exchanges available"]
        else:
            exchanges = [result[0] for result in exchange_results if result[0] is not None]
            if not exchanges:
                exchanges = ["No exchanges available"]
        
        if not timeframe_results:
            timeframes = ["No timeframes available"]
        else:
            timeframes = [result[0] for result in timeframe_results if result[0] is not None]
            if not timeframes:
                timeframes = ["No timeframes available"]
        
        return exchanges, timeframes
    except Exception as e:
        logger.error(f"Error loading filters: {e}")
        return ["No exchanges available"], ["No timeframes available"]

# Function to load market cap categories
@st.cache_data(persist="disk")
def load_market_cap_categories():
    return ["All", "large_cap", "mid_cap", "small_cap", "unknown"]

# Function to load data with market cap filtering
@st.cache_data(persist="disk")
def load_data(endpoint, coin, exchange, timeframe, time_range, market_cap_category=None):
    """Load data from the database based on selected filters"""
    try:
        # Calculate the start time based on the selected time range
        now = datetime.utcnow()
        if time_range == "Last Hour":
            start_time = now - timedelta(hours=1)
        elif time_range == "Last 6 Hours":
            start_time = now - timedelta(hours=6)
        elif time_range == "Last 24 Hours":
            start_time = now - timedelta(hours=24)
        elif time_range == "Last 7 Days":
            start_time = now - timedelta(days=7)
        else:  # 30d
            start_time = now - timedelta(days=30)
        
        conn = connect_to_database()
        if not conn:
            logger.error("Failed to connect to database")
            return None, "Failed to connect to the database"
        
        # Build the query
        query = """
            SELECT timestamp, data, market_cap_category
            FROM hyblock_data
            WHERE endpoint = %s AND coin = %s
        """
        
        # Convert parameters to strings to avoid type issues
        params = [str(endpoint), str(coin)]
        
        if exchange and exchange != "All":
            # Handle exchange parameter properly
            if isinstance(exchange, list):
                if len(exchange) == 1:
                    # Single exchange
                    query += " AND exchange = %s"
                    params.append(str(exchange[0]))
                elif len(exchange) > 1:
                    # Multiple exchanges - use IN clause
                    placeholders = ', '.join(['%s'] * len(exchange))
                    query += f" AND exchange IN ({placeholders})"
                    params.extend([str(ex) for ex in exchange])
            else:
                # Single exchange as string
                query += " AND exchange = %s"
                params.append(str(exchange))
        
        if timeframe and timeframe != "All":
            # Handle timeframe parameter properly
            if isinstance(timeframe, list):
                if len(timeframe) == 1:
                    # Single timeframe
                    query += " AND timeframe = %s"
                    params.append(str(timeframe[0]))
                elif len(timeframe) > 1:
                    # Multiple timeframes - use IN clause
                    placeholders = ', '.join(['%s'] * len(timeframe))
                    query += f" AND timeframe IN ({placeholders})"
                    params.extend([str(tf) for tf in timeframe])
            else:
                # Single timeframe as string
                query += " AND timeframe = %s"
                params.append(str(timeframe))
        
        if market_cap_category and market_cap_category != "All":
            # Handle market_cap_category parameter properly
            if isinstance(market_cap_category, list):
                if len(market_cap_category) == 1:
                    # Single category
                    query += " AND market_cap_category = %s"
                    params.append(str(market_cap_category[0]))
                elif len(market_cap_category) > 1:
                    # Multiple categories - use IN clause
                    placeholders = ', '.join(['%s'] * len(market_cap_category))
                    query += f" AND market_cap_category IN ({placeholders})"
                    params.extend([str(mc) for mc in market_cap_category])
            else:
                # Single category as string
                query += " AND market_cap_category = %s"
                params.append(str(market_cap_category))
        
        query += " AND timestamp >= %s ORDER BY timestamp"
        params.append(start_time)
        
        # Log the query and parameters for debugging
        logger.debug(f"Query: {query}")
        logger.debug(f"Parameters: {params}")
        
        results = execute_query(conn, query, params)
        conn.close()
        
        if not results:
            filter_msg = f"{coin}"
            if exchange and exchange != "All": 
                filter_msg += f" on {exchange}"
            if timeframe and timeframe != "All":
                filter_msg += f" with {timeframe} timeframe"
            return None, f"No data available for {filter_msg} with the selected filters."
        
        # Process the results
        data_points = []
        for row in results:
            timestamp, data_json, market_cap = row
            if data_json:
                try:
                    # Parse the JSON data
                    data_dict = json.loads(data_json) if isinstance(data_json, str) else data_json
                    
                    # Add timestamp and market cap category
                    data_dict["timestamp"] = timestamp
                    data_dict["market_cap_category"] = market_cap
                    
                    data_points.append(data_dict)
                except Exception as e:
                    logger.error(f"Error parsing JSON data: {e}")
        
        if not data_points:
            filter_msg = f"{coin}"
            if exchange and exchange != "All": 
                filter_msg += f" on {exchange}"
            if timeframe and timeframe != "All":
                filter_msg += f" with {timeframe} timeframe"
            return None, f"No valid data found for {filter_msg}. The data may be in an unexpected format."
            
        return data_points, None
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None, f"Error loading data: {str(e)}"

# Function to get all database tables
@st.cache_data(persist="disk")
def get_all_tables():
    try:
        conn = connect_to_database()
        if not conn:
            logger.error("Failed to connect to database")
            return []
        
        query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema='public' 
            AND table_type='BASE TABLE'
            ORDER BY table_name
        """
        
        results = execute_query(conn, query)
        conn.close()
        
        if not results:
            return []
        
        tables = [result[0] for result in results]
        return tables
    except Exception as e:
        logger.error(f"Error getting tables: {e}")
        return []

# Function to get table record count
@st.cache_data(persist="disk")
def get_table_count(table_name):
    try:
        conn = connect_to_database()
        if not conn:
            logger.error("Failed to connect to database")
            return 0
        
        query = f"SELECT COUNT(*) FROM {table_name}"
        
        results = execute_query(conn, query)
        conn.close()
        
        if not results:
            return 0
        
        return results[0][0]
    except Exception as e:
        logger.error(f"Error getting table count: {e}")
        return 0

# Function to get table data
@st.cache_data(persist="disk")
def get_table_data(table_name, limit=100):
    try:
        conn = connect_to_database()
        if not conn:
            logger.error("Failed to connect to database")
            return None
        
        query = f"""
            SELECT * FROM {table_name}
            ORDER BY timestamp DESC
            LIMIT {limit}
        """
        
        results = execute_query(conn, query)
        
        # Get column names
        column_query = f"""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = '{table_name}'
            ORDER BY ordinal_position
        """
        
        column_results = execute_query(conn, column_query)
        conn.close()
        
        if not results or not column_results:
            return None
        
        columns = [col[0] for col in column_results]
        df = pd.DataFrame(results, columns=columns)
        
        # Convert timestamp to datetime if it exists
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
        
        return df
    except Exception as e:
        logger.error(f"Error getting table data: {e}")
        return None

# Function to assess data quality
def assess_data_quality(data):
    """Assess the quality of the data and return a quality score and message."""
    if data is None or data.empty:
        return "low", "No data available"
    
    # Check for missing values
    missing_percentage = data.isnull().mean().mean() * 100
    
    # Check for data recency
    if 'timestamp' in data.columns:
        latest_timestamp = data['timestamp'].max()
        time_diff = datetime.now() - pd.to_datetime(latest_timestamp)
        hours_diff = time_diff.total_seconds() / 3600
    else:
        hours_diff = 24  # Default to 24 hours if no timestamp
    
    # Check data volume
    data_points = len(data)
    
    # Determine quality
    if missing_percentage < 5 and hours_diff < 1 and data_points >= 20:
        return "high", f"High quality: {data_points} recent data points with {missing_percentage:.1f}% missing values"
    elif missing_percentage < 15 and hours_diff < 6 and data_points >= 10:
        return "medium", f"Medium quality: {data_points} data points, {hours_diff:.1f} hours old, {missing_percentage:.1f}% missing values"
    else:
        return "low", f"Low quality: {data_points} data points, {hours_diff:.1f} hours old, {missing_percentage:.1f}% missing values"

# Custom metric display function
def custom_metric(label, value, delta=None, delta_color="normal"):
    """Display a custom styled metric with optional delta."""
    delta_html = ""
    if delta is not None:
        delta_color_class = "green" if delta_color == "normal" else "red" if delta_color == "inverse" else "normal"
        delta_icon = "↑" if (delta > 0 and delta_color == "normal") or (delta < 0 and delta_color == "inverse") else "↓"
        delta_html = f"""
        <div style="color: {'#00cc66' if delta_color_class == 'green' else '#ff3300'}; font-size: 16px; margin-top: 5px;">
            {delta_icon} {abs(delta):.2f}
        </div>
        """
    
    html = f"""
    <div class="metric-card">
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
        {delta_html}
    </div>
    """
    
    # Display the metric directly if no delta is provided
    if delta is None:
        st.markdown(html, unsafe_allow_html=True)
        return None
    else:
        return html

# Function to execute a query and return results as a DataFrame
@st.cache_data(persist="disk")
def execute_query_to_df(query, params=None):
    try:
        conn = connect_to_database()
        if not conn:
            logger.error("Failed to connect to database")
            return None
        
        # Ensure params are properly formatted
        if params and isinstance(params, list):
            # Convert any list parameters to strings to avoid SQL type issues
            processed_params = []
            for param in params:
                if isinstance(param, list):
                    # If param is a list, use the first item if available
                    if param:
                        processed_params.append(str(param[0]))
                    else:
                        processed_params.append(None)
                else:
                    processed_params.append(param)
            params = processed_params
        
        results = execute_query(conn, query, params)
        
        if not results:
            return None
        
        # Extract table name from the query
        table_name = None
        query_upper = query.upper()
        if "FROM" in query_upper:
            from_parts = query_upper.split("FROM")[1].strip().split()
            if from_parts:
                table_name = from_parts[0].strip()
                # Remove any schema prefix
                if "." in table_name:
                    table_name = table_name.split(".")[-1]
        
        if table_name:
            # Get column names
            column_query = f"""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = '{table_name}'
                ORDER BY ordinal_position
            """
            
            column_results = execute_query(conn, column_query)
            
            if column_results:
                columns = [col[0] for col in column_results]
                df = pd.DataFrame(results, columns=columns[:len(results[0])] if len(columns) > len(results[0]) else columns)
            else:
                # If we can't get column names, use generic column names
                df = pd.DataFrame(results, columns=[f"column_{i}" for i in range(len(results[0]))])
        else:
            # If we can't extract the table name, use generic column names
            df = pd.DataFrame(results, columns=[f"column_{i}" for i in range(len(results[0]))])
        
        conn.close()
        
        # Convert timestamp to datetime if it exists
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
        
        return df
    except Exception as e:
        logger.error(f"Error executing query to DataFrame: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None

@st.cache_data(persist="disk")
def execute_mcp_query(query, params=None):
    """
    Execute a SQL query using MCP and return results as a DataFrame.
    This provides a more direct and efficient way to query the database.
    
    Args:
        query (str): SQL query to execute
        params (list, optional): Parameters for the query
        
    Returns:
        pd.DataFrame: Query results as a DataFrame or None if error
    """
    try:
        import json
        # Log the query for debugging
        logger.info(f"Executing MCP query: {query}")
        
        # Try using direct database connection
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
        logger.error(f"Error executing MCP query: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None

# Function to get database schema information
@st.cache_data(persist="disk")
def get_database_schema():
    """
    Get database schema information including tables and their columns.
    
    Returns:
        dict: Dictionary of tables and their columns
    """
    try:
        # Get list of tables
        tables_query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """
        tables_df = execute_mcp_query(tables_query)
        
        if tables_df is None or tables_df.empty:
            return {}
        
        schema = {}
        for table_name in tables_df['table_name']:
            # Get columns for this table
            columns_query = f"""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = '{table_name}'
                ORDER BY ordinal_position
            """
            columns_df = execute_mcp_query(columns_query)
            
            if columns_df is not None and not columns_df.empty:
                schema[table_name] = columns_df.to_dict('records')
        
        return schema
    except Exception as e:
        logger.error(f"Error getting database schema: {e}")
        return {}

# Function to analyze data patterns and trends
def analyze_data_patterns(data, metric_column):
    """
    Analyze patterns and trends in the data for a specific metric.
    
    Args:
        data (pd.DataFrame): Data to analyze
        metric_column (str): Column name of the metric to analyze
        
    Returns:
        dict: Analysis results including trend, volatility, and patterns
    """
    if data is None or data.empty or metric_column not in data.columns:
        return {
            "trend": "unknown",
            "volatility": "unknown",
            "patterns": []
        }
    
    try:
        # Convert to numeric and handle errors
        values = pd.to_numeric(data[metric_column], errors='coerce')
        values = values.dropna()
        
        if len(values) < 3:
            return {
                "trend": "insufficient data",
                "volatility": "unknown", 
                "patterns": []
            }
        
        # Calculate basic statistics
        mean = values.mean()
        std = values.std()
        max_val = values.max()
        min_val = values.min()
        
        # Determine trend
        first_third = values[:len(values)//3].mean()
        last_third = values[2*len(values)//3:].mean()
        
        if last_third > first_third * 1.05:
            trend = "upward"
        elif last_third < first_third * 0.95:
            trend = "downward"
        else:
            trend = "sideways"
        
        # Determine volatility
        if std / abs(mean) if mean != 0 else 0 > 0.2:
            volatility = "high"
        elif std / abs(mean) if mean != 0 else 0 > 0.1:
            volatility = "medium"
        else:
            volatility = "low"
        
        # Look for patterns
        patterns = []
        
        # Check for consecutive increases/decreases
        consecutive_increases = 0
        consecutive_decreases = 0
        max_consecutive_increases = 0
        max_consecutive_decreases = 0
        
        for i in range(1, len(values)):
            if values.iloc[i] > values.iloc[i-1]:
                consecutive_increases += 1
                consecutive_decreases = 0
                max_consecutive_increases = max(max_consecutive_increases, consecutive_increases)
            elif values.iloc[i] < values.iloc[i-1]:
                consecutive_decreases += 1
                consecutive_increases = 0
                max_consecutive_decreases = max(max_consecutive_decreases, consecutive_decreases)
        
        if max_consecutive_increases >= 3:
            patterns.append(f"{max_consecutive_increases} consecutive increases")
        
        if max_consecutive_decreases >= 3:
            patterns.append(f"{max_consecutive_decreases} consecutive decreases")
        
        # Check for extreme values
        if max_val > mean + 2*std:
            patterns.append("extreme high values detected")
        
        if min_val < mean - 2*std:
            patterns.append("extreme low values detected")
        
        return {
            "trend": trend,
            "volatility": volatility,
            "patterns": patterns,
            "statistics": {
                "mean": mean,
                "std": std,
                "max": max_val,
                "min": min_val
            }
        }
        
    except Exception as e:
        logger.error(f"Error analyzing data patterns: {e}")
        return {
            "trend": "error",
            "volatility": "unknown",
            "patterns": [],
            "error": str(e)
        }

# Add a new section to the streamlit app for advanced database exploration
def add_database_explorer_section():
    """Add an advanced database explorer section to the Streamlit app"""
    st.header("🔍 Advanced Database Explorer")
    st.markdown("Explore the database with custom SQL queries and advanced analysis")
    
    # Get database schema
    schema = get_database_schema()
    
    if not schema:
        st.warning("Unable to retrieve database schema. Please check the connection.")
        return
    
    # Create tabs for different exploration options
    tab1, tab2, tab3 = st.tabs(["SQL Explorer", "Data Analysis", "Schema Overview"])
    
    with tab1:
        st.subheader("SQL Query Explorer")
        
        # Provide some example queries
        example_queries = {
            "List all endpoints": "SELECT DISTINCT endpoint FROM hyblock_data ORDER BY endpoint",
            "Get latest data for BTC": "SELECT * FROM hyblock_data WHERE coin = 'BTC' ORDER BY timestamp DESC LIMIT 10",
            "Compare exchanges for ETH": "SELECT exchange, COUNT(*) as data_count FROM hyblock_data WHERE coin = 'ETH' GROUP BY exchange ORDER BY data_count DESC",
            "Market cap distribution": "SELECT category, COUNT(*) as coin_count FROM market_cap_categories GROUP BY category ORDER BY coin_count DESC"
        }
        
        selected_example = st.selectbox("Example Queries", options=list(example_queries.keys()))
        
        # Display the example query
        query = st.text_area("SQL Query", value=example_queries[selected_example], height=150)
        
        if st.button("Execute Query"):
            with st.spinner("Executing query..."):
                result_df = execute_mcp_query(query)
                
                if result_df is not None and not result_df.empty:
                    st.success(f"Query returned {len(result_df)} rows")
                    st.dataframe(result_df, use_container_width=True)
                    
                    # Add option to download results
                    st.download_button(
                        label="Download results as CSV",
                        data=result_df.to_csv(index=False).encode('utf-8'),
                        file_name="query_results.csv",
                        mime="text/csv"
                    )
                    
                    # If the query includes timestamp, offer to plot the data
                    if 'timestamp' in result_df.columns:
                        st.subheader("Temporal Analysis")
                        
                        # Get numeric columns for plotting
                        numeric_cols = result_df.select_dtypes(include=['number']).columns.tolist()
                        
                        if numeric_cols:
                            selected_column = st.selectbox("Select column to plot over time", options=numeric_cols)
                            
                            # Plot the selected column over time
                            fig = px.line(result_df, x='timestamp', y=selected_column, title=f'{selected_column} over time')
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Add data pattern analysis
                            st.subheader("Pattern Analysis")
                            analysis = analyze_data_patterns(result_df, selected_column)
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Trend", analysis["trend"].capitalize())
                            with col2:
                                st.metric("Volatility", analysis["volatility"].capitalize())
                            with col3:
                                st.metric("Data Points", len(result_df))
                            
                            if analysis["patterns"]:
                                st.markdown("**Detected Patterns:**")
                                for pattern in analysis["patterns"]:
                                    st.markdown(f"- {pattern.capitalize()}")
                    else:
                        # If there's only one numeric column, just plot it
                        fig = px.line(result_df, x='timestamp', y=numeric_cols[0], 
                                     title=f"{numeric_cols[0]} over time")
                        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("Data Analysis Tools")
        
        # Select a table to analyze
        table_name = st.selectbox("Select Table", options=list(schema.keys()))
        
        if table_name:
            # Get columns for the selected table
            columns = [col['column_name'] for col in schema[table_name]]
            
            # Select column for filtering
            filter_col = st.selectbox("Filter by Column", options=columns)
            
            # Get unique values for the filter column
            filter_query = f"SELECT DISTINCT {filter_col} FROM {table_name} LIMIT 50"
            filter_values_df = execute_mcp_query(filter_query)
            
            if filter_values_df is not None and not filter_values_df.empty:
                filter_values = filter_values_df[filter_col].tolist()
                selected_filter = st.selectbox(f"Select {filter_col}", options=filter_values)
                
                # Get data based on the filter
                data_query = f"SELECT * FROM {table_name} WHERE {filter_col} = '{selected_filter}' ORDER BY timestamp DESC LIMIT 1000"
                data_df = execute_mcp_query(data_query)
                
                if data_df is not None and not data_df.empty:
                    st.success(f"Found {len(data_df)} rows for {filter_col} = {selected_filter}")
                    
                    # Show a sample of the data
                    st.subheader("Data Sample")
                    st.dataframe(data_df.head(10), use_container_width=True)
                    
                    # Analyze the data
                    st.subheader("Data Analysis")
                    
                    # Expand JSON data if present
                    if 'data' in data_df.columns and data_df['data'].dtype == 'object':
                        try:
                            # Check if first row has a 'data' field
                            if isinstance(data_df['data'].iloc[0], dict) and 'data' in data_df['data'].iloc[0]:
                                # Extract nested data
                                expanded_data = pd.json_normalize(data_df['data'].iloc[0], record_path='data')
                                
                                if not expanded_data.empty:
                                    st.subheader("Expanded Data")
                                    st.dataframe(expanded_data.head(10), use_container_width=True)
                                    
                                    # Plot the data if it has numeric columns
                                    numeric_cols = expanded_data.select_dtypes(include=['number']).columns.tolist()
                                    if numeric_cols and 'timestamp' in expanded_data.columns or 'openDate' in expanded_data.columns:
                                        time_col = 'timestamp' if 'timestamp' in expanded_data.columns else 'openDate'
                                        selected_metric = st.selectbox("Select metric to analyze", options=numeric_cols)
                                        
                                        # Create the plot
                                        fig = px.line(expanded_data, x=time_col, y=selected_metric, title=f'{selected_metric} over time')
                                        st.plotly_chart(fig, use_container_width=True)
                                        
                                        # Add statistics
                                        st.subheader("Statistical Analysis")
                                        stats = expanded_data[selected_metric].describe()
                                        st.dataframe(stats)
                                        
                                        # Add pattern analysis
                                        analysis = analyze_data_patterns(expanded_data, selected_metric)
                                        
                                        col1, col2, col3 = st.columns(3)
                                        with col1:
                                            st.metric("Trend", analysis["trend"].capitalize())
                                        with col2:
                                            st.metric("Volatility", analysis["volatility"].capitalize())
                                        with col3:
                                            st.metric("Data Points", len(expanded_data))
                                        
                                        if analysis["patterns"]:
                                            st.markdown("**Detected Patterns:**")
                                            for pattern in analysis["patterns"]:
                                                st.markdown(f"- {pattern.capitalize()}")
                        except Exception as e:
                            st.error(f"Error processing JSON data: {e}")
                else:
                    st.warning(f"No data found for {filter_col} = {selected_filter}")
            else:
                st.warning(f"Could not retrieve filter values for {filter_col}")
    
    with tab3:
        st.subheader("Database Schema Overview")
        
        # Display tables and their columns
        for table_name, columns in schema.items():
            with st.expander(f"Table: {table_name}"):
                columns_df = pd.DataFrame(columns)
                st.dataframe(columns_df, use_container_width=True)
                
                # Show sample data
                st.markdown("**Sample Data:**")
                sample_query = f"SELECT * FROM {table_name} LIMIT 5"
                sample_df = execute_mcp_query(sample_query)
                
                if sample_df is not None and not sample_df.empty:
                    st.dataframe(sample_df, use_container_width=True)
                else:
                    st.info("No data available in this table")
                
                # Show row count
                count_query = f"SELECT COUNT(*) as count FROM {table_name}"
                count_df = execute_mcp_query(count_query)
                
                if count_df is not None and not count_df.empty:
                    count = count_df['count'].iloc[0]
                    st.metric("Row Count", count)

# Function to display the main dashboard
def display_dashboard():
    """Display the main dashboard with key metrics and charts"""
    
    # Sidebar filters for the dashboard
    st.sidebar.header("Data Filters")
    
    # Endpoint selection
    endpoints = load_endpoints()
    endpoint = st.sidebar.selectbox(
        "Select Endpoint",
        options=endpoints,
        index=0 if endpoints else None,
    )
    
    # Coin selection - filtered by selected endpoint
    coins = load_coins(endpoint)
    
    if not coins or coins == ["No coins available"]:
        st.warning(f"No coins available for the selected endpoint: {endpoint}")
        return
        
    coin = st.sidebar.selectbox(
        "Select Coin",
        options=coins,
        index=0 if coins and "BTC" in coins else 0,
    )
    
    # Exchange selection
    exchanges, available_timeframes = load_filters(endpoint, coin)
    
    if exchanges == ["No exchanges available"]:
        st.warning(f"No exchanges available for {coin} with the selected endpoint: {endpoint}")
        return
        
    exchange = st.sidebar.selectbox(
        "Select Exchange",
        options=exchanges,
        index=0 if exchanges and "binance" in exchanges else 0,
    )
    
    # Timeframe selection - use available timeframes if possible
    if available_timeframes and available_timeframes != ["No timeframes available"]:
        timeframe_options = available_timeframes
    else:
        timeframe_options = ["1m", "5m", "15m", "1h", "4h", "1d"]
        
    timeframe = st.sidebar.selectbox(
        "Select Timeframe",
        options=timeframe_options,
        index=min(3, len(timeframe_options)-1),  # Default to 1h or the last option
    )
    
    # Time range selection
    time_range = st.sidebar.selectbox(
        "Select Time Range",
        options=["Last 24 Hours", "Last 7 Days", "Last 30 Days", "All Time"],
        index=0,
    )
    
    # Market cap category selection
    market_cap_categories = load_market_cap_categories()
    market_cap_category = st.sidebar.selectbox(
        "Market Cap Category",
        options=["All"] + market_cap_categories,
        index=0,
    )
    
    # Auto-refresh option
    st.sidebar.header("🔄 Auto Refresh")
    auto_refresh = st.sidebar.checkbox("Enable Auto Refresh", value=False)
    refresh_interval = 60
    
    if auto_refresh:
        refresh_interval = st.sidebar.slider(
            "Refresh Interval (seconds)",
            min_value=5,
            max_value=300,
            value=60
        )

    # Load data with MCP
    if market_cap_category == "All":
        market_cap_category = None
    
    # Use direct MCP query to load data
    query = f"""
        SELECT *
        FROM hyblock_data
        WHERE endpoint = '{endpoint}'
          AND coin = '{coin}'
          AND exchange = '{exchange}'
          AND timeframe = '{timeframe}'
        ORDER BY timestamp DESC
        LIMIT 1
    """
    
    latest_data = execute_mcp_query(query)
    
    # Display the data
    if latest_data is not None and not latest_data.empty:
        st.subheader(f"{coin} Data ({endpoint})")
        
        # Extract the JSON data from the data column
        if 'data' in latest_data.columns and isinstance(latest_data['data'].iloc[0], dict):
            data_json = latest_data['data'].iloc[0]
            
            # Check if it has 'data' key (nested structure)
            if 'data' in data_json and isinstance(data_json['data'], list):
                nested_data = data_json['data']
                
                # Convert nested data to dataframe
                nested_df = pd.DataFrame(nested_data)
                
                # Display the data
                st.subheader("Data Visualization")
                
                # Show a sample of the data
                with st.expander("Raw Data Sample"):
                    st.dataframe(nested_df.head(10), use_container_width=True)
                
                # Create visualizations based on the data
                if 'timestamp' in nested_df.columns or 'openDate' in nested_df.columns:
                    time_col = 'timestamp' if 'timestamp' in nested_df.columns else 'openDate'
                    
                    # Get numeric columns for plotting
                    numeric_cols = nested_df.select_dtypes(include=['number']).columns.tolist()
                    
                    if numeric_cols:
                        # If there are multiple numeric columns, create a dropdown to select which to plot
                        if len(numeric_cols) > 1:
                            selected_column = st.selectbox("Select Metric to Display", options=numeric_cols)
                            
                            # Plot the selected column
                            fig = px.line(nested_df, x=time_col, y=selected_column, 
                                         title=f"{selected_column} for {coin} on {exchange} ({timeframe})")
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Data analysis
                            analysis = analyze_data_patterns(nested_df, selected_column)
                            
                            # Display metrics
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Trend", analysis["trend"].capitalize())
                            with col2:
                                st.metric("Volatility", analysis["volatility"].capitalize())
                            with col3:
                                st.metric("Data Points", len(nested_df))
                            
                            if analysis["patterns"]:
                                st.subheader("Detected Patterns")
                                for pattern in analysis["patterns"]:
                                    st.markdown(f"- {pattern.capitalize()}")
                        else:
                            # If there's only one numeric column, just plot it
                            fig = px.line(nested_df, x=time_col, y=numeric_cols[0], 
                                         title=f"{numeric_cols[0]} for {coin} on {exchange} ({timeframe})")
                            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Data is not in the expected format.")
    else:
        st.warning(f"No data available for {coin} with the selected filters.")
    
    # Handle auto-refresh
    if auto_refresh:
        # Display last refresh time
        st.sidebar.markdown(f"**Last refreshed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        time.sleep(refresh_interval)
        st.experimental_rerun()

# Function to display the data explorer
def display_data_explorer():
    """Display the data explorer interface"""
    st.header("🔍 Data Explorer")
    st.markdown("Explore data across different endpoints, coins, and exchanges")
    
    # Create tabs for different exploration modes
    tab1, tab2 = st.tabs(["Single View", "Comparison View"])
    
    with tab1:
        # Endpoint selection
        endpoints = load_endpoints()
        endpoint = st.selectbox(
            "Select Endpoint",
            options=endpoints,
            index=0 if endpoints else None,
        )
        
        # Coin selection - filtered by selected endpoint
        coins = load_coins(endpoint)
        
        if not coins or coins == ["No coins available"]:
            st.warning(f"No coins available for the selected endpoint: {endpoint}")
            return
            
        coin = st.selectbox(
            "Select Coin",
            options=coins,
            index=0 if coins and "BTC" in coins else 0,
        )
        
        # Exchange selection
        exchanges, available_timeframes = load_filters(endpoint, coin)
        
        if exchanges == ["No exchanges available"]:
            st.warning(f"No exchanges available for {coin} with the selected endpoint: {endpoint}")
            return
            
        exchange = st.selectbox(
            "Select Exchange",
            options=exchanges,
            index=0 if exchanges and "binance" in exchanges else 0,
        )
        
        # Timeframe selection - use available timeframes if possible
        if available_timeframes and available_timeframes != ["No timeframes available"]:
            timeframe_options = available_timeframes
        else:
            timeframe_options = ["1m", "5m", "15m", "1h", "4h", "1d"]
            
        timeframe = st.selectbox(
            "Select Timeframe",
            options=timeframe_options,
            index=min(3, len(timeframe_options)-1),  # Default to 1h or the last option
        )
        
        # Time range selection
        time_range = st.selectbox(
            "Select Time Range",
            options=["Last 24 Hours", "Last 7 Days", "Last 30 Days", "All Time"],
            index=0,
        )
        
        if st.button("Load Data"):
            # Use MCP to query data
            time_filter = ""
            if time_range == "Last 24 Hours":
                time_filter = "AND timestamp > NOW() - INTERVAL '1 day'"
            elif time_range == "Last 7 Days":
                time_filter = "AND timestamp > NOW() - INTERVAL '7 days'"
            elif time_range == "Last 30 Days":
                time_filter = "AND timestamp > NOW() - INTERVAL '30 days'"
            
            query = f"""
                SELECT *
                FROM hyblock_data
                WHERE endpoint = '{endpoint}'
                  AND coin = '{coin}'
                  AND exchange = '{exchange}'
                  AND timeframe = '{timeframe}'
                  {time_filter}
                ORDER BY timestamp DESC
                LIMIT 1000
            """
            
            with st.spinner("Loading data..."):
                df = execute_mcp_query(query)
                
                if df is not None and not df.empty:
                    st.success(f"Loaded {len(df)} records")
                    
                    # Display data overview
                    st.subheader("Data Overview")
                    st.dataframe(df.head(10), use_container_width=True)
                    
                    # Extract nested data if available
                    if 'data' in df.columns and isinstance(df['data'].iloc[0], dict) and 'data' in df['data'].iloc[0]:
                        nested_data = df['data'].iloc[0]['data']
                        nested_df = pd.DataFrame(nested_data)
                        
                        st.subheader("Detailed Data")
                        st.dataframe(nested_df.head(20), use_container_width=True)
                        
                        # Create visualizations
                        if len(nested_df) > 1:
                            st.subheader("Data Visualization")
                            
                            # Get time column and numeric columns
                            time_col = None
                            if 'timestamp' in nested_df.columns:
                                time_col = 'timestamp'
                            elif 'openDate' in nested_df.columns:
                                time_col = 'openDate'
                            
                            if time_col:
                                numeric_cols = nested_df.select_dtypes(include=['number']).columns.tolist()
                                
                                if numeric_cols:
                                    selected_column = st.selectbox("Select Metric", options=numeric_cols)
                                    
                                    # Plot the selected column
                                    fig = px.line(nested_df, x=time_col, y=selected_column, 
                                                title=f"{selected_column} for {coin} on {exchange} ({timeframe})")
                                    st.plotly_chart(fig, use_container_width=True)
                                    
                                    # Basic statistics
                                    st.subheader("Statistics")
                                    stats = nested_df[selected_column].describe()
                                    st.dataframe(stats, use_container_width=True)
                                    
                                    # Data analysis
                                    analysis = analyze_data_patterns(nested_df, selected_column)
                                    
                                    # Display metrics
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        st.metric("Trend", analysis["trend"].capitalize())
                                    with col2:
                                        st.metric("Volatility", analysis["volatility"].capitalize())
                                    with col3:
                                        st.metric("Data Points", len(nested_df))
                                    
                                    # Download option
                                    st.download_button(
                                        label="Download data as CSV",
                                        data=nested_df.to_csv(index=False).encode('utf-8'),
                                        file_name=f"{coin}_{endpoint}_{exchange}_{timeframe}.csv",
                                        mime="text/csv"
                                    )
                    else:
                        st.warning("No detailed data available in the expected format.")
                else:
                    st.warning("No data found with the selected filters.")
    
    with tab2:
        st.subheader("Data Comparison")
        
        # Select comparison type
        comparison_type = st.radio(
            "Compare by",
            options=["Exchanges", "Coins", "Timeframes"],
            horizontal=True
        )
        
        # Endpoint selection
        endpoints = load_endpoints()
        endpoint = st.selectbox(
            "Select Endpoint",
            options=endpoints,
            index=0 if endpoints else None,
            key="comparison_endpoint"
        )
        
        # Check if endpoints are available
        if not endpoints or endpoints == ["No endpoints available"]:
            st.warning("No endpoints available. Please check data collection.")
            return
            
        # Load all available coins for this endpoint
        all_coins = load_coins(endpoint)
        
        if not all_coins or all_coins == ["No coins available"]:
            st.warning(f"No coins available for the selected endpoint: {endpoint}")
            return
            
        if comparison_type == "Exchanges":
            # Compare across exchanges
            coin = st.selectbox(
                "Select Coin",
                options=all_coins,
                index=0 if all_coins and "BTC" in all_coins else 0,
                key="comparison_coin"
            )
            
            # Get all available exchanges for this coin and endpoint
            exchanges, available_timeframes = load_filters(endpoint, coin)
            
            if exchanges == ["No exchanges available"]:
                st.warning(f"No exchanges available for {coin} with the selected endpoint.")
                return
                
            # Timeframe selection - use available timeframes if possible
            if available_timeframes and available_timeframes != ["No timeframes available"]:
                timeframe_options = available_timeframes
            else:
                timeframe_options = ["1m", "5m", "15m", "1h", "4h", "1d"]
                
            timeframe = st.selectbox(
                "Select Timeframe",
                options=timeframe_options,
                index=min(3, len(timeframe_options)-1),  # Default to 1h or the last option
                key="comparison_timeframe"
            )
            
            # Select multiple exchanges
            selected_exchanges = st.multiselect(
                "Select Exchanges to Compare",
                options=exchanges,
                default=[exchanges[0]] if exchanges and exchanges[0] != "No exchanges available" else []
            )
            
            if st.button("Compare Data"):
                if selected_exchanges:
                    # Show spinner while loading data
                    with st.spinner("Loading comparison data..."):
                        comparison_data = {}
                        
                        for ex in selected_exchanges:
                            query = f"""
                                SELECT *
                                FROM hyblock_data
                                WHERE endpoint = '{endpoint}'
                                  AND coin = '{coin}'
                                  AND exchange = '{ex}'
                                  AND timeframe = '{timeframe}'
                ORDER BY timestamp DESC
                                LIMIT 1
                            """
                            
                            df = execute_mcp_query(query)
                            
                            if df is not None and not df.empty and 'data' in df.columns:
                                # Extract nested data
                                if isinstance(df['data'].iloc[0], dict) and 'data' in df['data'].iloc[0]:
                                    nested_data = df['data'].iloc[0]['data']
                                    nested_df = pd.DataFrame(nested_data)
                                    comparison_data[ex] = nested_df
                        
                        if comparison_data:
                            # Find common metrics across all exchanges
                            common_metrics = set()
                            for ex, df in comparison_data.items():
                                numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                                if not common_metrics:
                                    common_metrics = set(numeric_cols)
                                else:
                                    common_metrics = common_metrics.intersection(set(numeric_cols))
                            
                            if common_metrics:
                                selected_metric = st.selectbox("Select Metric to Compare", options=list(common_metrics))
                                
                                # Create comparison chart
                                fig = go.Figure()
                                
                                for ex, df in comparison_data.items():
                                    time_col = 'timestamp' if 'timestamp' in df.columns else 'openDate'
                                    fig.add_trace(go.Scatter(
                                        x=df[time_col],
                                        y=df[selected_metric],
                                        mode='lines',
                                        name=ex
                                    ))
                                
                                fig.update_layout(
                                    title=f"{selected_metric} for {coin} across exchanges",
                                    xaxis_title="Time",
                                    yaxis_title=selected_metric,
                                    legend_title="Exchange"
                                )
                                
                                st.plotly_chart(fig, use_container_width=True)
                                
                                # Summary statistics
                                stats = {}
                                for ex, df in comparison_data.items():
                                    stats[ex] = {
                                        "Mean": df[selected_metric].mean(),
                                        "Min": df[selected_metric].min(),
                                        "Max": df[selected_metric].max(),
                                        "Std Dev": df[selected_metric].std()
                                    }
                                
                                st.subheader("Summary Statistics")
                                st.dataframe(pd.DataFrame(stats), use_container_width=True)
                            else:
                                st.warning("No common metrics found across the selected exchanges.")
                        else:
                            st.warning("Please select at least one exchange for comparison.")
        
        elif comparison_type == "Coins":
            # Compare across coins
            # Get available exchanges for the first available coin as a starting point
            first_coin = all_coins[0]
            exchanges, available_timeframes = load_filters(endpoint, first_coin)
            
            if exchanges == ["No exchanges available"]:
                st.warning(f"No exchanges available for {first_coin} with the selected endpoint.")
                return
                
            exchange = st.selectbox(
                "Select Exchange",
                options=exchanges,
                index=0 if exchanges and "binance" in exchanges else 0,
                key="comparison_exchange"
            )
            
            # Timeframe selection - use available timeframes if possible
            if available_timeframes and available_timeframes != ["No timeframes available"]:
                timeframe_options = available_timeframes
            else:
                timeframe_options = ["1m", "5m", "15m", "1h", "4h", "1d"]
                
            timeframe = st.selectbox(
                "Select Timeframe",
                options=timeframe_options,
                index=min(3, len(timeframe_options)-1),  # Default to 1h or the last option
                key="comparison_timeframe_coins"
            )
            
            # Select multiple coins
            default_coin = all_coins[0] if all_coins and all_coins[0] != "No coins available" else None
            selected_coins = st.multiselect(
                "Select Coins to Compare",
                options=all_coins,
                default=[default_coin] if default_coin else []
            )
            
            if st.button("Compare Coins"):
                if selected_coins:
                    # Show spinner while loading data
                    with st.spinner("Loading comparison data..."):
                        comparison_data = {}
                        
                        for coin in selected_coins:
                            query = f"""
                                SELECT *
                                FROM hyblock_data
                                WHERE endpoint = '{endpoint}'
                                  AND coin = '{coin}'
                                  AND exchange = '{exchange}'
                                  AND timeframe = '{timeframe}'
                ORDER BY timestamp DESC
                                LIMIT 1
                            """
                            
                            df = execute_mcp_query(query)
                            
                            if df is not None and not df.empty and 'data' in df.columns:
                                # Extract nested data
                                if isinstance(df['data'].iloc[0], dict) and 'data' in df['data'].iloc[0]:
                                    nested_data = df['data'].iloc[0]['data']
                                    nested_df = pd.DataFrame(nested_data)
                                    comparison_data[coin] = nested_df
                        
                        if comparison_data:
                            # Find common metrics across all coins
                            common_metrics = set()
                            for coin, df in comparison_data.items():
                                numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                                if not common_metrics:
                                    common_metrics = set(numeric_cols)
                                else:
                                    common_metrics = common_metrics.intersection(set(numeric_cols))
                            
                            if common_metrics:
                                selected_metric = st.selectbox("Select Metric to Compare", options=list(common_metrics))
                                
                                # Create comparison chart
                                fig = go.Figure()
                                
                                for coin, df in comparison_data.items():
                                    time_col = 'timestamp' if 'timestamp' in df.columns else 'openDate'
                                    fig.add_trace(go.Scatter(
                                        x=df[time_col],
                                        y=df[selected_metric],
                                        mode='lines',
                                        name=coin
                                    ))
                                
                                fig.update_layout(
                                    title=f"{selected_metric} across coins on {exchange}",
                                    xaxis_title="Time",
                                    yaxis_title=selected_metric,
                                    legend_title="Coin"
                                )
                                
                                st.plotly_chart(fig, use_container_width=True)
                            elif not common_metrics:
                                st.warning("No common metrics found across the selected coins.")
                            elif not comparison_data:
                                st.warning("No data available for comparison.")
                            else:
                                st.warning("Please select at least one coin for comparison.")
        
        else:  # Timeframes
            # Compare across timeframes
            coin = st.selectbox(
                "Select Coin",
                options=all_coins,
                index=0 if all_coins and "BTC" in all_coins else 0,
                key="comparison_coin_timeframes"
            )
            
            # Get available exchanges for this coin
            exchanges, _ = load_filters(endpoint, coin)
            
            if exchanges == ["No exchanges available"]:
                st.warning(f"No exchanges available for {coin} with the selected endpoint.")
                return
                
            exchange = st.selectbox(
                "Select Exchange",
                options=exchanges,
                index=0 if exchanges and "binance" in exchanges else 0,
                key="comparison_exchange_timeframes"
            )
            
            # Select multiple timeframes
            selected_timeframes = st.multiselect(
                "Select Timeframes to Compare",
                options=["1m", "5m", "15m", "1h", "4h", "1d"],
                default=["1h"]
            )
            
            if st.button("Compare Timeframes"):
                if selected_timeframes:
                    # Show spinner while loading data
                    with st.spinner("Loading comparison data..."):
                        comparison_data = {}
                        
                        for tf in selected_timeframes:
                            query = f"""
                                SELECT *
                                FROM hyblock_data
                                WHERE endpoint = '{endpoint}'
                                  AND coin = '{coin}'
                                  AND exchange = '{exchange}'
                                  AND timeframe = '{tf}'
                ORDER BY timestamp DESC
                                LIMIT 1
                            """
                            
                            df = execute_mcp_query(query)
                            
                            if df is not None and not df.empty and 'data' in df.columns:
                                # Extract nested data
                                if isinstance(df['data'].iloc[0], dict) and 'data' in df['data'].iloc[0]:
                                    nested_data = df['data'].iloc[0]['data']
                                    nested_df = pd.DataFrame(nested_data)
                                    comparison_data[tf] = nested_df
                        
                        if comparison_data:
                            # Find common metrics across all timeframes
                            common_metrics = set()
                            for tf, df in comparison_data.items():
                                numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                                if not common_metrics:
                                    common_metrics = set(numeric_cols)
                                else:
                                    common_metrics = common_metrics.intersection(set(numeric_cols))
                            
                            if common_metrics:
                                selected_metric = st.selectbox("Select Metric to Compare", options=list(common_metrics))
                                
                                # Create comparison chart
                                fig = go.Figure()
                                
                                for tf, df in comparison_data.items():
                                    time_col = 'timestamp' if 'timestamp' in df.columns else 'openDate'
                                    fig.add_trace(go.Scatter(
                                        x=df[time_col],
                                        y=df[selected_metric],
                                        mode='lines',
                                        name=tf
                                    ))
                                
                                fig.update_layout(
                                    title=f"{selected_metric} for {coin} on {exchange} across timeframes",
                                    xaxis_title="Time",
                                    yaxis_title=selected_metric,
                                    legend_title="Timeframe"
                                )
                                
                                st.plotly_chart(fig, use_container_width=True)
                            elif not common_metrics:
                                st.warning("No common metrics found across the selected timeframes.")
                            elif not comparison_data:
                                st.warning("No data available for comparison.")
                            else:
                                st.warning("Please select at least one timeframe for comparison.")

# Function to display the database status
def display_database_status():
    """Display database status information"""
    st.header("💾 Database Status")
    st.markdown("Overview of database tables and their status")
    
    # Get all tables
    tables = get_all_tables()
    
    if not tables:
        st.warning("No tables found in the database.")
    else:
        # Create a table with counts
        table_counts = []
        for table in tables:
            count = get_table_count(table)
            table_counts.append({"Table": table, "Record Count": count})
        
        count_df = pd.DataFrame(table_counts)
        
        # Display the table counts
        st.subheader("Database Tables")
        st.dataframe(count_df, use_container_width=True)
        
        # Create a bar chart of record counts
        fig = px.bar(count_df, x='Table', y='Record Count', title='Records per Table')
        st.plotly_chart(fig, use_container_width=True)
        
        # Select a table to view
        selected_table = st.selectbox("Select a table to view", tables)
        
        # Get the data for the selected table
        row_limit = st.slider("Number of rows to display", 10, 1000, 100)
        table_data = get_table_data(selected_table, limit=row_limit)
        
        if table_data is not None:
            st.subheader(f"Data from {selected_table}")
            st.dataframe(table_data, use_container_width=True)
            
            # Download button
            csv = table_data.to_csv(index=False)
            st.download_button(
                label="Download data as CSV",
                data=csv,
                file_name=f"{selected_table}.csv",
                mime="text/csv"
            )
            
            # Add visualization if possible
            if len(table_data) > 0 and "timestamp" in table_data.columns:
                numeric_columns = table_data.select_dtypes(include=['number']).columns.tolist()
                if numeric_columns:
                    st.subheader("Data Visualization")
                    chart_col = st.selectbox("Select column to visualize", numeric_columns)
                    
                    fig = px.line(
                        table_data.sort_values("timestamp"), 
                        x="timestamp", 
                        y=chart_col,
                        title=f"{chart_col} over time"
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning(f"No data available in the {selected_table} table.")

# Function to display API usage
def display_api_usage():
    """Display API usage statistics"""
    st.header("📈 API Usage")
    st.markdown("Monitor API usage and performance")
    
    # Query API usage data
    query = """
        SELECT * FROM api_usage
        ORDER BY timestamp DESC
        LIMIT 1000
    """
    
    api_data = execute_mcp_query(query)
    
    if api_data is not None and not api_data.empty:
        # Show overall stats
        st.subheader("API Usage Overview")
        
        # Count requests by status
        if 'status' in api_data.columns:
            status_counts = api_data['status'].value_counts().reset_index()
            status_counts.columns = ['Status', 'Count']
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Total Requests", len(api_data))
                
                success_count = status_counts[status_counts['Status'] == 200]['Count'].sum() if len(status_counts[status_counts['Status'] == 200]) > 0 else 0
                st.metric("Successful Requests", success_count)
            
            with col2:
                if 'response_time' in api_data.columns:
                    avg_response = api_data['response_time'].mean()
                    st.metric("Avg Response Time (ms)", f"{avg_response:.2f}")
                
                error_count = len(api_data) - success_count
                st.metric("Failed Requests", error_count)
            
            # Plot status code distribution
            fig = px.pie(status_counts, values='Count', names='Status', title='API Status Code Distribution')
            st.plotly_chart(fig, use_container_width=True)
            
            # Plot requests over time
            if 'timestamp' in api_data.columns:
                # Resample by hour
                api_data['timestamp'] = pd.to_datetime(api_data['timestamp'])
                hourly_requests = api_data.resample('H', on='timestamp').size().reset_index()
                hourly_requests.columns = ['timestamp', 'count']
                
                fig = px.line(hourly_requests, x='timestamp', y='count', title='API Requests per Hour')
                st.plotly_chart(fig, use_container_width=True)
            
            # Endpoint statistics if available
            if 'endpoint' in api_data.columns:
                st.subheader("Endpoint Usage")
                
                endpoint_counts = api_data['endpoint'].value_counts().reset_index()
                endpoint_counts.columns = ['Endpoint', 'Count']
                
                fig = px.bar(endpoint_counts, x='Endpoint', y='Count', title='Requests by Endpoint')
                st.plotly_chart(fig, use_container_width=True)
                    
                # Response time by endpoint
                if 'response_time' in api_data.columns:
                    endpoint_response = api_data.groupby('endpoint')['response_time'].mean().reset_index()
                    endpoint_response.columns = ['Endpoint', 'Avg Response Time (ms)']
                    
                    fig = px.bar(
                        endpoint_response, 
                        x='Endpoint', 
                        y='Avg Response Time (ms)',
                        title='Average Response Time by Endpoint'
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            # Show raw data
            with st.expander("View Raw API Usage Data"):
                st.dataframe(api_data, use_container_width=True)
        else:
            st.info("No API usage data available.")

# Function to analyze data collection gaps
@st.cache_data(persist="disk")
def analyze_collection_gaps():
    """
    Analyze data collection gaps and provide recommendations for the collector.
    
    Returns:
        dict: Dictionary containing gap analysis and recommendations
    """
    try:
        # Get all available endpoints
        endpoints_query = """
            SELECT DISTINCT endpoint FROM hyblock_data
        """
        endpoints_df = execute_mcp_query(endpoints_query)
        if endpoints_df is None or endpoints_df.empty:
            return {"error": "Failed to retrieve endpoints"}
        
        available_endpoints = endpoints_df['endpoint'].tolist()
        
        # Get all available coins
        coins_query = """
            SELECT DISTINCT coin FROM hyblock_data
        """
        coins_df = execute_mcp_query(coins_query)
        if coins_df is None or coins_df.empty:
            return {"error": "Failed to retrieve coins"}
        
        available_coins = coins_df['coin'].tolist()
        
        # Get all available exchanges
        exchanges_query = """
            SELECT DISTINCT exchange FROM hyblock_data
        """
        exchanges_df = execute_mcp_query(exchanges_query)
        if exchanges_df is None or exchanges_df.empty:
            return {"error": "Failed to retrieve exchanges"}
        
        available_exchanges = exchanges_df['exchange'].tolist()
        
        # Get all available timeframes
        timeframes_query = """
            SELECT DISTINCT timeframe FROM hyblock_data
        """
        timeframes_df = execute_mcp_query(timeframes_query)
        if timeframes_df is None or timeframes_df.empty:
            return {"error": "Failed to retrieve timeframes"}
        
        available_timeframes = timeframes_df['timeframe'].tolist()
        
        # Get coverage matrix (which endpoint-coin-exchange-timeframe combinations exist)
        coverage_query = """
            SELECT 
                endpoint, 
                coin, 
                exchange, 
                timeframe, 
                COUNT(*) as count, 
                MAX(timestamp) as latest_timestamp
            FROM 
                hyblock_data
            GROUP BY 
                endpoint, coin, exchange, timeframe
        """
        coverage_df = execute_mcp_query(coverage_query)
        if coverage_df is None or coverage_df.empty:
            return {"error": "Failed to retrieve coverage data"}
        
        # Find the most recent data for each combination
        coverage_df['latest_timestamp'] = pd.to_datetime(coverage_df['latest_timestamp'])
        coverage_df['age_hours'] = (datetime.now() - coverage_df['latest_timestamp']).dt.total_seconds() / 3600
        
        # Identify stale data (older than 24 hours)
        stale_data = coverage_df[coverage_df['age_hours'] > 24].sort_values('age_hours', ascending=False)
        
        # Identify missing combinations (focus on the most important ones)
        # For simplicity, focus on top coins and major exchanges
        top_coins = ['BTC', 'ETH', 'SOL', 'XRP', 'BNB', 'DOGE']  # Example top coins
        major_exchanges = ['binance', 'coinbase', 'bybit', 'okx', 'bitfinex']  # Example major exchanges
        important_timeframes = ['1h', '4h', '1d']  # Example important timeframes
        
        # Create all possible important combinations
        important_combinations = []
        for endpoint in available_endpoints:
            for coin in [c for c in top_coins if c in available_coins]:
                for exchange in [e for e in major_exchanges if e in available_exchanges]:
                    for timeframe in [t for t in important_timeframes if t in available_timeframes]:
                        important_combinations.append({
                            'endpoint': endpoint,
                            'coin': coin,
                            'exchange': exchange,
                            'timeframe': timeframe
                        })
        
        # Convert to DataFrame for easier comparison
        important_df = pd.DataFrame(important_combinations)
        
        # Merge with actual coverage to find missing combinations
        important_df['key'] = important_df['endpoint'] + '|' + important_df['coin'] + '|' + important_df['exchange'] + '|' + important_df['timeframe']
        coverage_df['key'] = coverage_df['endpoint'] + '|' + coverage_df['coin'] + '|' + coverage_df['exchange'] + '|' + coverage_df['timeframe']
        
        # Find missing combinations
        missing_keys = set(important_df['key']) - set(coverage_df['key'])
        missing_combinations = important_df[important_df['key'].isin(missing_keys)]
        
        # Generate recommendations
        recommendations = []
        
        # 1. Recommend collecting missing high-priority combinations
        if not missing_combinations.empty:
            high_priority = missing_combinations[missing_combinations['coin'].isin(['BTC', 'ETH'])]
            if not high_priority.empty:
                recommendations.append({
                    'priority': 'HIGH',
                    'type': 'missing_data',
                    'message': f"Collect data for {len(high_priority)} missing high-priority combinations",
                    'details': high_priority.drop('key', axis=1).to_dict('records')
                })
            
            medium_priority = missing_combinations[~missing_combinations['coin'].isin(['BTC', 'ETH'])]
            if not medium_priority.empty:
                recommendations.append({
                    'priority': 'MEDIUM',
                    'type': 'missing_data',
                    'message': f"Collect data for {len(medium_priority)} missing medium-priority combinations",
                    'details': medium_priority.drop('key', axis=1).to_dict('records')
                })
        
        # 2. Recommend refreshing stale data
        if not stale_data.empty:
            very_stale = stale_data[stale_data['age_hours'] > 72]  # Older than 3 days
            if not very_stale.empty:
                recommendations.append({
                    'priority': 'HIGH',
                    'type': 'stale_data',
                    'message': f"Refresh {len(very_stale)} combinations with very stale data (>3 days old)",
                    'details': very_stale.drop('key', axis=1).to_dict('records')
                })
            
            moderately_stale = stale_data[(stale_data['age_hours'] <= 72) & (stale_data['age_hours'] > 24)]
            if not moderately_stale.empty:
                recommendations.append({
                    'priority': 'MEDIUM',
                    'type': 'stale_data',
                    'message': f"Refresh {len(moderately_stale)} combinations with moderately stale data (1-3 days old)",
                    'details': moderately_stale.drop('key', axis=1).to_dict('records')
                })
        
        # Return the analysis results
        return {
            'available_endpoints': available_endpoints,
            'available_coins': available_coins,
            'available_exchanges': available_exchanges,
            'available_timeframes': available_timeframes,
            'total_combinations': len(coverage_df),
            'stale_combinations': len(stale_data),
            'missing_important_combinations': len(missing_combinations),
            'recommendations': recommendations
        }
    except Exception as e:
        logger.error(f"Error analyzing collection gaps: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {"error": str(e)}

# Main function to organize the app structure
def main():
    """Main function to organize the app structure"""
    
    # Sidebar navigation
    st.sidebar.title("Hyblock Data Dashboard")
    
    # Add navigation options
    nav_options = ["Dashboard", "Data Explorer", "Database Stats", "Advanced Explorer", "API Usage", "Collector Recommendations"]
    selected_option = st.sidebar.radio("Navigation", nav_options)
    
    # Display the selected section
    if selected_option == "Dashboard":
        display_dashboard()
    elif selected_option == "Data Explorer":
        display_data_explorer()
    elif selected_option == "Database Stats":
        display_database_status()
    elif selected_option == "Advanced Explorer":
        add_database_explorer_section()
    elif selected_option == "API Usage":
        display_api_usage()
    elif selected_option == "Collector Recommendations":
        display_collector_recommendations()
    
    # Add footer with version information
    st.sidebar.markdown("---")
    st.sidebar.markdown("v1.0.0 - Hyblock Data Dashboard")
    st.sidebar.markdown("Powered by Streamlit & MCP")

# Function to display collector recommendations
def display_collector_recommendations():
    """Display recommendations for the data collector"""
    st.header("📋 Data Collection Recommendations")
    st.markdown("Analyze data gaps and get recommendations for the collector")
    
    # Add refresh button
    if st.button("Refresh Analysis"):
        st.cache_data.clear()
        st.success("Cache cleared! Analysis will be refreshed.")
    
    # Get gap analysis
    with st.spinner("Analyzing data collection gaps..."):
        analysis = analyze_collection_gaps()
    
    if "error" in analysis:
        st.error(f"Error analyzing gaps: {analysis['error']}")
        return
    
    # Display summary statistics
    st.subheader("Collection Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Endpoints", len(analysis['available_endpoints']))
    with col2:
        st.metric("Total Coins", len(analysis['available_coins']))
    with col3:
        st.metric("Total Exchanges", len(analysis['available_exchanges']))
    with col4:
        st.metric("Total Timeframes", len(analysis['available_timeframes']))
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Combinations", analysis['total_combinations'])
    with col2:
        st.metric("Stale Combinations", analysis['stale_combinations'], 
                 delta=-analysis['stale_combinations'], delta_color="inverse")
    with col3:
        st.metric("Missing Combinations", analysis['missing_important_combinations'], 
                 delta=-analysis['missing_important_combinations'], delta_color="inverse")
    
    # Display recommendations
    st.subheader("Collection Recommendations")
    
    if not analysis['recommendations']:
        st.success("No recommendations at this time. Data collection is up to date!")
    else:
        # Sort recommendations by priority
        recommendations = sorted(
            analysis['recommendations'], 
            key=lambda x: 0 if x['priority'] == 'HIGH' else 1 if x['priority'] == 'MEDIUM' else 2
        )
        
        for i, rec in enumerate(recommendations):
            with st.expander(f"{rec['priority']} PRIORITY: {rec['message']}"):
                if rec['type'] == 'missing_data':
                    st.markdown("### Missing Data Combinations")
                    details_df = pd.DataFrame(rec['details'])
                    st.dataframe(details_df, use_container_width=True)
                    
                    # Add option to download as CSV for collector input
                    csv = details_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Download as CSV for Collector Input",
                        data=csv,
                        file_name=f"missing_data_combinations_{i}.csv",
                        mime="text/csv"
                    )
                elif rec['type'] == 'stale_data':
                    st.markdown("### Stale Data Combinations")
                    details_df = pd.DataFrame(rec['details'])
                    
                    # Format the timestamp and age for better readability
                    if 'latest_timestamp' in details_df.columns:
                        details_df['latest_timestamp'] = pd.to_datetime(details_df['latest_timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
                    if 'age_hours' in details_df.columns:
                        details_df['age_days'] = details_df['age_hours'] / 24
                        details_df['age_days'] = details_df['age_days'].round(1)
                        details_df = details_df.drop('age_hours', axis=1)
                    
                    st.dataframe(details_df, use_container_width=True)
                    
                    # Add option to download as CSV for collector input
                    csv = details_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Download as CSV for Collector Input",
                        data=csv,
                        file_name=f"stale_data_combinations_{i}.csv",
                        mime="text/csv"
                    )
    
    # Add section for collector configuration
    st.subheader("Collector Configuration")
    st.markdown("""
    To synchronize the collector with these recommendations:
    
    1. Download the relevant CSV files above
    2. Configure your collector to prioritize these combinations
    3. Run the collector with these inputs:
    ```
    python collector.py --input missing_data_combinations_0.csv --priority high
    python collector.py --input stale_data_combinations_0.csv --refresh
    ```
    """)
    
    # Display available endpoints, coins, exchanges, and timeframes
    with st.expander("View Available Data Dimensions"):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### Available Endpoints")
            st.write(", ".join(sorted(analysis['available_endpoints'])))
            
            st.markdown("### Available Exchanges")
            st.write(", ".join(sorted(analysis['available_exchanges'])))
        
        with col2:
            st.markdown("### Available Coins")
            st.write(", ".join(sorted(analysis['available_coins'])))
            
            st.markdown("### Available Timeframes")
            st.write(", ".join(sorted(analysis['available_timeframes'])))

# Entry point of the application
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"An error occurred: {e}")
        logger.error(f"Application error: {e}") 