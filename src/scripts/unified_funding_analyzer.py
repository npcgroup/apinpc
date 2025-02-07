import asyncio
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import logging
from supabase import create_client
import os
from dotenv import load_dotenv
from advanced_funding_analyzer import AdvancedFundingAnalyzer
from enhanced_funding_crawler import EnhancedFundingCrawler
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from rich.console import Console
import numpy as np

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
console = Console()

class UnifiedFundingAnalyzer:
    def __init__(self):
        load_dotenv()
        # Initialize Supabase client
        self.supabase = create_client(
            os.getenv("NEXT_PUBLIC_SUPABASE_URL"),
            os.getenv("NEXT_PUBLIC_SUPABASE_KEY")
        )
        self.funding_analyzer = AdvancedFundingAnalyzer()
        self.funding_crawler = EnhancedFundingCrawler()
        self._cache = {}
        self._last_update = None
        self._cache_duration = timedelta(minutes=1)  # Cache data for 1 minute

    async def get_predicted_rates_from_supabase(self) -> pd.DataFrame:
        """Fetch latest predicted funding rates from Supabase with caching"""
        cache_key = 'predicted_rates'
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]

        try:
            response = (self.supabase.table('predicted_funding_rates')
                .select('*')
                .order('created_at', desc=True)
                .limit(100)  # Reduced limit for faster response
                .execute())
            
            if response.data:
                df = pd.DataFrame(response.data)
                df['created_at'] = pd.to_datetime(df['created_at'])
                df['next_funding_time'] = pd.to_datetime(df['next_funding_time'])
                self._update_cache(cache_key, df)
                return df
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error fetching predicted rates: {e}")
            return self._cache.get(cache_key, pd.DataFrame())

    def _is_cache_valid(self, key: str) -> bool:
        """Check if cached data is still valid"""
        if key not in self._cache or key not in self._last_update:
            return False
        return datetime.now() - self._last_update[key] < self._cache_duration

    def _update_cache(self, key: str, data: pd.DataFrame):
        """Update cache with new data"""
        self._cache[key] = data
        self._last_update = self._last_update or {}
        self._last_update[key] = datetime.now()

    async def get_arbitrage_opportunities(self) -> pd.DataFrame:
        """Fetch latest arbitrage opportunities from Supabase"""
        try:
            response = (self.supabase.table('funding_arbitrage_opportunities')
                .select('*')
                .order('timestamp', desc=True)
                .limit(100)  # Reduced limit for faster response
                .execute())
            
            if response.data:
                df = pd.DataFrame(response.data)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                return df
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error fetching arbitrage opportunities: {e}")
            return pd.DataFrame()

    def get_realtime_rates(self) -> pd.DataFrame:
        """Get real-time funding rates using AdvancedFundingAnalyzer"""
        try:
            # Get both Binance and Hyperliquid rates
            analyzer = self.funding_analyzer
            
            binance_rates = analyzer.get_binance_all_rates()
            hyperliquid_rates = analyzer.get_hyperliquid_all_rates()
            
            # Combine rates
            all_rates = binance_rates + hyperliquid_rates
            
            if not all_rates:
                logger.warning("No realtime rates available")
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(all_rates)
            
            # Ensure required columns exist
            required_columns = ['symbol', 'exchange', 'funding_rate']
            for col in required_columns:
                if col not in df.columns:
                    df[col] = None
            
            return df
        
        except Exception as e:
            logger.error(f"Error getting real-time rates: {e}")
            return pd.DataFrame()

    def combine_data(self, realtime_df: pd.DataFrame, predicted_df: pd.DataFrame, 
                    arbitrage_df: pd.DataFrame) -> pd.DataFrame:
        """Combine real-time and predicted data with arbitrage opportunities"""
        try:
            # If no realtime data, try to use predicted data
            if realtime_df.empty and not predicted_df.empty:
                logger.info("Using predicted rates as base data")
                realtime_df = predicted_df.copy()
                realtime_df['funding_rate'] = realtime_df['predicted_rate']
            
            if realtime_df.empty:
                logger.warning("No data available to combine")
                return pd.DataFrame()

            # Ensure predicted_df has the required columns
            if not predicted_df.empty:
                # Rename columns to match if needed
                predicted_df = predicted_df.rename(columns={
                    'asset': 'symbol',
                    'predicted_funding_rate': 'predicted_rate'
                })
                
                # Ensure required columns exist
                required_columns = ['symbol', 'exchange', 'predicted_rate']
                if not all(col in predicted_df.columns for col in required_columns):
                    logger.warning("Predicted rates dataframe missing required columns")
                    predicted_df['predicted_rate'] = 0.0
                    predicted_df['exchange'] = predicted_df.get('exchange', 'Unknown')

            # Create base dataframe from realtime data
            combined_df = realtime_df.copy()
            combined_df['predicted_rate'] = 0.0  # Default value

            # Add predicted rates if available
            if not predicted_df.empty:
                try:
                    # Merge on both symbol and exchange
                    predicted_rates = predicted_df[['symbol', 'exchange', 'predicted_rate']].drop_duplicates()
                    combined_df = combined_df.merge(
                        predicted_rates,
                        on=['symbol', 'exchange'],
                        how='left'
                    )
                    combined_df['predicted_rate'] = combined_df['predicted_rate'].fillna(0.0)
                except Exception as e:
                    logger.error(f"Error merging predicted rates: {e}")
                    combined_df['predicted_rate'] = 0.0

            # Add arbitrage metrics if available
            if not arbitrage_df.empty:
                try:
                    latest_arbitrage = arbitrage_df.sort_values('timestamp').groupby('coin').last()
                    combined_df = combined_df.merge(
                        latest_arbitrage[['priority_score', 'market_size', 'volume_24h']],
                        left_on='symbol',
                        right_index=True,
                        how='left'
                    )
                except Exception as e:
                    logger.error(f"Error merging arbitrage data: {e}")

            # Fill NaN values
            combined_df['priority_score'] = combined_df.get('priority_score', 0.0).fillna(0.0)
            combined_df['market_size'] = combined_df.get('market_size', 0.0).fillna(0.0)
            combined_df['volume_24h'] = combined_df.get('volume_24h', 0.0).fillna(0.0)

            # Calculate additional metrics
            combined_df['annualized_rate'] = combined_df['funding_rate'] * 365 * 100
            combined_df['opportunity_score'] = combined_df.apply(
                lambda x: self.calculate_opportunity_score(x), axis=1
            )

            return combined_df
        except Exception as e:
            logger.error(f"Error combining data: {e}")
            return pd.DataFrame()

    def calculate_opportunity_score(self, row: pd.Series) -> float:
        """Calculate comprehensive opportunity score"""
        try:
            weights = {
                'current_rate': 0.3,
                'predicted_rate': 0.2,
                'volume': 0.25,
                'market_size': 0.25
            }

            # Normalize values
            current_rate_norm = abs(row.get('funding_rate', 0))
            predicted_rate_norm = abs(row.get('predicted_rate', 0))
            volume_norm = min(row.get('volume_24h', 0) / 1e8, 1)
            market_size_norm = min(row.get('market_size', 0) / 1e8, 1)

            score = (
                current_rate_norm * weights['current_rate'] +
                predicted_rate_norm * weights['predicted_rate'] +
                volume_norm * weights['volume'] +
                market_size_norm * weights['market_size']
            )

            return score
        except Exception as e:
            logger.error(f"Error calculating opportunity score: {e}")
            return 0.0

    async def get_unified_analysis(self) -> Tuple[pd.DataFrame, Dict]:
        """Get unified analysis with improved performance"""
        try:
            logger.info("Starting unified analysis...")
            
            # Run data fetching concurrently
            tasks = [
                asyncio.create_task(self.get_predicted_rates_from_supabase()),
                asyncio.create_task(self.get_arbitrage_opportunities())
            ]
            
            # Get realtime rates while waiting for async tasks
            logger.info("Fetching realtime rates...")
            realtime_df = self.get_realtime_rates()
            logger.info(f"Got realtime rates: {len(realtime_df)} rows")
            
            # Wait for all async tasks to complete
            logger.info("Waiting for async tasks...")
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results with detailed logging
            predicted_df = results[0] if isinstance(results[0], pd.DataFrame) else pd.DataFrame()
            arbitrage_df = results[1] if isinstance(results[1], pd.DataFrame) else pd.DataFrame()
            
            logger.info(f"Got predicted rates: {len(predicted_df)} rows")
            logger.info(f"Got arbitrage opportunities: {len(arbitrage_df)} rows")

            # Combine all data
            unified_df = self.combine_data(realtime_df, predicted_df, arbitrage_df)
            logger.info(f"Combined data: {len(unified_df)} rows")

            if unified_df.empty:
                logger.warning("Combined DataFrame is empty!")
                return pd.DataFrame(), {}

            # Calculate market statistics
            stats = {
                'total_markets': len(unified_df),
                'total_volume_24h': unified_df['volume_24h'].sum() if 'volume_24h' in unified_df else 0,
                'avg_funding_rate': unified_df['funding_rate'].mean() if 'funding_rate' in unified_df else 0,
                'max_opportunity_score': unified_df['opportunity_score'].max() if 'opportunity_score' in unified_df else 0,
                'timestamp': datetime.now()
            }
            
            logger.info("Analysis complete successfully")
            return unified_df, stats

        except Exception as e:
            logger.error(f"Error in unified analysis: {e}", exc_info=True)
            return pd.DataFrame(), {
                'total_markets': 0,
                'total_volume_24h': 0,
                'avg_funding_rate': 0,
                'max_opportunity_score': 0,
                'timestamp': datetime.now()
            }

    def create_visualization_data(self, df: pd.DataFrame) -> Dict:
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
                    size='opportunity_score',
                    hover_data=['symbol', 'annualized_rate'],
                    title='Funding Rate Opportunities'
                ),
                'top_opportunities': df.nlargest(10, 'opportunity_score'),
                'market_heatmap': px.density_heatmap(
                    df,
                    x='funding_rate',
                    y='predicted_rate',
                    title='Funding Rate Density'
                )
            }
        except Exception as e:
            logger.error(f"Error creating visualization data: {e}")
            return {}

async def main():
    """Main function to run the unified analyzer"""
    analyzer = UnifiedFundingAnalyzer()
    unified_df, stats = await analyzer.get_unified_analysis()
    return unified_df, stats

if __name__ == "__main__":
    asyncio.run(main()) 