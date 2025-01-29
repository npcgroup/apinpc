import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
from rich.console import Console
from advanced_funding_analyzer import AdvancedFundingAnalyzer
import time
import logging

logger = logging.getLogger(__name__)

def fetch_data():
    """Fetch data with proper error handling"""
    try:
        with st.spinner("Fetching funding rates..."):
            analyzer = AdvancedFundingAnalyzer()
            df = analyzer.analyze_funding_opportunities()
            
            if isinstance(df, pd.DataFrame) and not df.empty:
                # Calculate annualized rates if not present
                if 'annualized_rate' not in df.columns:
                    df['annualized_rate'] = df.apply(
                        lambda x: float(x['funding_rate']) * (365 * 24 / x['payment_interval']) * 100,
                        axis=1
                    )
                return df
            else:
                st.warning("No data received from exchanges")
                return pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
        logger.error(f"Fetch error: {str(e)}", exc_info=True)
        return pd.DataFrame()

def calculate_stats(df: pd.DataFrame) -> dict:
    """Calculate statistics from the funding data"""
    if df.empty:
        return {}
    
    try:
        return {
            'total_markets': len(df),
            'binance_markets': len(df[df['exchange'] == 'Binance']),
            'hl_markets': len(df[df['exchange'] == 'Hyperliquid']),
            'avg_funding_rate': df['funding_rate'].mean(),
            'max_funding_rate': df['funding_rate'].max(),
            'min_funding_rate': df['funding_rate'].min(),
            'timestamp': datetime.now()
        }
    except Exception as e:
        logger.error(f"Error calculating stats: {e}")
        return {}

def create_visualizations(df: pd.DataFrame) -> dict:
    """Create visualization data for Streamlit"""
    try:
        return {
            'funding_distribution': px.box(
                df, x='exchange', y='funding_rate',
                title='Funding Rate Distribution by Exchange'
            ),
            'opportunity_scatter': px.scatter(
                df,
                x='funding_rate',
                y='predicted_rate',
                color='exchange',
                hover_data=['symbol', 'annualized_rate'],
                title='Funding Rate vs Predicted Rate'
            ),
            'top_opportunities': df.nlargest(10, 'annualized_rate'),
            'funding_heatmap': px.density_heatmap(
                df,
                x='funding_rate',
                y='predicted_rate',
                title='Funding Rate Density'
            )
        }
    except Exception as e:
        logger.error(f"Error creating visualizations: {e}")
        return {}

def main():
    st.set_page_config(page_title="Funding Rate Analysis", page_icon="📊", layout="wide")

    # Add refresh button and status
    col1, col2 = st.columns([1, 5])
    with col1:
        refresh = st.button("🔄 Refresh Data")
    with col2:
        if 'last_update' in st.session_state:
            st.write(f"Last updated: {st.session_state.last_update.strftime('%H:%M:%S')}")

    # Run analysis with progress and error handling
    if 'df' not in st.session_state or refresh:
        df = fetch_data()
        if not df.empty:
            st.session_state.df = df
            st.session_state.last_update = datetime.now()
            st.session_state.stats = calculate_stats(df)
        else:
            if st.button("Retry"):
                st.rerun()
            return

    # Display data if available
    if 'df' in st.session_state and not st.session_state.df.empty:
        try:
            # Display metrics
            stats = st.session_state.stats
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Total Markets",
                    f"{stats['total_markets']}",
                    f"{stats['binance_markets']} Binance / {stats['hl_markets']} HL"
                )
            with col2:
                st.metric(
                    "Avg Funding Rate",
                    f"{stats['avg_funding_rate']*100:.4f}%",
                    f"{stats['avg_funding_rate']*365*100:.1f}% APR"
                )
            with col3:
                st.metric(
                    "Highest Rate",
                    f"{stats['max_funding_rate']*100:.4f}%"
                )
            with col4:
                st.metric(
                    "Lowest Rate",
                    f"{stats['min_funding_rate']*100:.4f}%"
                )

            # Create tabs
            tab1, tab2, tab3 = st.tabs([
                "🎯 Top Opportunities",
                "📊 Market Analysis",
                "🔍 Detailed View"
            ])

            # Get visualization data
            viz_data = create_visualizations(st.session_state.df)

            # Display tabs content
            with tab1:
                if 'opportunity_scatter' in viz_data:
                    st.plotly_chart(viz_data['opportunity_scatter'], use_container_width=True)
                if 'top_opportunities' in viz_data:
                    st.dataframe(
                        viz_data['top_opportunities'][[
                            'symbol', 'exchange', 'funding_rate',
                            'predicted_rate', 'annualized_rate'
                        ]].style.format({
                            'funding_rate': '{:.6f}',
                            'predicted_rate': '{:.6f}',
                            'annualized_rate': '{:.2f}%'
                        })
                    )

            with tab2:
                col1, col2 = st.columns(2)
                with col1:
                    if 'funding_distribution' in viz_data:
                        st.plotly_chart(viz_data['funding_distribution'], use_container_width=True)
                with col2:
                    if 'funding_heatmap' in viz_data:
                        st.plotly_chart(viz_data['funding_heatmap'], use_container_width=True)

            with tab3:
                st.dataframe(
                    st.session_state.df.style.format({
                        'funding_rate': '{:.6f}',
                        'predicted_rate': '{:.6f}',
                        'annualized_rate': '{:.2f}%',
                        'mark_price': '${:,.2f}'
                    })
                )

        except Exception as e:
            st.error(f"Error displaying data: {str(e)}")
            logger.error(f"Display error: {str(e)}", exc_info=True)
            if st.button("Retry Display"):
                st.rerun()
    else:
        st.info("Waiting for data... Click Refresh Data to start.")

if __name__ == "__main__":
    main() 