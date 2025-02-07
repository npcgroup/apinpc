import json
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import seaborn as sns
import matplotlib.pyplot as plt
from supabase import create_client
from dotenv import load_dotenv
import os
import warnings
warnings.filterwarnings('ignore')
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from scipy import stats
import statsmodels.api as sm
from statsmodels.tsa.seasonal import seasonal_decompose

# Initialize Supabase connection
load_dotenv()
supabase = create_client(
    os.getenv("NEXT_PUBLIC_SUPABASE_URL"),
    os.getenv("NEXT_PUBLIC_SUPABASE_KEY")
)

def safe_datetime_convert(df, time_columns=['timestamp', 'created_at', 'next_funding_time']):
    """Safely convert time columns to datetime if they exist"""
    for col in time_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col])
    return df

def fetch_all_records(table_name, page_size=1000):
    """Fetch all records from a table using pagination"""
    try:
        all_records = []
        last_id = 0
        
        while True:
            response = supabase.table(table_name)\
                .select('*')\
                .order('id')\
                .gt('id', last_id)\
                .limit(page_size)\
                .execute()
                
            if not response.data:
                break
                
            all_records.extend(response.data)
            last_record_id = response.data[-1]['id']
            
            if len(response.data) < page_size:
                break
                
            last_id = last_record_id
            
        if not all_records:
            print(f"No data found in {table_name}")
            return pd.DataFrame()
            
        df = pd.DataFrame(all_records)
        print(f"Fetched {len(df)} records from {table_name}")
        return safe_datetime_convert(df)
        
    except Exception as e:
        print(f"Error fetching data from {table_name}: {e}")
        return pd.DataFrame()

def fetch_top_opportunities():
    """Fetch all funding opportunities from Supabase"""
    return fetch_all_records('funding_top_opportunities')

def fetch_rate_snapshots():
    """Fetch all funding rate snapshots"""
    return fetch_all_records('funding_rate_snapshots')

def fetch_market_snapshots():
    """Fetch all market snapshots"""
    return fetch_all_records('binance_market_data')

def fetch_funding_statistics():
    """Fetch all funding statistics"""
    return fetch_all_records('funding_statistics')

def fetch_funding_market_snapshots():
    """Fetch all funding market snapshots"""
    return fetch_all_records('funding_market_snapshots')

def fetch_binance_funding():
    """Fetch all Binance funding rates"""
    return fetch_all_records('binance_funding_rates')

def fetch_binance_market():
    """Fetch all Binance market data"""
    return fetch_all_records('binance_market_data')

def fetch_hyperliquid_funding():
    """Fetch all Hyperliquid funding rates"""
    return fetch_all_records('hyperliquid_funding_rates')

def fetch_predicted_funding_rates():
    """Fetch all predicted funding rates"""
    return fetch_all_records('predicted_funding_rates')

# Main analysis
print("Loading data from Supabase...")

# Load all dataframes
dfs = {
    'top_opportunities': fetch_top_opportunities(),
    'rate_snapshots': fetch_rate_snapshots(),
    'market_snapshots': fetch_market_snapshots(),
    'funding_stats': fetch_funding_statistics(),
    'binance_funding': fetch_binance_funding(),
    'binance_market': fetch_binance_market(),
    'hyperliquid_funding': fetch_hyperliquid_funding(),
    'funding_market_snapshots': fetch_funding_market_snapshots(),
    'predicted_rates': fetch_predicted_funding_rates()
}

# Check which dataframes have data
for name, df in dfs.items():
    if df.empty:
        print(f"Warning: No data available for {name}")
    else:
        print(f"Successfully loaded {len(df)} records for {name}")

# Only proceed with analysis if we have data
if all(df.empty for df in dfs.values()):
    print("No data available for analysis")
    exit()

# 2. Cross-Exchange Analysis
print("\n=== Cross-Exchange Analysis ===")
if not dfs['binance_funding'].empty and not dfs['hyperliquid_funding'].empty:
    # Combine Binance and Hyperliquid data for comparison
    binance_funding_df = dfs['binance_funding']
    hyperliquid_funding_df = dfs['hyperliquid_funding']
    
    binance_funding_df['exchange'] = 'Binance'
    hyperliquid_funding_df['exchange'] = 'Hyperliquid'
    
    required_cols = ['symbol', 'funding_rate', 'timestamp', 'exchange']
    if all(col in binance_funding_df.columns for col in required_cols) and \
       all(col in hyperliquid_funding_df.columns for col in required_cols):
        combined_funding = pd.concat([
            binance_funding_df[required_cols],
            hyperliquid_funding_df[required_cols]
        ])

        exchange_stats = combined_funding.groupby('exchange').agg({
            'funding_rate': ['mean', 'std', 'count'],
            'symbol': 'nunique'
        }).round(6)

        print("\nExchange Statistics:")
        print(exchange_stats)
    else:
        print("Missing required columns for cross-exchange analysis")

# Continue with rest of the analysis only if relevant data is available...
# (Rest of your analysis code with appropriate error checking)

# Save analysis results
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
analysis_results = {
    'timestamp': timestamp,
    'data_availability': {name: not df.empty for name, df in dfs.items()},
    'exchange_stats': exchange_stats.to_dict() if 'exchange_stats' in locals() else {},
}

# Export to JSON
output_file = f'funding_analysis_{timestamp}.json'
with open(output_file, 'w') as f:
    json.dump(analysis_results, f, indent=2, default=str)

print(f"\nAnalysis complete. Results saved to {output_file}")

# Add these analysis functions after the fetch functions
def analyze_funding_patterns(dfs):
    """Analyze funding rate patterns and seasonality"""
    print("\n=== Funding Rate Pattern Analysis ===")
    
    if not dfs['funding_market_snapshots'].empty:
        df = dfs['funding_market_snapshots'].copy()
        
        # Debug print columns
        print("\nAvailable columns:", df.columns.tolist())
        
        # Check for required columns
        required_columns = ['funding_rate', 'created_at']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"Missing required columns: {missing_columns}")
            return {}
            
        # Use created_at if timestamp is not available
        time_column = 'created_at'
        
        try:
            # Convert to datetime if not already
            df[time_column] = pd.to_datetime(df[time_column])
            
            # Extract time components
            df['hour'] = df[time_column].dt.hour
            df['day_of_week'] = df[time_column].dt.dayofweek
            
            # Hourly patterns
            hourly_stats = df.groupby('hour').agg({
                'funding_rate': ['mean', 'std', 'count']
            }).round(6)
            
            best_hours = hourly_stats['funding_rate'].nlargest(3, 'mean')
            worst_hours = hourly_stats['funding_rate'].nsmallest(3, 'mean')
            
            print("\nBest Hours for Funding (UTC):")
            print(best_hours)
            print("\nWorst Hours for Funding (UTC):")
            print(worst_hours)
            
            # Plot hourly patterns
            plt.figure(figsize=(12, 6))
            sns.boxplot(data=df, x='hour', y='funding_rate')
            plt.title('Hourly Funding Rate Distribution')
            plt.xlabel('Hour (UTC)')
            plt.ylabel('Funding Rate')
            plt.savefig('hourly_funding_patterns.png')
            plt.close()
            
            # Daily patterns
            daily_stats = df.groupby('day_of_week').agg({
                'funding_rate': ['mean', 'std', 'count']
            }).round(6)
            
            # Add day names for readability
            day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            daily_stats.index = day_names
            
            print("\nDaily Funding Rate Patterns:")
            print(daily_stats)
            
            return {
                'best_hours': best_hours.to_dict(),
                'worst_hours': worst_hours.to_dict(),
                'daily_stats': daily_stats.to_dict(),
                'hourly_stats': hourly_stats.to_dict()
            }
            
        except Exception as e:
            print(f"Error in analyze_funding_patterns: {str(e)}")
            print(f"DataFrame info:")
            print(df.info())
            return {}
    else:
        print("No funding market snapshot data available")
        return {}

def analyze_market_correlations(dfs):
    """Analyze correlations between funding rates and market metrics"""
    print("\n=== Market Correlation Analysis ===")
    
    if not dfs['funding_market_snapshots'].empty:
        df = dfs['funding_market_snapshots'].copy()
        
        # Debug print columns
        print("\nAvailable columns:", df.columns.tolist())
        
        # Check for required columns
        potential_metrics = ['funding_rate', 'volume_24h', 'open_interest', 'mark_price', 
                           'predicted_rate', 'next_funding_time']
        available_metrics = [col for col in potential_metrics if col in df.columns]
        
        if len(available_metrics) < 2:
            print("Not enough metrics available for correlation analysis")
            return {}
        
        try:
            # Calculate correlations for available metrics
            corr_matrix = df[available_metrics].corr()
            
            # Plot correlation heatmap
            plt.figure(figsize=(12, 10))
            sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0, fmt='.2f')
            plt.title('Market Metrics Correlation')
            plt.xticks(rotation=45)
            plt.yticks(rotation=0)
            plt.tight_layout()
            plt.savefig('market_correlations.png')
            plt.close()
            
            return {
                'correlations': corr_matrix.to_dict(),
                'available_metrics': available_metrics
            }
        except Exception as e:
            print(f"Error in analyze_market_correlations: {str(e)}")
            print("DataFrame info:")
            print(df.info())
            return {}
    else:
        print("No funding market snapshot data available")
        return {}

def identify_arbitrage_opportunities(dfs):
    """Identify and analyze arbitrage opportunities"""
    print("\n=== Arbitrage Opportunity Analysis ===")
    
    if not dfs['binance_funding'].empty and not dfs['hyperliquid_funding'].empty:
        # Merge exchange data
        binance = dfs['binance_funding'].copy()
        hyperliquid = dfs['hyperliquid_funding'].copy()
        
        merged = pd.merge(
            binance,
            hyperliquid,
            on=['symbol', 'timestamp'],
            suffixes=('_binance', '_hyperliquid')
        )
        
        # Calculate spreads
        merged['funding_spread'] = merged['funding_rate_binance'] - merged['funding_rate_hyperliquid']
        merged['annualized_return'] = merged['funding_spread'] * 365 * 100  # Annualized percentage
        
        # Find best opportunities
        best_ops = merged.nlargest(5, 'annualized_return')
        print("\nTop 5 Arbitrage Opportunities:")
        print(best_ops[['symbol', 'funding_spread', 'annualized_return']])
        
        return {
            'top_opportunities': best_ops.to_dict(orient='records'),
            'avg_spread': merged['funding_spread'].mean(),
            'max_return': merged['annualized_return'].max()
        }
    return {}

def analyze_market_regimes(dfs):
    """Identify market regimes using clustering"""
    print("\n=== Market Regime Analysis ===")
    
    if not dfs['funding_market_snapshots'].empty:
        df = dfs['funding_market_snapshots'].copy()
        
        # Debug print columns
        print("\nAvailable columns:", df.columns.tolist())
        
        # Define potential features and check which are available
        potential_features = ['funding_rate', 'volume_24h', 'open_interest', 'mark_price']
        available_features = [f for f in potential_features if f in df.columns]
        
        if len(available_features) < 2:
            print("Not enough features available for clustering analysis")
            return {}
            
        try:
            # Prepare features for clustering using only available columns
            X = df[available_features].copy()
            
            # Handle missing values if any
            X = X.fillna(X.mean())
            
            # Normalize features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Determine optimal number of clusters (2-5)
            inertias = []
            n_clusters_range = range(2, 6)
            for n in n_clusters_range:
                kmeans = KMeans(n_clusters=n, random_state=42)
                kmeans.fit(X_scaled)
                inertias.append(kmeans.inertia_)
            
            # Find optimal number of clusters using elbow method
            optimal_clusters = 3  # default
            for i in range(len(inertias)-1):
                if (inertias[i] - inertias[i+1]) / inertias[i] < 0.2:  # 20% improvement threshold
                    optimal_clusters = i + 2
                    break
            
            # Perform clustering with optimal number
            kmeans = KMeans(n_clusters=optimal_clusters, random_state=42)
            df['regime'] = kmeans.fit_predict(X_scaled)
            
            # Analyze regimes
            regime_stats = df.groupby('regime').agg({
                feature: ['mean', 'std', 'count'] for feature in available_features
            }).round(4)
            
            print(f"\nMarket Regime Characteristics (using {optimal_clusters} clusters):")
            print(regime_stats)
            
            # Plot regime characteristics
            plt.figure(figsize=(15, 8))
            
            # Create subplots for each feature
            for i, feature in enumerate(available_features, 1):
                plt.subplot(1, len(available_features), i)
                sns.boxplot(data=df, x='regime', y=feature)
                plt.title(f'{feature} by Regime')
                plt.xticks(rotation=0)
            
            plt.tight_layout()
            plt.savefig('market_regimes.png')
            plt.close()
            
            # Calculate regime transitions
            df['prev_regime'] = df.groupby('symbol')['regime'].shift(1)
            transitions = pd.crosstab(df['prev_regime'], df['regime'], normalize='index')
            
            return {
                'regime_stats': regime_stats.to_dict(),
                'n_clusters': optimal_clusters,
                'features_used': available_features,
                'regime_transitions': transitions.to_dict(),
                'cluster_sizes': df['regime'].value_counts().to_dict()
            }
            
        except Exception as e:
            print(f"Error in market regime analysis: {str(e)}")
            print("DataFrame info:")
            print(df.info())
            return {}
    else:
        print("No market snapshots data available")
        return {}

def analyze_prediction_accuracy(dfs):
    """Analyze accuracy of funding rate predictions"""
    print("\n=== Prediction Accuracy Analysis ===")
    
    if not dfs['predicted_rates'].empty and not dfs['funding_market_snapshots'].empty:
        pred_df = dfs['predicted_rates'].copy()
        actual_df = dfs['funding_market_snapshots'].copy()
        
        try:
            # Merge predicted and actual rates
            merged = pd.merge(
                pred_df,
                actual_df,
                on=['symbol', 'exchange'],
                suffixes=('_pred', '_actual'),
                how='inner'
            )
            
            # Calculate prediction metrics
            merged['prediction_error'] = merged['funding_rate_actual'] - merged['predicted_rate']
            merged['absolute_error'] = abs(merged['prediction_error'])
            merged['error_percentage'] = (merged['prediction_error'] / merged['funding_rate_actual']).abs() * 100
            
            # Aggregate metrics by symbol
            accuracy_metrics = merged.groupby('symbol').agg({
                'prediction_error': ['mean', 'std'],
                'absolute_error': 'mean',
                'error_percentage': 'mean'
            }).round(4)
            
            # Plot prediction accuracy
            plt.figure(figsize=(12, 6))
            sns.scatterplot(data=merged, x='funding_rate_actual', y='predicted_rate', hue='symbol')
            plt.plot([merged['funding_rate_actual'].min(), merged['funding_rate_actual'].max()], 
                    [merged['funding_rate_actual'].min(), merged['funding_rate_actual'].max()], 
                    'r--', label='Perfect Prediction')
            plt.title('Predicted vs Actual Funding Rates')
            plt.xlabel('Actual Funding Rate')
            plt.ylabel('Predicted Funding Rate')
            plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.tight_layout()
            plt.savefig('prediction_accuracy.png')
            plt.close()
            
            print("\nPrediction Accuracy Metrics:")
            print(accuracy_metrics)
            
            # Find best and worst predicted symbols
            best_predicted = accuracy_metrics.nsmallest(5, ('absolute_error', 'mean'))
            worst_predicted = accuracy_metrics.nlargest(5, ('absolute_error', 'mean'))
            
            print("\nBest Predicted Symbols:")
            print(best_predicted)
            print("\nWorst Predicted Symbols:")
            print(worst_predicted)
            
            return {
                'accuracy_metrics': accuracy_metrics.to_dict(),
                'best_predicted': best_predicted.to_dict(),
                'worst_predicted': worst_predicted.to_dict(),
                'mean_absolute_error': merged['absolute_error'].mean(),
                'mean_error_percentage': merged['error_percentage'].mean()
            }
            
        except Exception as e:
            print(f"Error in prediction accuracy analysis: {str(e)}")
            return {}
    else:
        print("Missing predicted rates or market snapshots data")
        return {}

def analyze_market_dynamics(dfs):
    """Analyze market dynamics using funding rates and market data"""
    print("\n=== Market Dynamics Analysis ===")
    
    if not dfs['funding_market_snapshots'].empty:
        df = dfs['funding_market_snapshots'].copy()
        
        try:
            # Calculate market metrics
            df['funding_volatility'] = df.groupby('symbol')['funding_rate'].transform('std')
            df['volume_rank'] = df.groupby('symbol')['volume_24h'].transform('rank', pct=True)
            df['oi_rank'] = df.groupby('symbol')['open_interest'].transform('rank', pct=True)
            
            # Market health score
            df['market_health'] = (
                df['volume_rank'] * 0.4 +
                df['oi_rank'] * 0.3 +
                (1 - df['funding_volatility']) * 0.3
            )
            
            # Analyze top markets
            top_markets = df.groupby('symbol').agg({
                'funding_rate': ['mean', 'std'],
                'volume_24h': 'mean',
                'open_interest': 'mean',
                'market_health': 'mean'
            }).round(4)
            
            top_markets = top_markets.sort_values(('market_health', 'mean'), ascending=False)
            
            print("\nTop 10 Healthiest Markets:")
            print(top_markets.head(10))
            
            # Plot market health distribution
            plt.figure(figsize=(12, 6))
            sns.boxplot(data=df, x='symbol', y='market_health', order=top_markets.head(20).index)
            plt.xticks(rotation=45)
            plt.title('Market Health Distribution')
            plt.tight_layout()
            plt.savefig('market_health.png')
            plt.close()
            
            return {
                'market_health': top_markets.to_dict(),
                'top_markets': top_markets.head(10).to_dict(),
                'overall_health': df['market_health'].mean()
            }
            
        except Exception as e:
            print(f"Error in market dynamics analysis: {str(e)}")
            return {}
    else:
        print("No market snapshots data available")
        return {}

# Add to the main analysis section
if __name__ == "__main__":
    # ... (previous code remains the same until after loading dfs)
    
    # Perform advanced analyses
    analysis_results.update({
        'funding_patterns': analyze_funding_patterns(dfs),
        'market_correlations': analyze_market_correlations(dfs),
        'arbitrage_opportunities': identify_arbitrage_opportunities(dfs),
        'market_regimes': analyze_market_regimes(dfs),
        'prediction_accuracy': analyze_prediction_accuracy(dfs),
        'market_dynamics': analyze_market_dynamics(dfs)
    })
    
    # Generate summary insights
    print("\n=== Key Insights ===")
    if 'arbitrage_opportunities' in analysis_results:
        arb = analysis_results['arbitrage_opportunities']
        if arb.get('max_return'):
            print(f"Maximum annualized return potential: {arb['max_return']:.2f}%")
    
    if 'funding_patterns' in analysis_results:
        patterns = analysis_results['funding_patterns']
        if patterns.get('best_hours'):
            print(f"Best funding hours identified: {list(patterns['best_hours'].keys())}")
    
    # Export enhanced analysis results
    output_file = f'enhanced_funding_analysis_{timestamp}.json'
    with open(output_file, 'w') as f:
        json.dump(analysis_results, f, indent=2, default=str)
    
    print(f"\nEnhanced analysis complete. Results saved to {output_file}")
    
    # Generate PDF report
    try:
        from fpdf import FPDF
        
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'Funding Rate Analysis Report', ln=True, align='C')
        
        # Add analysis sections
        pdf.set_font('Arial', '', 12)
        for section in ['funding_patterns', 'market_correlations', 'arbitrage_opportunities', 'market_regimes', 'prediction_accuracy', 'market_dynamics']:
            if section in analysis_results:
                pdf.add_page()
                pdf.set_font('Arial', 'B', 14)
                pdf.cell(0, 10, section.replace('_', ' ').title(), ln=True)
                pdf.set_font('Arial', '', 12)
                
                # Add visualizations
                if os.path.exists(f'{section}.png'):
                    pdf.image(f'{section}.png', x=10, w=190)
        
        pdf_file = f'funding_analysis_report_{timestamp}.pdf'
        pdf.output(pdf_file)
        print(f"PDF report generated: {pdf_file}")
        
    except ImportError:
        print("FPDF not installed. Skipping PDF report generation.")