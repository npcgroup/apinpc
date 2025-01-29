import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
from rich.console import Console
from advanced_funding_analyzer import AdvancedFundingAnalyzer
from supabase import create_client
import os
from dotenv import load_dotenv
import time
import logging

logger = logging.getLogger(__name__)

def get_predicted_rates():
    """Fetch predicted rates from Supabase with proper column handling"""
    try:
        load_dotenv()
        supabase = create_client(
            os.getenv("NEXT_PUBLIC_SUPABASE_URL"),
            os.getenv("NEXT_PUBLIC_SUPABASE_KEY")
        )
        
        # Early validation of Supabase connection
        if not supabase:
            logger.error("Failed to initialize Supabase client")
            return pd.DataFrame()
        
        response = (supabase.table('predicted_funding_rates')
            .select('id,asset,predicted_rate,annualized_rate,direction,exchange,next_funding_time,created_at,timestamp')
            .order('created_at', desc=True)
            .limit(100)
            .execute())
        
        if not response.data:
            logger.warning("No data returned from Supabase")
            return pd.DataFrame()
            
        df = pd.DataFrame(response.data)
        logger.info(f"Raw columns from Supabase: {df.columns.tolist()}")
        
        # Ensure all required columns exist
        required_cols = ['asset', 'predicted_rate', 'next_funding_time']
        if not all(col in df.columns for col in required_cols):
            logger.error(f"Missing required columns. Found: {df.columns.tolist()}")
            return pd.DataFrame()
        
        # Convert timestamps with proper timezone handling
        for col in ['next_funding_time', 'created_at', 'timestamp']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], utc=True)
        
        latest_time = df['created_at'].max()
        latest_df = df[df['created_at'] >= latest_time - pd.Timedelta(minutes=5)]
        
        result_df = pd.DataFrame({
            'symbol': latest_df['asset'].str.upper(),
            'predicted_rate': pd.to_numeric(latest_df['predicted_rate'], errors='coerce'),
            'next_funding_time': latest_df['next_funding_time'],
            'exchange': latest_df['exchange'],
            'direction': latest_df['direction'],
            'annualized_rate': pd.to_numeric(latest_df['annualized_rate'], errors='coerce')
        })
        
        result_df = (result_df.sort_values('next_funding_time', ascending=False)
                            .groupby('symbol')
                            .first()
                            .reset_index())
        
        logger.info(f"Found {len(result_df)} predicted rates")
        return result_df
        
    except Exception as e:
        logger.error(f"Error fetching predicted rates: {e}")
        return pd.DataFrame()

def check_supabase_connection():
    """Check Supabase connection and data availability before fetching exchange data"""
    try:
        load_dotenv()
        supabase = create_client(
            os.getenv("NEXT_PUBLIC_SUPABASE_URL"),
            os.getenv("NEXT_PUBLIC_SUPABASE_KEY")
        )
        
        # Test connection with a small query
        response = (supabase.table('predicted_funding_rates')
            .select('count', count='exact')
            .limit(1)
            .execute())
            
        return True if response else False
        
    except Exception as e:
        logger.error(f"Supabase connection check failed: {e}")
        return False

def fetch_data():
    """Fetch and combine current and predicted rates with early validation"""
    try:
        # Early Supabase check
        if not check_supabase_connection():
            st.error("Cannot connect to Supabase. Please check your connection and try again.")
            return pd.DataFrame()
            
        with st.spinner("Fetching predicted rates..."):
            predicted_df = get_predicted_rates()
            if predicted_df.empty:
                st.warning("No predicted rates available from Supabase. Proceeding with current rates only.")
            else:
                logger.info(f"Successfully fetched {len(predicted_df)} predicted rates")
        
        with st.spinner("Fetching current exchange rates..."):
            analyzer = AdvancedFundingAnalyzer()
            df = analyzer.analyze_funding_opportunities()
            
            if not isinstance(df, pd.DataFrame) or df.empty:
                st.error("No data received from exchanges")
                return pd.DataFrame()
            
            logger.info(f"Successfully fetched {len(df)} current rates")
            
            # Combine the data
            if not predicted_df.empty:
                df['symbol'] = df['symbol'].str.upper()
                df = df.merge(
                    predicted_df[[
                        'symbol', 
                        'predicted_rate', 
                        'next_funding_time',
                        'direction',
                        'annualized_rate'
                    ]],
                    on='symbol',
                    how='left',
                    suffixes=('', '_pred')
                )
                
                # Ensure all timestamps are UTC
                now = pd.Timestamp.now(tz='UTC')
                df['time_to_funding'] = df.apply(
                    lambda row: max(0, (pd.Timestamp(row['next_funding_time'], tz='UTC') - now).total_seconds() / 3600) 
                    if pd.notnull(row.get('next_funding_time')) else 8.0,
                    axis=1
                )
            else:
                # Use current rates if no predictions available
                df['predicted_rate'] = df['funding_rate']
                df['direction'] = 'neutral'
                df['time_to_funding'] = 8.0
            
            # Fill any missing values
            df['predicted_rate'] = df['predicted_rate'].fillna(df['funding_rate'])
            df['direction'] = df['direction'].fillna('neutral')
            
            # Calculate scores
            df['opportunity_score'] = df.apply(calculate_opportunity_score, axis=1)
            df['annualized_rate'] = df.apply(
                lambda x: float(x['funding_rate']) * (365 * 24 / x['payment_interval']) * 100,
                axis=1
            )
            
            logger.info(f"Final dataframe shape: {df.shape}")
            return df.sort_values('opportunity_score', ascending=False)
            
    except Exception as e:
        logger.error(f"Error in fetch_data: {str(e)}")
        st.error(f"Error fetching data: {str(e)}")
        return pd.DataFrame()

def calculate_opportunity_score(row):
    """Calculate opportunity score based on rates and timing"""
    try:
        current_rate = abs(float(row['funding_rate']))
        predicted_rate = abs(float(row.get('predicted_rate', current_rate)))
        time_to_funding = float(row.get('time_to_funding', 8))
        
        # Normalize time factor
        time_factor = max(0, min(1, (8 - time_to_funding) / 8))
        
        # Calculate score with time weighting
        base_score = abs(current_rate - predicted_rate) + abs(current_rate)
        score = base_score * (1 + time_factor)
        
        return score * (365 * 24 / row['payment_interval']) * 100
    except Exception as e:
        return 0

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
                y='predicted_rate',  # Changed from predicted_funding_rate
                color='exchange',
                hover_data=['symbol', 'annualized_rate', 'opportunity_score'],
                title='Current vs Predicted Funding Rates'
            ),
            'top_opportunities': df.nlargest(10, 'opportunity_score'),
            'funding_heatmap': px.density_heatmap(
                df,
                x='funding_rate',
                y='predicted_rate',  # Changed from predicted_funding_rate
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
                    display_top_opportunities(viz_data['top_opportunities'])

            with tab2:
                col1, col2 = st.columns(2)
                with col1:
                    if 'funding_distribution' in viz_data:
                        st.plotly_chart(viz_data['funding_distribution'], use_container_width=True)
                with col2:
                    if 'funding_heatmap' in viz_data:
                        st.plotly_chart(viz_data['funding_heatmap'], use_container_width=True)

            with tab3:
                display_detailed_view(st.session_state.df)

        except Exception as e:
            st.error(f"Error displaying data: {str(e)}")
            logger.error(f"Display error: {str(e)}", exc_info=True)
            if st.button("Retry Display"):
                st.rerun()
    else:
        st.info("Waiting for data... Click Refresh Data to start.")

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
                'opportunity_score': '{:.2f}',
                'annualized_rate': '{:.2f}%'
            })
        )

def display_detailed_view(df):
    """Display detailed view of all data"""
    st.dataframe(
        df.style.format({
            'funding_rate': '{:.6f}',
            'predicted_rate': '{:.6f}',
            'opportunity_score': '{:.2f}',
            'annualized_rate': '{:.2f}%',
            'mark_price': '${:,.2f}'
        })
    )

if __name__ == "__main__":
    main() 