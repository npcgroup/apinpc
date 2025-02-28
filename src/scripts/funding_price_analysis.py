import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from supabase import create_client
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase = create_client(
    os.getenv("NEXT_PUBLIC_SUPABASE_URL"),
    os.getenv("NEXT_PUBLIC_SUPABASE_KEY")
)

def get_price_history(symbol, lookback_hours=72):
    """
    Fetch price history from Supabase for a given symbol
    """
    try:
        start_time = (datetime.now() - timedelta(hours=lookback_hours)).isoformat()
        
        response = supabase.table('price_history')\
            .select("*")\
            .eq('symbol', symbol)\
            .gte('timestamp', start_time)\
            .order('timestamp', desc=True)\
            .execute()
            
        if not response.data:
            return pd.DataFrame()
            
        df = pd.DataFrame(response.data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        return df
        
    except Exception as e:
        st.error(f"Error fetching price history for {symbol}: {e}")
        return pd.DataFrame()

def get_funding_rates(symbol, lookback_hours=72):
    """
    Fetch funding rates from Supabase for a given symbol
    """
    try:
        start_time = (datetime.now() - timedelta(hours=lookback_hours)).isoformat()
        
        response = supabase.table('funding_market_snapshots')\
            .select("*")\
            .eq('symbol', symbol)\
            .gte('created_at', start_time)\
            .order('created_at', desc=True)\
            .execute()
            
        if not response.data:
            return pd.DataFrame()
            
        df = pd.DataFrame(response.data)
        df['timestamp'] = pd.to_datetime(df['created_at'])
        df.set_index('timestamp', inplace=True)
        return df
        
    except Exception as e:
        st.error(f"Error fetching funding rates for {symbol}: {e}")
        return pd.DataFrame()

def calculate_performance(df):
    """
    Calculate historical performance metrics
    """
    if df.empty:
        return {"24h": None, "48h": None, "72h": None}
    
    current_price = df['close'].iloc[0]  # Most recent price
    metrics = {}
    
    for hours in [24, 48, 72]:
        try:
            past_price = df['close'][df.index <= df.index[0] - timedelta(hours=hours)].iloc[0]
            perf = ((current_price - past_price) / past_price) * 100
            metrics[f"{hours}h"] = round(perf, 2)
        except (IndexError, KeyError):
            metrics[f"{hours}h"] = None
            
    return metrics

def main():
    st.title("🔄 Funding Rate vs Price Performance Analysis")
    
    # Default symbols
    default_symbols = ["BTC", "ETH", "SOL", "AVAX", "LINK"]
    
    # Sidebar controls
    st.sidebar.header("Settings")
    selected_symbols = st.sidebar.multiselect(
        "Select Symbols",
        options=default_symbols,
        default=default_symbols[:3]
    )
    
    lookback_hours = st.sidebar.slider(
        "Lookback Period (hours)",
        min_value=24,
        max_value=168,
        value=72,
        step=24
    )
    
    # Main analysis
    if not selected_symbols:
        st.warning("Please select at least one symbol to analyze")
        return
        
    analysis_data = []
    
    for symbol in selected_symbols:
        with st.spinner(f"Analyzing {symbol}..."):
            # Get price history
            price_df = get_price_history(symbol, lookback_hours)
            if price_df.empty:
                st.warning(f"No price data available for {symbol}")
                continue
                
            # Get funding rates
            funding_df = get_funding_rates(symbol, lookback_hours)
            if funding_df.empty:
                st.warning(f"No funding rate data available for {symbol}")
                continue
                
            # Calculate metrics
            perf = calculate_performance(price_df)
            current_funding = funding_df['funding_rate'].iloc[0] * 100  # Convert to percentage
            
            # Store analysis results
            analysis_data.append({
                "symbol": symbol,
                "current_price": price_df['close'].iloc[0],
                "funding_rate": round(current_funding, 4),
                "24h_perf": perf["24h"],
                "48h_perf": perf["48h"],
                "72h_perf": perf["72h"],
                "volume_24h": price_df['volume'].iloc[0],
            })
            
            # Create price and funding rate chart
            fig = go.Figure()
            
            # Add price line
            fig.add_trace(go.Scatter(
                x=price_df.index,
                y=price_df['close'],
                name='Price',
                yaxis='y1'
            ))
            
            # Add funding rate line
            fig.add_trace(go.Scatter(
                x=funding_df.index,
                y=funding_df['funding_rate'] * 100,  # Convert to percentage
                name='Funding Rate (%)',
                yaxis='y2'
            ))
            
            # Update layout
            fig.update_layout(
                title=f"{symbol} Price and Funding Rate",
                yaxis=dict(title="Price"),
                yaxis2=dict(title="Funding Rate (%)", overlaying='y', side='right'),
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    # Display analysis table
    if analysis_data:
        df_analysis = pd.DataFrame(analysis_data)
        
        # Format the dataframe
        df_display = df_analysis.copy()
        df_display['current_price'] = df_display['current_price'].map('${:,.2f}'.format)
        df_display['volume_24h'] = df_display['volume_24h'].map('${:,.0f}'.format)
        df_display['funding_rate'] = df_display['funding_rate'].map('{:,.4f}%'.format)
        for col in ['24h_perf', '48h_perf', '72h_perf']:
            df_display[col] = df_display[col].map('{:,.2f}%'.format)
        
        st.subheader("Analysis Summary")
        st.dataframe(df_display, use_container_width=True)
        
        # Create performance comparison chart
        performance_data = []
        for _, row in df_analysis.iterrows():
            for period in ['24h_perf', '48h_perf', '72h_perf']:
                if pd.notnull(row[period]):
                    performance_data.append({
                        'Symbol': row['symbol'],
                        'Period': period.replace('_perf', ''),
                        'Performance': row[period]
                    })
        
        if performance_data:
            df_perf = pd.DataFrame(performance_data)
            fig_perf = px.bar(
                df_perf,
                x='Symbol',
                y='Performance',
                color='Period',
                barmode='group',
                title='Performance Comparison'
            )
            st.plotly_chart(fig_perf, use_container_width=True)

if __name__ == "__main__":
    main() 