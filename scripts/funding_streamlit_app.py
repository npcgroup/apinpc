import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
from rich.console import Console
import io
from contextlib import redirect_stdout
from advanced_funding_analyzer import AdvancedFundingAnalyzer
import time
from unified_funding_analyzer import UnifiedFundingAnalyzer
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging
import sys
import os

# Add the scripts directory to Python path to find the setup module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.setup_supabase import setup_supabase_tables

logger = logging.getLogger(__name__)

def capture_analyzer_output():
    """Capture the rich console output from the analyzer"""
    output = io.StringIO()
    with redirect_stdout(output):
        analyzer = AdvancedFundingAnalyzer()
        df = analyzer.analyze_funding_opportunities()
        if not df.empty:
            analyzer.display_results(df)
    return output.getvalue(), df

def create_funding_metrics(df):
    """Create key metrics display"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Markets", 
            len(df['symbol'].unique()),
            delta=f"{len(df[df['exchange'] == 'Binance'])} Binance / {len(df[df['exchange'] == 'Hyperliquid'])} HL"
        )
    with col2:
        avg_rate = df['funding_rate'].mean()
        st.metric(
            "Avg Funding Rate", 
            f"{avg_rate:.6f}",
            delta=f"{(avg_rate * 365 * 24):.2f}% APR"
        )
    with col3:
        highest_rate = df['funding_rate'].max()
        highest_symbol = df.loc[df['funding_rate'].idxmax(), 'symbol']
        st.metric(
            "Highest Rate", 
            f"{highest_rate:.6f}",
            delta=f"{highest_symbol}"
        )
    with col4:
        lowest_rate = df['funding_rate'].min()
        lowest_symbol = df.loc[df['funding_rate'].idxmin(), 'symbol']
        st.metric(
            "Lowest Rate", 
            f"{lowest_rate:.6f}",
            delta=f"{lowest_symbol}"
        )

def create_arbitrage_opportunities(df):
    """Create enhanced arbitrage opportunities visualization"""
    comparison_df = df.pivot_table(
        index='symbol',
        columns='exchange',
        values=['funding_rate', 'predicted_rate', 'mark_price']
    ).dropna()
    
    # Calculate spreads
    comparison_df['spread'] = comparison_df['funding_rate']['Binance'] - comparison_df['funding_rate']['Hyperliquid']
    comparison_df['predicted_spread'] = comparison_df['predicted_rate']['Binance'] - comparison_df['predicted_rate']['Hyperliquid']
    
    # Sort by absolute spread
    top_opportunities = comparison_df.nlargest(10, 'spread')
    
    # Create visualization
    fig = go.Figure()
    
    # Current spread bars
    fig.add_trace(go.Bar(
        name='Current Spread',
        x=top_opportunities.index,
        y=top_opportunities['spread'],
        marker_color=['red' if x < 0 else 'green' for x in top_opportunities['spread']]
    ))
    
    # Predicted spread line
    fig.add_trace(go.Scatter(
        name='Predicted Spread',
        x=top_opportunities.index,
        y=top_opportunities['predicted_spread'],
        line=dict(color='yellow', dash='dash')
    ))
    
    fig.update_layout(
        title='Top 10 Arbitrage Opportunities',
        xaxis_title='Symbol',
        yaxis_title='Spread',
        template='plotly_dark',
        barmode='group',
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        )
    )
    
    return fig, top_opportunities

def run_async(coro):
    """Helper to run async code in Streamlit with timeout"""
    try:
        with ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, coro)
            try:
                result = future.result(timeout=30)  # 30 second timeout
                
                # Validate result format
                if not isinstance(result, tuple) or len(result) != 2:
                    logger.error(f"Invalid result format: {result}")
                    return pd.DataFrame(), {}
                
                df, stats = result
                
                # Validate DataFrame
                if not isinstance(df, pd.DataFrame):
                    logger.error(f"Invalid DataFrame type: {type(df)}")
                    return pd.DataFrame(), {}
                
                # Validate required columns
                required_columns = ['symbol', 'exchange', 'funding_rate']
                missing_columns = [col for col in required_columns if col not in df.columns]
                if missing_columns:
                    logger.error(f"Missing required columns: {missing_columns}")
                    return pd.DataFrame(), {}
                
                # Check if DataFrame is empty
                if df.empty:
                    logger.warning("Received empty DataFrame from analyzer")
                    st.warning("No data available. The analyzer returned an empty dataset.")
                
                return df, stats
                
            except TimeoutError:
                logger.error("Async operation timed out")
                st.error("Data fetch timeout - taking too long to respond")
                return pd.DataFrame(), {}
                
            except Exception as e:
                logger.error(f"Error in async execution: {str(e)}", exc_info=True)
                st.error(f"Error processing data: {str(e)}")
                return pd.DataFrame(), {}
                
    except Exception as e:
        logger.error(f"Error in run_async: {str(e)}", exc_info=True)
        st.error(f"Error fetching data: {str(e)}")
        return pd.DataFrame(), {}

def main():
    st.set_page_config(page_title="Unified Funding Analysis", page_icon="📊", layout="wide")

    # Initialize Supabase tables if needed
    try:
        with st.spinner("Setting up database..."):
            if not setup_supabase_tables():
                st.error("Failed to setup database tables. Check your Supabase configuration.")
                return
    except Exception as e:
        st.error(f"Database setup error: {str(e)}")
        logger.error(f"Database setup error: {str(e)}", exc_info=True)
        return

    # Initialize analyzer with retry
    if 'analyzer' not in st.session_state:
        with st.spinner("Initializing analyzer..."):
            try:
                st.session_state.analyzer = UnifiedFundingAnalyzer()
                st.session_state.init_complete = True
            except Exception as e:
                st.error(f"Error initializing analyzer: {str(e)}")
                st.session_state.init_complete = False
                if st.button("Retry Initialization"):
                    st.rerun()
                return

    if not st.session_state.get('init_complete', False):
        st.error("Analyzer not properly initialized")
        if st.button("Retry Initialization"):
            st.rerun()
        return

    # Add refresh button and status
    col1, col2 = st.columns([1, 5])
    with col1:
        refresh = st.button("🔄 Refresh Data")
    with col2:
        if 'last_update' in st.session_state:
            st.write(f"Last updated: {st.session_state.last_update.strftime('%H:%M:%S')}")

    # Run analysis with progress and error handling
    if 'last_update' not in st.session_state or refresh:
        try:
            with st.spinner("Fetching latest funding data..."):
                unified_df, stats = run_async(
                    st.session_state.analyzer.get_unified_analysis()
                )
                
                if unified_df.empty:
                    st.warning("No data received from the analyzer. Will retry in 5 seconds...")
                    time.sleep(5)
                    st.rerun()
                
                # Store the results in session state
                st.session_state.last_update = datetime.now()
                st.session_state.unified_df = unified_df
                st.session_state.stats = stats
                
        except Exception as e:
            st.error(f"Error updating data: {str(e)}")
            logger.error(f"Analysis error: {str(e)}", exc_info=True)
            
            # Initialize empty state if needed
            if 'unified_df' not in st.session_state:
                st.session_state.unified_df = pd.DataFrame()
                st.session_state.stats = {}
            
            # Add retry button
            if st.button("Retry"):
                st.rerun()
            return

    # Auto-refresh logic
    if 'last_update' in st.session_state:
        time_since_update = datetime.now() - st.session_state.last_update
        if time_since_update.total_seconds() > 60:  # Refresh every minute
            st.rerun()

    # Display data if available
    if hasattr(st.session_state, 'unified_df') and not st.session_state.unified_df.empty:
        try:
            # Display metrics
            display_metrics(st.session_state.unified_df, st.session_state.stats)
            
            # Create tabs
            tab1, tab2, tab3 = st.tabs([
                "🎯 Top Opportunities",
                "📊 Market Analysis",
                "🔍 Detailed View"
            ])

            # Get visualization data with error handling
            try:
                viz_data = st.session_state.analyzer.create_visualization_data(
                    st.session_state.unified_df
                )
            except Exception as e:
                st.error("Error creating visualizations. Displaying raw data instead.")
                logger.error(f"Visualization error: {str(e)}", exc_info=True)
                viz_data = {}

            display_tabs(tab1, tab2, tab3, viz_data, st.session_state.unified_df)

        except Exception as e:
            st.error(f"Error displaying data: {str(e)}")
            logger.error(f"Display error: {str(e)}", exc_info=True)
            
            # Add retry button
            if st.button("Retry Display"):
                st.rerun()
    else:
        st.warning("No funding rate data available. Please try refreshing.")
        
        # Add manual refresh button
        if st.button("Refresh Data"):
            st.rerun()

def display_metrics(df, stats):
    """Display key metrics in columns"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Markets",
            f"{stats.get('total_markets', 0):,}",
            f"${stats.get('total_volume_24h', 0)/1e6:.1f}M 24h Volume"
        )
    with col2:
        st.metric(
            "Avg Funding Rate",
            f"{stats.get('avg_funding_rate', 0)*100:.4f}%",
            f"{stats.get('avg_funding_rate', 0)*365*100:.1f}% APR"
        )
    with col3:
        st.metric(
            "Best Opportunity Score",
            f"{stats.get('max_opportunity_score', 0):.4f}"
        )
    with col4:
        st.metric(
            "Last Update",
            datetime.now().strftime("%H:%M:%S")
        )

def display_tabs(tab1, tab2, tab3, viz_data, df):
    """Display content in tabs"""
    with tab1:
        if 'opportunity_scatter' in viz_data:
            st.plotly_chart(viz_data['opportunity_scatter'], use_container_width=True)
        if 'top_opportunities' in viz_data:
            display_top_opportunities(viz_data['top_opportunities'])

    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            if 'funding_distribution' in viz_data:
                st.plotly_chart(viz_data['funding_distribution'], use_container_width=True)
        with col2:
            if 'market_heatmap' in viz_data:
                st.plotly_chart(viz_data['market_heatmap'], use_container_width=True)

    with tab3:
        display_detailed_view(df)

def display_top_opportunities(top_opps):
    """Display top opportunities table"""
    if not top_opps.empty:
        st.dataframe(
            top_opps[[
                'symbol', 'exchange', 'funding_rate',
                'predicted_rate', 'opportunity_score',
                'annualized_rate'
            ]].style.format({
                'funding_rate': '{:.6f}',
                'predicted_rate': '{:.6f}',
                'opportunity_score': '{:.4f}',
                'annualized_rate': '{:.2f}%'
            })
        )

def display_detailed_view(df):
    """Display detailed view of all data"""
    st.dataframe(
        df.style.format({
            'funding_rate': '{:.6f}',
            'predicted_rate': '{:.6f}',
            'opportunity_score': '{:.4f}',
            'annualized_rate': '{:.2f}%',
            'volume_24h': '${:,.0f}',
            'market_size': '${:,.0f}'
        })
    )

if __name__ == "__main__":
    main() 