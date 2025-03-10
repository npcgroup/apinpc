import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from rich.console import Console
from advanced_funding_analyzer import AdvancedFundingAnalyzer
from supabase import create_client
import os
from dotenv import load_dotenv
import time
import logging
import yaml
from pathlib import Path
import sys
import logging.config
import math
import requests
import json
from types import SimpleNamespace
import argparse

# Configure logging
logging.config.dictConfig({
    'version': 1,
    'formatters': {
        'default': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
            'level': 'INFO',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'app.log',
            'formatter': 'default',
            'level': 'INFO',
        }
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    }
})

logger = logging.getLogger(__name__)

# Add the project root to the Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

# Environment variables
def load_environment():
    """Load environment variables from .env file or environment"""
    load_dotenv()
    
    required_vars = [
        "NEXT_PUBLIC_SUPABASE_URL",
        "NEXT_PUBLIC_SUPABASE_KEY"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        st.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        return False
    return True

def get_predicted_rates():
    """Fetch predicted rates from Supabase with proper rate normalization"""
    try:
        # Connect to Supabase for read operations
        load_dotenv()
        supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        supabase_key = os.getenv("NEXT_PUBLIC_SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            logger.error("Missing Supabase credentials")
            return pd.DataFrame()
            
        # Initialize Supabase client with minimal parameters
        supabase = create_client(supabase_url, supabase_key)
        
        # Get current UTC time
        current_utc = pd.Timestamp.now(tz='UTC')
        
        # First get all recent predictions
        response = (supabase.table('predicted_funding_rates')
            .select("*")
            .order('created_at', desc=True)
            .limit(1000)  # Get enough data to find matches
            .execute())
        
        if not response.data:
            logger.error("No predicted rates found in Supabase")
            return pd.DataFrame()
            
        df = pd.DataFrame(response.data)
        
        # Debug initial data
        logger.info(f"\n=== Raw Data ===")
        logger.info(f"Total records: {len(df)}")
        logger.info(f"Unique assets: {df['asset'].nunique()}")
        logger.info(f"Unique exchanges: {df['exchange'].unique().tolist()}")
        
        # Convert timestamps to UTC
        for col in ['next_funding_time', 'created_at', 'timestamp']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], utc=True)
        
        # Map exchange names first
        exchange_map = {
            'BinPerp': 'Binance',
            'HlPerp': 'Hyperliquid',
            'Binance': 'Binance',
            'Hyperliquid': 'Hyperliquid'
        }
        df['exchange'] = df['exchange'].map(exchange_map)
        
        # Get latest prediction for each asset/exchange combination
        latest_df = (df.sort_values('created_at', ascending=False)
                      .groupby(['asset', 'exchange'])
                      .first()
                      .reset_index())
        
        # Convert rates to proper format and normalize
        latest_df['predicted_rate'] = latest_df.apply(
            lambda x: float(x['predicted_rate']) * (100 if x['exchange'] == 'Hyperliquid' else 10),
            axis=1
        )
        latest_df['annualized_rate'] = latest_df.apply(
            lambda x: float(x['annualized_rate']) * (100 if x['exchange'] == 'Hyperliquid' else 10),
            axis=1
        )
        
        # Prepare final DataFrame with normalized rates
        result_df = pd.DataFrame({
            'symbol': latest_df['asset'].str.upper(),
            'exchange': latest_df['exchange'],
            'predicted_rate': latest_df['predicted_rate'],  # Already normalized above
            'direction': latest_df['direction'],
            'annualized_rate': latest_df['annualized_rate'],
            'next_funding_time': latest_df['next_funding_time']
        })
        
        # Debug final results with normalized rates
        logger.info("\n=== Final Predictions (Normalized) ===")
        logger.info(f"Total predictions: {len(result_df)}")
        for ex in ['Binance', 'Hyperliquid']:
            ex_df = result_df[result_df['exchange'] == ex]
            logger.info(f"\n{ex} predictions: {len(ex_df)}")
            if not ex_df.empty:
                logger.info(f"Sample {ex} predictions (normalized):")
                sample = ex_df[['symbol', 'predicted_rate', 'next_funding_time']].head()
                logger.info(f"{sample.to_dict('records')}")
                logger.info(f"Normalized rate range: {ex_df['predicted_rate'].min():.6f} to {ex_df['predicted_rate'].max():.6f}")
        
        return result_df
        
    except Exception as e:
        logger.error(f"Error fetching predicted rates: {e}")
        logger.error("Error details:", exc_info=True)
        return pd.DataFrame()

def check_supabase_connection():
    """Check Supabase connection and data availability before fetching exchange data"""
    try:
        load_dotenv()
        supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        supabase_key = os.getenv("NEXT_PUBLIC_SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            logger.error("Missing Supabase credentials")
            return False
            
        # Initialize Supabase client with minimal parameters
        supabase = create_client(supabase_url, supabase_key)
        
        # Test connection with a small query
        response = (supabase.table('predicted_funding_rates')
            .select('count', count='exact')
            .limit(1)
            .execute())
            
        return True if response else False
        
    except Exception as e:
        logger.error(f"Supabase connection check failed: {e}")
        return False

def calculate_opportunity_score(row):
    """Calculate opportunity score based on rate difference and market factors"""
    try:
        # Base score from rate difference
        score = abs(row['rate_diff']) * 100
        
        # Adjust based on time to funding
        time_factor = 1.0 if row['time_to_funding'] <= 1.0 else (8.0 / row['time_to_funding'])
        score *= time_factor
        
        # Adjust based on mark price (if available)
        if 'mark_price' in row and pd.notnull(row['mark_price']) and row['mark_price'] > 0:
            price_factor = min(1.0, math.log10(row['mark_price']) / 4)
            score *= (1 + price_factor)
            
        return round(score, 2)
    except Exception as e:
        logger.error(f"Error calculating opportunity score: {e}")
        return 0.0

def fetch_data(use_cache=True, max_retries=3):
    """Fetch and combine current and predicted rates with proper rate matching"""
    retry_count = 0
    while retry_count < max_retries:
        try:
            # Check cache first if enabled
            cache_file = 'funding_data_cache.pkl'
            cache_max_age = 3600  # 1 hour in seconds
            
            if use_cache and os.path.exists(cache_file):
                cache_modified_time = os.path.getmtime(cache_file)
                cache_age = time.time() - cache_modified_time
                
                if cache_age < cache_max_age:
                    try:
                        df = pd.read_pickle(cache_file)
                        logger.info(f"Using cached data ({cache_age:.1f} seconds old)")
                        return df
                    except Exception as cache_error:
                        logger.warning(f"Cache read failed: {cache_error}")
            
            # Get predicted rates first
            logger.info("Fetching predicted rates from Supabase...")
            predicted_df = get_predicted_rates()
            
            if predicted_df.empty:
                logger.warning("No predicted rates found in Supabase. Will use current rates as predictions.")
            else:
                logger.info(f"Successfully fetched {len(predicted_df)} predicted rates from Supabase")
                logger.info(f"Predicted rates shape: {predicted_df.shape}")
                logger.info(f"Predicted rates exchanges: {predicted_df['exchange'].unique().tolist()}")
                logger.info(f"Sample predicted rates: {predicted_df[['symbol', 'exchange', 'predicted_rate']].head(3).to_dict('records')}")
            
            # Get current rates
            logger.info("Fetching current rates from exchanges...")
            analyzer = AdvancedFundingAnalyzer()
            df = analyzer.analyze_funding_opportunities()
            
            if not isinstance(df, pd.DataFrame) or df.empty:
                logger.error("Failed to fetch current rates from exchanges")
                retry_count += 1
                if retry_count < max_retries:
                    logger.warning(f"Retry {retry_count}/{max_retries} for fetch_data due to empty result")
                    time.sleep(5)  # Wait 5 seconds before retrying
                    continue
                else:
                    logger.error(f"All {max_retries} retries failed, returning empty DataFrame")
                    return pd.DataFrame()
            
            # Create a copy to avoid modifying original
            df = df.copy()
            logger.info(f"Successfully fetched {len(df)} current rates from exchanges")
            logger.info(f"Current rates exchanges: {df['exchange'].unique().tolist()}")
            logger.info(f"Sample current rates: {df[['symbol', 'exchange', 'funding_rate']].head(3).to_dict('records')}")
            
            # Initialize required columns with defaults
            required_columns = ['predicted_rate', 'direction', 'rate_diff']
            for col in required_columns:
                if col not in df.columns:
                    df[col] = None
            
            # Standardize symbols for matching
            df['symbol'] = df['symbol'].str.upper().str.replace('USDT', '').str.replace('PERP', '').str.strip()
            
            # Fix decimal places and normalize rates based on exchange
            df['funding_rate'] = df.apply(
                lambda x: (x['funding_rate'] * 100) if x['exchange'] == 'Hyperliquid' 
                else (x['funding_rate'] * 10),  # Binance rate normalization
                axis=1
            )
            
            try:
                if not predicted_df.empty:
                    # Ensure predicted_df has required columns
                    required_pred_columns = ['symbol', 'exchange', 'predicted_rate', 'direction']
                    if all(col in predicted_df.columns for col in required_pred_columns):
                        # Merge with predicted rates matching on both symbol and exchange
                        logger.info("Merging current and predicted rates...")
                        merged_df = df.merge(
                            predicted_df,
                            on=['symbol', 'exchange'],
                            how='left',
                            suffixes=('', '_pred')
                        )
                        
                        # Log merge results
                        logger.info(f"Merged data shape: {merged_df.shape}")
                        logger.info(f"Matched predictions: {merged_df['predicted_rate_pred'].notna().sum()} out of {len(merged_df)}")
                        
                        # Update original df with merged data
                        if 'predicted_rate_pred' in merged_df.columns:
                            df['predicted_rate'] = merged_df['predicted_rate_pred'].fillna(merged_df['funding_rate'])
                        else:
                            df['predicted_rate'] = df['funding_rate']
                            
                        if 'direction_pred' in merged_df.columns:
                            df['direction'] = merged_df['direction_pred'].fillna('neutral')
                        else:
                            df['direction'] = 'neutral'
                    else:
                        logger.warning(f"Missing required columns in predicted_df. Available columns: {predicted_df.columns.tolist()}")
                        df['predicted_rate'] = df['funding_rate']
                        df['direction'] = 'neutral'
                else:
                    logger.info("Using current rates as predictions (no predicted rates available)")
                    df['predicted_rate'] = df['funding_rate']
                    df['direction'] = 'neutral'
                
                # Calculate rate differences
                df['rate_diff'] = abs(df['predicted_rate'] - df['funding_rate'])
                
                # Set time_to_funding
                df['time_to_funding'] = df.apply(
                    lambda x: 1.0 if x['exchange'] == 'Hyperliquid' else 8.0,
                    axis=1
                )
                
                # Calculate opportunity score
                df['opportunity_score'] = df.apply(calculate_opportunity_score, axis=1)
                
                # Log successful processing
                logger.info(f"Successfully processed {len(df)} rows")
                logger.info(f"Columns after processing: {df.columns.tolist()}")
                logger.info(f"Top 5 opportunities: {df.nlargest(5, 'opportunity_score')[['symbol', 'exchange', 'funding_rate', 'predicted_rate', 'opportunity_score']].to_dict('records')}")
                
            except Exception as merge_error:
                logger.error(f"Error during merge/processing: {merge_error}")
                logger.error("Error details:", exc_info=True)
                # Fallback to using funding rates as predictions
                df['predicted_rate'] = df['funding_rate']
                df['direction'] = 'neutral'
                df['rate_diff'] = 0.0
                df['opportunity_score'] = df.apply(calculate_opportunity_score, axis=1)
            
            # Sort by opportunity score
            result_df = df.sort_values('opportunity_score', ascending=False)
            
            # Cache the result if caching is enabled
            if use_cache:
                try:
                    result_df.to_pickle(cache_file)
                    logger.info(f"Data cached to {cache_file}")
                except Exception as cache_error:
                    logger.warning(f"Failed to cache data: {cache_error}")
            
            return result_df
            
        except Exception as e:
            retry_count += 1
            if retry_count < max_retries:
                logger.warning(f"Retry {retry_count}/{max_retries} for fetch_data due to error: {e}")
                logger.warning("Error details:", exc_info=True)
                time.sleep(5)  # Wait 5 seconds before retrying
            else:
                logger.error(f"All {max_retries} retries failed with error: {e}")
                logger.error("Error details:", exc_info=True)
                return pd.DataFrame()

def calculate_stats(df: pd.DataFrame) -> dict:
    """Calculate statistics from the funding data with multiple timeframes"""
    if df.empty:
        return {}
    
    try:
        # Calculate base rates
        avg_rate = df['funding_rate'].mean()
        max_rate = df['funding_rate'].max()
        min_rate = df['funding_rate'].min()
        
        # Calculate timeframe rates
        hourly = avg_rate * 100
        eight_hour = hourly * 8
        daily = hourly * 24
        
        return {
            'total_markets': len(df),
            'binance_markets': len(df[df['exchange'] == 'Binance']),
            'hl_markets': len(df[df['exchange'] == 'Hyperliquid']),
            'avg_funding_rate': avg_rate,
            'max_funding_rate': max_rate,
            'min_funding_rate': min_rate,
            'hourly_rate': hourly,
            'eight_hour_rate': eight_hour,
            'daily_rate': daily,
            'timestamp': datetime.now()
        }
    except Exception as e:
        logger.error(f"Error calculating stats: {e}")
        return {}

def create_arbitrage_visualization(df):
    """Create visualization for cross-exchange arbitrage opportunities"""
    try:
        # Prepare data for arbitrage visualization
        binance_df = df[df['exchange'] == 'Binance'].copy()
        hl_df = df[df['exchange'] == 'Hyperliquid'].copy()
        
        # Standardize symbols
        binance_df['symbol'] = binance_df['symbol'].str.replace('USDT', '').str.replace('PERP', '').str.strip()
        hl_df['symbol'] = hl_df['symbol'].str.replace('USDT', '').str.replace('PERP', '').str.strip()
        
        # Find common symbols and create arbitrage data
        common_symbols = set(binance_df['symbol']) & set(hl_df['symbol'])
        
        arb_data = []
        
        for symbol in common_symbols:
            b_rate = float(binance_df[binance_df['symbol'] == symbol]['funding_rate'].iloc[0])
            h_rate = float(hl_df[hl_df['symbol'] == symbol]['funding_rate'].iloc[0])
            spread = b_rate - h_rate
            
            arb_data.append({
                'symbol': symbol,
                'binance_rate': b_rate,
                'hl_rate': h_rate,
                'spread': spread,
                'abs_spread': abs(spread)
            })
        
        if arb_data:
            arb_df = pd.DataFrame(arb_data)
            
            # Create scatter plot
            fig = go.Figure()
            
            # Add diagonal line for reference
            fig.add_trace(go.Scatter(
                x=[-0.1, 0.1],
                y=[-0.1, 0.1],
                mode='lines',
                name='Equal Rates',
                line=dict(color='rgba(128,128,128,0.5)', dash='dash'),
                showlegend=True
            ))
            
            # Add points
            fig.add_trace(go.Scatter(
                x=arb_df['binance_rate'],
                y=arb_df['hl_rate'],
                mode='markers+text',
                name='Trading Pairs',
                text=arb_df['symbol'],
                textposition="top center",
                marker=dict(
                    size=10,
                    color=arb_df['abs_spread'],
                    colorscale='RdYlGn',
                    showscale=True,
                    colorbar=dict(title='Spread %')
                ),
                hovertemplate=
                "<b>%{text}</b><br>" +
                "Binance Rate: %{x:.4f}%<br>" +
                "HL Rate: %{y:.4f}%<br>" +
                "Spread: %{marker.color:.4f}%<br>" +
                "<extra></extra>"
            ))
            
            fig.update_layout(
                title='Cross-Exchange Arbitrage Opportunities',
                title_x=0.5,
                xaxis_title='Binance Funding Rate (%)',
                yaxis_title='Hyperliquid Funding Rate (%)',
                template='plotly_dark',
                height=400,
                showlegend=True,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            
            return fig
            
    except Exception as e:
        logger.error(f"Error creating arbitrage visualization: {e}")
        return None

def create_visualizations(df):
    """Create visualization objects for the dashboard"""
    try:
        viz_data = {}
        
        # Current vs Predicted scatter plot
        viz_data['opportunity_scatter'] = px.scatter(
            df,
            x='funding_rate',
            y='predicted_rate',
            color='exchange',
            hover_data=['symbol', 'annualized_rate'],
            title='Current vs Predicted Funding Rates',
            template='plotly_dark'
        ).update_layout(
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        # Create arbitrage visualization
        viz_data['arb_scatter'] = create_arbitrage_visualization(df)
        
        # Store top opportunities
        viz_data['top_opportunities'] = df.copy()
        
        return viz_data
        
    except Exception as e:
        logger.error(f"Error creating visualizations: {e}")
        return {}

def create_exchange_comparison(df):
    """Create comparative visualization of funding rates between exchanges"""
    try:
        # Separate data by exchange
        binance_data = df[df['exchange'] == 'Binance']
        hl_data = df[df['exchange'] == 'Hyperliquid']
        
        # Create figure with secondary y-axis
        fig = go.Figure()
        
        # Add Hyperliquid distribution
        fig.add_trace(go.Violin(
            x=['Hyperliquid'] * len(hl_data),
            y=hl_data['funding_rate'],
            name='Hyperliquid',
            side='positive',
            line_color='rgba(0,128,255,0.7)',
            fillcolor='rgba(0,128,255,0.3)',
            points='all',
            jitter=0.05,
            box_visible=True,
            meanline_visible=True
        ))
        
        # Add Binance distribution
        fig.add_trace(go.Violin(
            x=['Binance'] * len(binance_data),
            y=binance_data['funding_rate'],
            name='Binance',
            side='positive',
            line_color='rgba(240,128,0,0.7)',
            fillcolor='rgba(240,128,0,0.3)',
            points='all',
            jitter=0.05,
            box_visible=True,
            meanline_visible=True
        ))
        
        # Add scatter points for actual values
        fig.add_trace(go.Scatter(
            x=['Hyperliquid'] * len(hl_data),
            y=hl_data['funding_rate'],
            mode='markers',
            name='HL Points',
            marker=dict(
                color='rgba(0,128,255,0.5)',
                size=4
            ),
            showlegend=False
        ))
        
        fig.add_trace(go.Scatter(
            x=['Binance'] * len(binance_data),
            y=binance_data['funding_rate'],
            mode='markers',
            name='Binance Points',
            marker=dict(
                color='rgba(240,128,0,0.5)',
                size=4
            ),
            showlegend=False
        ))
        
        # Update layout
        fig.update_layout(
            title='Funding Rate Distribution by Exchange',
            title_x=0.5,
            xaxis_title='Exchange',
            yaxis_title='Funding Rate (%)',
            template='plotly_dark',
            showlegend=True,
            height=500,
            violingap=0.2,
            violinmode='overlay',
            xaxis=dict(showgrid=False),
            yaxis=dict(
                gridcolor='rgba(128,128,128,0.2)',
                zerolinecolor='rgba(128,128,128,0.5)'
            ),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        # Add mean lines and annotations
        hl_mean = hl_data['funding_rate'].mean()
        binance_mean = binance_data['funding_rate'].mean()
        
        fig.add_hline(
            y=hl_mean,
            line_dash="dash",
            line_color="rgba(0,128,255,0.5)",
            annotation_text=f"HL Mean: {hl_mean:.4f}%"
        )
        
        fig.add_hline(
            y=binance_mean,
            line_dash="dash",
            line_color="rgba(240,128,0,0.5)",
            annotation_text=f"Binance Mean: {binance_mean:.4f}%"
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"Error creating exchange comparison: {e}")
        return None

def generate_hummingbot_config(df):
    """Generate Hummingbot configuration file"""
    try:
        # Filter and sort opportunities
        top_opportunities = df.nlargest(10, 'opportunity_score')
        
        config = {
            'template_version': 1,
            'strategy': 'perpetual_market_making',
            'exchange': 'hyperliquid_perpetual',
            'markets': [],
            'execution_timeframe': '8h',
            'position_mode': 'ONEWAY'
        }
        
        for _, token_data in top_opportunities.iterrows():
            market_config = {
                'market': f"{token_data['symbol']}-USDT",
                'leverage': 2,
                'position_size_quote': 100,
                'profitability_to_take_profit': max(0.01, abs(float(token_data['funding_rate'])) * 10),
                'funding_rate_diff_stop_loss': -abs(float(token_data['funding_rate'])),
                'trade_profitability_condition_to_enter': False
            }
            config['markets'].append(market_config)
        
        # Save config to file
        config_path = Path('generated_config.yml')
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        st.success(f"Config generated and saved to {config_path}")
        
        # Display config preview
        with st.expander("Preview Config"):
            st.code(yaml.dump(config, default_flow_style=False), language='yaml')
            
    except Exception as e:
        logger.error(f"Error generating config: {e}")
        st.error(f"Failed to generate config: {str(e)}")

def save_config_file(config: dict) -> str:
    """Save config to YAML file"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"config_arb_{timestamp}.yml"
        
        with open(filename, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
            
        return filename
    except Exception as e:
        logger.error(f"Error saving config: {e}")
        return ""

def push_to_supabase(df: pd.DataFrame, stats: dict, viz_data: dict):
    """Push analyzed data to Supabase tables"""
    if df.empty:
        logger.error("Cannot push empty DataFrame to Supabase")
        return False
        
    try:
        load_dotenv()
        supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        supabase_key = os.getenv("NEXT_PUBLIC_SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            logger.error("Missing Supabase credentials")
            return False
            
        # Initialize Supabase client with minimal parameters
        supabase = create_client(supabase_url, supabase_key)
        
        # Validate DataFrame columns
        required_columns = ['symbol', 'exchange', 'funding_rate', 'predicted_rate', 'rate_diff', 
                           'time_to_funding', 'direction', 'annualized_rate', 'opportunity_score', 'mark_price']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            logger.error(f"Missing required columns in DataFrame: {missing_columns}")
            return False
            
        # Prepare market data with proper type handling
        logger.info("Preparing market data for Supabase...")
        market_data = []
        timestamp = datetime.now().isoformat()
        
        for _, row in df.iterrows():
            try:
                market_data.append({
                    'symbol': str(row['symbol']),
                    'exchange': str(row['exchange']),
                    'funding_rate': float(row['funding_rate']),
                    'predicted_rate': float(row['predicted_rate']),
                    'rate_diff': float(row['rate_diff']),
                    'time_to_funding': float(row['time_to_funding']),
                    'direction': str(row['direction']),
                    'annualized_rate': float(row['annualized_rate']),
                    'opportunity_score': float(row['opportunity_score']),
                    'mark_price': float(row['mark_price']),
                    'suggested_position': "Long" if row['funding_rate'] < 0 else "Short",
                    'created_at': timestamp,
                })
            except Exception as row_error:
                logger.warning(f"Error processing row for Supabase: {row_error}")
                continue
        
        if not market_data:
            logger.error("No valid market data to push to Supabase")
            return False
            
        logger.info(f"Pushing {len(market_data)} market records to Supabase...")
        
        # Push market snapshot in batches to avoid payload size issues
        batch_size = 100
        success_count = 0
        
        for i in range(0, len(market_data), batch_size):
            batch = market_data[i:i+batch_size]
            try:
                response = supabase.table('funding_market_snapshots').insert(batch).execute()
                success_count += len(batch)
                logger.info(f"Pushed batch {i//batch_size + 1} with {len(batch)} market records")
            except Exception as batch_error:
                logger.error(f"Error pushing batch {i//batch_size + 1} to Supabase: {batch_error}")
                
        if success_count == 0:
            logger.error("Failed to push any market records to Supabase")
            return False
            
        logger.info(f"Successfully pushed {success_count}/{len(market_data)} market records to Supabase")
        
        # Push statistics
        if not stats:
            logger.warning("No statistics to push to Supabase")
        else:
            try:
                stats_data = {
                    'total_markets': int(stats.get('total_markets', 0)),
                    'binance_markets': int(stats.get('binance_markets', 0)),
                    'hl_markets': int(stats.get('hl_markets', 0)),
                    'hourly_rate': float(stats.get('hourly_rate', 0.0)),
                    'eight_hour_rate': float(stats.get('eight_hour_rate', 0.0)),
                    'daily_rate': float(stats.get('daily_rate', 0.0)),
                    'created_at': timestamp
                }
                
                response = supabase.table('funding_statistics').insert(stats_data).execute()
                logger.info("Successfully pushed statistics to Supabase")
            except Exception as stats_error:
                logger.error(f"Error pushing statistics to Supabase: {stats_error}")
        
        # Push top opportunities
        if 'top_opportunities' not in viz_data or viz_data['top_opportunities'].empty:
            logger.warning("No top opportunities to push to Supabase")
        else:
            try:
                top_opps = []
                for _, row in viz_data['top_opportunities'].iterrows():
                    try:
                        top_opps.append({
                            'symbol': str(row['symbol']),
                            'exchange': str(row['exchange']),
                            'funding_rate': float(row['funding_rate']),
                            'predicted_rate': float(row['predicted_rate']),
                            'opportunity_score': float(row['opportunity_score']),
                            'created_at': timestamp
                        })
                    except Exception as row_error:
                        logger.warning(f"Error processing top opportunity for Supabase: {row_error}")
                        continue
                
                if top_opps:
                    response = supabase.table('funding_top_opportunities').insert(top_opps).execute()
                    logger.info(f"Successfully pushed {len(top_opps)} top opportunities to Supabase")
                else:
                    logger.warning("No valid top opportunities to push to Supabase")
            except Exception as opps_error:
                logger.error(f"Error pushing top opportunities to Supabase: {opps_error}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error pushing to Supabase: {e}")
        logger.error("Error details:", exc_info=True)
        return False

def test_supabase_query():
    """Test direct SQL query to Supabase"""
    try:
        load_dotenv()
        supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        supabase_key = os.getenv("NEXT_PUBLIC_SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            logger.error("Missing Supabase credentials")
            return pd.DataFrame()
            
        # Initialize Supabase client with minimal parameters
        supabase = create_client(supabase_url, supabase_key)
        
        # Direct SQL query
        query = """
        select 
            asset,
            exchange,
            predicted_rate,
            created_at,
            direction
        from predicted_funding_rates
        where created_at > now() - interval '1 hour'
        order by created_at desc
        limit 10;
        """
        
        response = supabase.table('predicted_funding_rates').select("*").execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        logger.error(f"SQL query test failed: {e}")
        return pd.DataFrame()

def main():
    try:
        # Add auto-refresh meta tag at the top of the app
        st.set_page_config(
            page_title="Funding Rate Dashboard",
            page_icon="📊",
            layout="wide",
            menu_items={
                'About': 'Funding Rate Analysis Dashboard - Real-time funding rate analysis for crypto perpetual futures'
            }
        )
        
        # Custom CSS for better styling
        st.markdown("""
        <style>
        .main-header {
            font-size: 2.5rem;
            font-weight: 700;
            color: #4CAF50;
            text-align: center;
            margin-bottom: 1rem;
        }
        .sub-header {
            font-size: 1.5rem;
            font-weight: 500;
            color: #2196F3;
            margin-bottom: 0.5rem;
        }
        .info-text {
            font-size: 1rem;
            color: #757575;
        }
        .highlight {
            background-color: rgba(76, 175, 80, 0.1);
            padding: 1rem;
            border-radius: 0.5rem;
            border-left: 5px solid #4CAF50;
        }
        .warning {
            background-color: rgba(255, 152, 0, 0.1);
            padding: 1rem;
            border-radius: 0.5rem;
            border-left: 5px solid #FF9800;
        }
        .error {
            background-color: rgba(244, 67, 54, 0.1);
            padding: 1rem;
            border-radius: 0.5rem;
            border-left: 5px solid #F44336;
        }
        #auto-refresh-status {
            position: fixed;
            top: 10px;
            right: 10px;
            z-index: 999;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Add auto-refresh using HTML
        st.markdown(
            """
            <meta http-equiv="refresh" content="300">
            """,
            unsafe_allow_html=True
        )
        
        # Display header
        st.markdown('<div class="main-header">Crypto Funding Rate Dashboard</div>', unsafe_allow_html=True)
        st.markdown('<div class="info-text">Real-time analysis of funding rates across major exchanges</div>', unsafe_allow_html=True)
        
        # Initialize session state for refresh tracking
        if 'last_refresh' not in st.session_state:
            st.session_state.last_refresh = time.time()
            st.session_state.refresh_count = 0
        
        # Calculate time until next refresh
        time_since_refresh = time.time() - st.session_state.last_refresh
        time_until_refresh = max(0, 300 - time_since_refresh)  # 300 seconds = 5 minutes
        
        # Display refresh status in sidebar
        st.sidebar.markdown('<div class="sub-header">Dashboard Status</div>', unsafe_allow_html=True)
        
        refresh_col1, refresh_col2 = st.sidebar.columns(2)
        with refresh_col1:
            st.markdown(f"**Next refresh in:**")
        with refresh_col2:
            st.markdown(f"**{int(time_until_refresh)} seconds**")
            
        count_col1, count_col2 = st.sidebar.columns(2)
        with count_col1:
            st.markdown(f"**Refresh count:**")
        with count_col2:
            st.markdown(f"**{st.session_state.refresh_count}**")
        
        st.sidebar.markdown("---")
        
        # Environment check
        if not load_environment():
            st.error("❌ Failed to load environment variables. Please check your .env file.")
            st.stop()
        
        # Check if manual refresh button was clicked
        manual_refresh = st.button("🔄 Refresh Data Now", key="manual_refresh")
        if manual_refresh:
            st.session_state._manual_refresh = True
        
        # Run analysis with progress and error handling
        if ('df' not in st.session_state or 
            manual_refresh or 
            should_refresh):
            
            # Update refresh tracking
            st.session_state.last_refresh = time.time()
            st.session_state.refresh_count += 1
            
            with st.spinner("🔄 Fetching latest funding rate data..."):
                try:
                    # Use cache for auto-refresh, but not for manual refresh
                    use_cache = not st.session_state.get('_manual_refresh', False)
                    df = fetch_data(use_cache=use_cache)
                    
                    # Reset manual refresh flag
                    st.session_state._manual_refresh = False
                    
                    if not df.empty:
                        st.session_state.df = df
                        st.session_state.stats = calculate_stats(df)
                        st.session_state.last_update = datetime.now()
                        
                        # Create visualizations
                        viz_data = create_visualizations(df)
                        
                        # Push data to Supabase
                        with st.spinner("📤 Updating database..."):
                            if push_to_supabase(df, st.session_state.stats, viz_data):
                                st.success("✅ Data successfully updated in database")
                            else:
                                st.warning("⚠️ Failed to update database, but analysis will continue")
                        
                        st.session_state.viz_data = viz_data
                    else:
                        st.error("❌ No data retrieved from exchanges")
                        st.markdown('<div class="error">Failed to fetch funding rate data from exchanges. Please check the logs for details.</div>', unsafe_allow_html=True)
                        if st.button("🔁 Retry", key="retry_fetch"):
                            st.rerun()
                        return
                except Exception as e:
                    logger.error(f"Error fetching data: {e}")
                    logger.error("Error details:", exc_info=True)
                    st.error(f"❌ Error fetching data: {str(e)}")
                    st.markdown(f'<div class="error">An error occurred while fetching data: {str(e)}</div>', unsafe_allow_html=True)
                    if st.button("🔁 Retry", key="retry_error"):
                        st.rerun()
                    return

        # Display last update time
        if 'last_update' in st.session_state:
            st.sidebar.markdown('<div class="sub-header">Data Status</div>', unsafe_allow_html=True)
            st.sidebar.markdown(f"**Last updated:** {st.session_state.last_update.strftime('%Y-%m-%d %H:%M:%S')}")

        # Display data if available
        if 'df' in st.session_state and not st.session_state.df.empty:
            try:
                # Display metrics
                stats = st.session_state.stats
                st.markdown('<div class="sub-header">Market Overview</div>', unsafe_allow_html=True)
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "Total Markets", 
                        f"{stats['total_markets']}",
                        f"{stats['binance_markets']} Binance / {stats['hl_markets']} HL"
                    )
                with col2:
                    st.metric(
                        "1H Funding Rate",
                        f"{stats['hourly_rate']:.4f}%",
                        f"{stats['hourly_rate']*365*24:.1f}% APR"
                    )
                with col3:
                    st.metric(
                        "8H Funding Rate",
                        f"{stats['eight_hour_rate']:.4f}%",
                        f"{stats['eight_hour_rate']*365/8:.1f}% APR"
                    )
                with col4:
                    st.metric(
                        "24H Funding Rate",
                        f"{stats['daily_rate']:.4f}%",
                        f"{stats['daily_rate']*365/24:.1f}% APR"
                    )

                # Create tabs
                tab1, tab2, tab3, tab4 = st.tabs([
                    "🎯 Top Opportunities",
                    "📊 Market Analysis",
                    "🔄 Cross-Exchange",
                    "🔍 Detailed View"
                ])
                
                with tab1:
                    display_top_opportunities(st.session_state.viz_data.get('top_opportunities', pd.DataFrame()))
                    
                with tab2:
                    display_directional_opportunities(st.session_state.df)
                    
                with tab3:
                    display_cross_exchange_opportunities(st.session_state.df)
                    
                with tab4:
                    display_detailed_view(st.session_state.df)
                
                # Add config generation option
                st.sidebar.markdown('<div class="sub-header">Tools</div>', unsafe_allow_html=True)
                if st.sidebar.button("Generate Hummingbot Config"):
                    generate_hummingbot_config(st.session_state.df)
                    
                # Add data download option
                if st.sidebar.button("Download Data as CSV"):
                    csv = st.session_state.df.to_csv(index=False)
                    st.sidebar.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name=f"funding_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                
            except Exception as e:
                logger.error(f"Error displaying dashboard: {e}")
                logger.error("Error details:", exc_info=True)
                st.error(f"❌ Error displaying dashboard: {str(e)}")
                st.markdown(f'<div class="error">An error occurred while displaying the dashboard: {str(e)}</div>', unsafe_allow_html=True)
        else:
            st.warning("⚠️ No data available. Please refresh to fetch the latest data.")
            
        # Add footer
        st.markdown("---")
        st.markdown('<div class="info-text" style="text-align: center;">Funding Rate Dashboard | Data refreshes every 5 minutes</div>', unsafe_allow_html=True)
            
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        logger.error("Error details:", exc_info=True)
        st.error(f"❌ Application error: {str(e)}")
        st.markdown(f'<div class="error">An unexpected error occurred: {str(e)}</div>', unsafe_allow_html=True)

def display_top_opportunities(top_opps):
    """Display both directional and cross-exchange funding opportunities side by side"""
    if not top_opps.empty:
        st.subheader("💰 Top Funding Rate Opportunities")
        
        # Create two columns for side-by-side display
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🎯 Directional Opportunities")
            display_directional_opportunities(top_opps)
            
        with col2:
            st.markdown("#### 🔄 Cross-Exchange Arbitrage")
            display_cross_exchange_opportunities(top_opps)

def display_directional_opportunities(df):
    """Display best single-direction funding rate opportunities"""
    directional_df = df.copy()
    
    # Calculate absolute funding rate for sorting
    directional_df['abs_funding_rate'] = directional_df['funding_rate'].abs()
    
    # Sort by absolute funding rate and get top 25
    directional_df = directional_df.nlargest(25, 'abs_funding_rate')
    
    # Format for display
    display_df = directional_df[[
        'symbol',
        'exchange',
        'funding_rate',
        'predicted_rate',
        'time_to_funding',
        'annualized_rate'
    ]].copy()
    
    # Add suggested position
    display_df['position'] = display_df.apply(
        lambda x: "🟢 Long" if x['funding_rate'] < 0 else "🔴 Short", 
        axis=1
    )
    
    # Reorder columns for better display
    display_df = display_df[[
        'symbol',
        'position',
        'funding_rate',
        'predicted_rate',
        'annualized_rate',
        'exchange',
        'time_to_funding'
    ]]
    
    st.dataframe(
        display_df.style.format({
            'funding_rate': '{:.4f}%',
            'predicted_rate': '{:.4f}%',
            'annualized_rate': '{:.2f}%',
            'time_to_funding': '{:.1f}h'
        }).background_gradient(
            subset=['funding_rate', 'annualized_rate'],
            cmap='RdYlGn'
        ).set_properties(**{
            'text-align': 'center'
        }).set_table_styles([
            {'selector': 'th', 'props': [('text-align', 'center')]},
            {'selector': 'td', 'props': [('text-align', 'center')]}
        ]),
        use_container_width=True,
        height=600  # Increased height for 25 rows
    )

def display_cross_exchange_opportunities(df):
    """Display cross-exchange funding rate arbitrage opportunities"""
    try:
        # Prepare data
        binance_df = df[df['exchange'] == 'Binance'].copy()
        hl_df = df[df['exchange'] == 'Hyperliquid'].copy()
        
        # Standardize symbols
        binance_df['symbol'] = binance_df['symbol'].str.replace('USDT', '').str.replace('PERP', '').str.strip()
        hl_df['symbol'] = hl_df['symbol'].str.replace('USDT', '').str.replace('PERP', '').str.strip()
        
        common_symbols = set(binance_df['symbol']) & set(hl_df['symbol'])
        
        arb_opportunities = []
        
        for symbol in common_symbols:
            try:
                b_data = binance_df[binance_df['symbol'] == symbol].iloc[0]
                h_data = hl_df[hl_df['symbol'] == symbol].iloc[0]
                
                # Calculate spread
                spread = float(b_data['funding_rate']) - float(h_data['funding_rate'])
                
                if abs(spread) > 0.0001:  # Only include meaningful spreads
                    arb_opportunities.append({
                        'symbol': symbol,
                        'spread': spread,
                        'binance': b_data['funding_rate'],
                        'hyperliquid': h_data['funding_rate'],
                        'strategy': "🟢 Long Bin/Short HL" if spread < 0 else "🔴 Short Bin/Long HL",
                        'annual_return': abs(spread) * 365 * 24
                    })
                
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
                continue
        
        if arb_opportunities:
            arb_df = pd.DataFrame(arb_opportunities)
            arb_df = arb_df.sort_values('annual_return', ascending=False).head(25)  # Show top 25
            
            # Reorder columns for better display
            arb_df = arb_df[[
                'symbol',
                'strategy',
                'spread',
                'binance',
                'hyperliquid',
                'annual_return'
            ]]
            
            st.dataframe(
                arb_df.style.format({
                    'spread': '{:.4f}%',
                    'binance': '{:.4f}%',
                    'hyperliquid': '{:.4f}%',
                    'annual_return': '{:.2f}%'
                }).background_gradient(
                    subset=['spread', 'annual_return'],
                    cmap='RdYlGn'
                ).set_properties(**{
                    'text-align': 'center'
                }).set_table_styles([
                    {'selector': 'th', 'props': [('text-align', 'center')]},
                    {'selector': 'td', 'props': [('text-align', 'center')]}
                ]),
                use_container_width=True,
                height=600  # Increased height for 25 rows
            )
        else:
            st.info("No significant cross-exchange opportunities found")
            
    except Exception as e:
        logger.error(f"Error in cross-exchange opportunities: {e}")
        st.error("Error calculating cross-exchange opportunities")

def display_detailed_view(df):
    """Display enhanced detailed view of all data"""
    try:
        if not df.empty:
            # Prepare display dataframe
            display_df = df.copy()
            
            # Add formatted columns
            display_df['rate_diff'] = (display_df['predicted_rate'] - display_df['funding_rate']).abs()
            display_df['next_funding'] = display_df['time_to_funding'].apply(
                lambda x: f"{x:.1f}h" if pd.notnull(x) else "8h"
            )
            display_df['suggested_position'] = display_df.apply(
                lambda x: "Long" if x['funding_rate'] < 0 else "Short", 
                axis=1
            )
            
            # Sort by opportunity score
            display_df = display_df.sort_values('opportunity_score', ascending=False)
            
            # Display with formatting
            st.dataframe(
                display_df[[
                    'symbol',
                    'exchange',
                    'funding_rate',
                    'predicted_rate',
                    'rate_diff',
                    'next_funding',
                    'direction',
                    'suggested_position',
                    'annualized_rate',
                    'opportunity_score',
                    'mark_price'
                ]].style.format({
                    'funding_rate': '{:.6f}',
                    'predicted_rate': '{:.6f}',
                    'rate_diff': '{:.6f}',
                    'annualized_rate': '{:.2f}%',
                    'opportunity_score': '{:.2f}',
                    'mark_price': '${:,.2f}'
                }).background_gradient(
                    subset=['opportunity_score'],
                    cmap='RdYlGn'
                ).background_gradient(
                    subset=['rate_diff'],
                    cmap='YlOrRd',
                    vmin=0,
                    vmax=0.0001  # Set a maximum value for the gradient 
                )
            )
    except Exception as e:
        logger.error(f"Error in detailed view: {e}")
        st.error("Error displaying detailed view")

# Add a scheduled refresh function that can be called externally
def scheduled_refresh():
    """Function to be called by external scheduler to refresh data"""
    start_time = time.time()
    logger.info("=== Starting scheduled data refresh ===")
    
    try:
        # Load environment variables
        if not load_environment():
            logger.error("Failed to load environment variables")
            return False
            
        # Check Supabase connection
        if not check_supabase_connection():
            logger.error("Failed to connect to Supabase")
            return False
            
        # Fetch data with caching enabled but with fewer retries for scheduled runs
        logger.info("Fetching latest data...")
        df = fetch_data(use_cache=True, max_retries=3)
        
        if df.empty:
            logger.error("No data retrieved during scheduled refresh")
            return False
            
        # Calculate statistics
        logger.info("Calculating statistics...")
        stats = calculate_stats(df)
        
        # Create visualizations
        logger.info("Creating visualizations...")
        viz_data = create_visualizations(df)
        
        # Push to Supabase
        logger.info("Pushing data to Supabase...")
        success = push_to_supabase(df, stats, viz_data)
        
        if success:
            elapsed_time = time.time() - start_time
            logger.info(f"Scheduled refresh completed successfully in {elapsed_time:.2f} seconds")
            logger.info(f"Processed {len(df)} market records")
            
            # Save a backup of the data
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = f"funding_data_backup_{timestamp}.pkl"
                df.to_pickle(backup_file)
                logger.info(f"Created data backup: {backup_file}")
                
                # Clean up old backups (keep only the 5 most recent)
                backup_files = sorted([f for f in os.listdir('.') if f.startswith('funding_data_backup_')])
                if len(backup_files) > 5:
                    for old_file in backup_files[:-5]:
                        try:
                            os.remove(old_file)
                            logger.info(f"Removed old backup: {old_file}")
                        except Exception as rm_error:
                            logger.warning(f"Could not remove old backup {old_file}: {rm_error}")
            except Exception as backup_error:
                logger.warning(f"Failed to create data backup: {backup_error}")
            
            return True
        else:
            logger.error("Failed to push data to Supabase during scheduled refresh")
            return False
            
    except Exception as e:
        logger.error(f"Error during scheduled refresh: {e}")
        logger.error("Error details:", exc_info=True)
        return False
    finally:
        logger.info("=== Scheduled refresh process completed ===")
        
        # Log memory usage
        try:
            import psutil
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            logger.info(f"Memory usage: {memory_info.rss / 1024 / 1024:.2f} MB")
        except ImportError:
            logger.info("psutil not installed, skipping memory usage logging")
        except Exception as mem_error:
            logger.warning(f"Failed to log memory usage: {mem_error}")

if __name__ == "__main__":
    # Check for command line arguments
    parser = argparse.ArgumentParser(description='Funding Rate Analysis Dashboard')
    parser.add_argument('--scheduled', action='store_true', help='Run in scheduled mode (no UI)')
    args = parser.parse_args()
    
    if args.scheduled:
        # Run in scheduled mode
        print("Running in scheduled mode...")
        success = scheduled_refresh()
        sys.exit(0 if success else 1)
    else:
        # Run in normal UI mode
        main() 