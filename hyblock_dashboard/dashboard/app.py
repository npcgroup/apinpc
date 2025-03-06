import os
import sys
import json
import dash
from dash import dcc, html, callback, Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.database import connect_to_database, execute_query, get_logger

# Set up logger
logger = get_logger("dashboard")

# Initialize the Dash app
app = dash.Dash(__name__, title="Hyblock Data Dashboard")

# Define the layout
app.layout = html.Div([
    html.H1("Hyblock SUI Data Dashboard"),
    
    html.Div([
        html.Div([
            html.Label("Select Endpoint:"),
            dcc.Dropdown(
                id="endpoint-dropdown",
                options=[],
                value=None,
                placeholder="Select an endpoint"
            ),
        ], style={"width": "30%", "display": "inline-block", "marginRight": "2%"}),
        
        html.Div([
            html.Label("Select Coin:"),
            dcc.Dropdown(
                id="coin-dropdown",
                options=[{"label": "SUI", "value": "SUI"}],
                value="SUI",
                placeholder="Select a coin"
            ),
        ], style={"width": "20%", "display": "inline-block", "marginRight": "2%"}),
        
        html.Div([
            html.Label("Select Exchange:"),
            dcc.Dropdown(
                id="exchange-dropdown",
                options=[],
                value=None,
                placeholder="Select an exchange"
            ),
        ], style={"width": "20%", "display": "inline-block", "marginRight": "2%"}),
        
        html.Div([
            html.Label("Select Timeframe:"),
            dcc.Dropdown(
                id="timeframe-dropdown",
                options=[],
                value=None,
                placeholder="Select a timeframe"
            ),
        ], style={"width": "20%", "display": "inline-block"}),
    ]),
    
    html.Div([
        html.Label("Time Range:"),
        dcc.RadioItems(
            id="time-range",
            options=[
                {"label": "Last Hour", "value": "1h"},
                {"label": "Last 6 Hours", "value": "6h"},
                {"label": "Last 24 Hours", "value": "24h"},
                {"label": "Last 7 Days", "value": "7d"}
            ],
            value="24h"
        ),
    ], style={"marginTop": "20px"}),
    
    html.Div([
        dcc.Loading(
            id="loading-graph",
            type="circle",
            children=[
                dcc.Graph(id="data-graph")
            ]
        )
    ], style={"marginTop": "20px"}),
    
    html.Div([
        html.H3("Data Preview"),
        dcc.Loading(
            id="loading-table",
            type="circle",
            children=[
                html.Div(id="data-table")
            ]
        )
    ], style={"marginTop": "20px"}),
    
    dcc.Interval(
        id="interval-component",
        interval=60 * 1000,  # Update every minute
        n_intervals=0
    )
])

@callback(
    Output("endpoint-dropdown", "options"),
    Input("interval-component", "n_intervals")
)
def update_endpoints(_):
    """Update the list of available endpoints"""
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
            return [{"label": endpoint[0], "value": endpoint[0]} for endpoint in results]
        
        return []
    
    except Exception as e:
        logger.error(f"Error updating endpoints: {e}")
        return []

@callback(
    [
        Output("exchange-dropdown", "options"),
        Output("timeframe-dropdown", "options")
    ],
    [
        Input("endpoint-dropdown", "value"),
        Input("coin-dropdown", "value")
    ]
)
def update_filters(endpoint, coin):
    """Update the exchange and timeframe filters based on the selected endpoint and coin"""
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
        
        exchanges = [{"label": exch[0], "value": exch[0]} for exch in exchange_results if exch[0]]
        timeframes = [{"label": tf[0], "value": tf[0]} for tf in timeframe_results if tf[0]]
        
        return exchanges, timeframes
    
    except Exception as e:
        logger.error(f"Error updating filters: {e}")
        return [], []

@callback(
    [
        Output("data-graph", "figure"),
        Output("data-table", "children")
    ],
    [
        Input("endpoint-dropdown", "value"),
        Input("coin-dropdown", "value"),
        Input("exchange-dropdown", "value"),
        Input("timeframe-dropdown", "value"),
        Input("time-range", "value"),
        Input("interval-component", "n_intervals")
    ]
)
def update_graph(endpoint, coin, exchange, timeframe, time_range, _):
    """Update the graph and data table based on the selected filters"""
    try:
        if not endpoint or not coin:
            return go.Figure(), html.Div("Select an endpoint and coin to view data")
        
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
            return go.Figure(), html.Div("Failed to connect to database")
        
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
            return go.Figure(), html.Div("No data available for the selected filters")
        
        # Process the data
        timestamps = []
        data_points = []
        
        for row in results:
            timestamp = row[0]
            data_json = row[1]
            
            timestamps.append(timestamp)
            data_points.append(json.loads(data_json))
        
        # Create a figure based on the data
        fig = go.Figure()
        
        # This is a simplified approach - in reality, you'd need to adapt this
        # based on the specific structure of each endpoint's data
        try:
            # Try to extract a common data structure
            if data_points and isinstance(data_points[0], dict):
                # Check if there's a 'data' field with numeric values
                if 'data' in data_points[0] and isinstance(data_points[0]['data'], (int, float)):
                    values = [point.get('data', 0) for point in data_points]
                    fig.add_trace(go.Scatter(x=timestamps, y=values, mode='lines+markers', name='Value'))
                
                # Check if there's a 'value' field with numeric values
                elif 'value' in data_points[0] and isinstance(data_points[0]['value'], (int, float)):
                    values = [point.get('value', 0) for point in data_points]
                    fig.add_trace(go.Scatter(x=timestamps, y=values, mode='lines+markers', name='Value'))
                
                # If it's a more complex structure, just show the raw data
                else:
                    fig.add_annotation(
                        text="Complex data structure - see data preview below",
                        xref="paper", yref="paper",
                        x=0.5, y=0.5,
                        showarrow=False
                    )
            else:
                fig.add_annotation(
                    text="Unknown data structure - see data preview below",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5,
                    showarrow=False
                )
        
        except Exception as e:
            logger.error(f"Error processing data for visualization: {e}")
            fig.add_annotation(
                text=f"Error processing data: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False
            )
        
        fig.update_layout(
            title=f"{endpoint} - {coin}" + (f" - {exchange}" if exchange else "") + (f" - {timeframe}" if timeframe else ""),
            xaxis_title="Time",
            yaxis_title="Value",
            template="plotly_white"
        )
        
        # Create a data preview table
        # Just show the first 5 data points for simplicity
        preview_data = data_points[:5]
        preview_html = html.Pre(json.dumps(preview_data, indent=2))
        
        return fig, preview_html
    
    except Exception as e:
        logger.error(f"Error updating graph: {e}")
        return go.Figure(), html.Div(f"Error: {str(e)}")

if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=8050) 