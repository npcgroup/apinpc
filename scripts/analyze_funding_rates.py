import pandas as pd
import json
import os
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from tabulate import tabulate
import logging
from typing import Dict, List
import numpy as np
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FundingRateAnalyzer:
    def __init__(self):
        self.data_dir = "data/funding_rates"
        self.output_dir = "data/analysis"
        os.makedirs(self.output_dir, exist_ok=True)

    def load_latest_data(self) -> pd.DataFrame:
        """Load and process the most recent funding rate data"""
        try:
            files = [f for f in os.listdir(self.data_dir) if f.startswith('funding_raw_')]
            if not files:
                raise FileNotFoundError("No funding rate data files found")
            
            latest_file = max(files)
            file_path = os.path.join(self.data_dir, latest_file)
            logger.info(f"Loading data from {latest_file}")
            
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Convert to DataFrame for easier analysis
            processed_data = []
            for market in data:
                # Calculate additional metrics
                historical_rates = pd.DataFrame(market['historical_rates'])
                avg_funding_rate = historical_rates['rate'].mean() if not historical_rates.empty else market['current_funding_rate']
                rate_volatility = historical_rates['rate'].std() if not historical_rates.empty else 0
                
                # Calculate notional values
                notional_oi = float(market['open_interest']) * float(market['mark_price'])
                
                processed_data.append({
                    'token': market['token'],
                    'current_funding_rate': float(market['current_funding_rate']),
                    'predicted_funding_rate': float(market['predicted_funding_rate']),
                    'mark_price': float(market['mark_price']),
                    'open_interest': float(market['open_interest']),
                    'notional_open_interest': notional_oi,
                    'volume_24h': float(market['volume_24h']),
                    'avg_funding_rate_24h': avg_funding_rate,
                    'funding_rate_volatility': rate_volatility,
                    'historical_rates': market['historical_rates']
                })
            
            df = pd.DataFrame(processed_data)
            return df
            
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            raise

    def identify_opportunities(self, df: pd.DataFrame) -> Dict:
        """Identify funding rate opportunities with improved metrics"""
        try:
            # Calculate annualized rates
            df['annualized_funding'] = df['current_funding_rate'] * 365 * 24
            df['predicted_annual'] = df['predicted_funding_rate'] * 365 * 24
            
            # Calculate opportunity scores
            df['opportunity_score'] = (
                (df['predicted_funding_rate'] - df['current_funding_rate']).abs() * 
                np.log1p(df['notional_open_interest']) * 
                (1 + df['volume_24h'] / df['notional_open_interest'])
            )
            
            # Filter for liquid markets
            liquid_markets = df[df['notional_open_interest'] > df['notional_open_interest'].median()]
            
            opportunities = {
                'highest_current_rates': df.nlargest(5, 'current_funding_rate')[
                    ['token', 'current_funding_rate', 'predicted_funding_rate', 'notional_open_interest']
                ].to_dict('records'),
                
                'highest_predicted_rates': df.nlargest(5, 'predicted_funding_rate')[
                    ['token', 'current_funding_rate', 'predicted_funding_rate', 'notional_open_interest']
                ].to_dict('records'),
                
                'best_opportunities': liquid_markets.nlargest(5, 'opportunity_score')[
                    ['token', 'current_funding_rate', 'predicted_funding_rate', 'opportunity_score', 'notional_open_interest']
                ].to_dict('records')
            }
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Error identifying opportunities: {str(e)}")
            raise

    def calculate_market_metrics(self, df: pd.DataFrame) -> Dict:
        """Calculate comprehensive market metrics"""
        try:
            total_oi = df['notional_open_interest'].sum()
            total_volume = df['volume_24h'].sum()
            
            metrics = {
                'total_markets': len(df),
                'total_open_interest': total_oi,
                'total_volume_24h': total_volume,
                'avg_funding_rate': df['current_funding_rate'].mean(),
                'weighted_funding_rate': (
                    df['current_funding_rate'] * df['notional_open_interest']
                ).sum() / total_oi if total_oi > 0 else 0,
                'market_concentration': (
                    df.nlargest(5, 'notional_open_interest')['notional_open_interest'].sum() / total_oi
                ) * 100 if total_oi > 0 else 0
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating market metrics: {str(e)}")
            raise

    def generate_analysis(self) -> Dict:
        """Generate comprehensive market analysis"""
        try:
            df = self.load_latest_data()
            
            opportunities = self.identify_opportunities(df)
            market_metrics = self.calculate_market_metrics(df)
            
            analysis = {
                'timestamp': datetime.now().isoformat(),
                'market_summary': market_metrics,
                'opportunities': opportunities,
                'risk_metrics': {
                    'liquidity_metrics': {
                        'volume_concentration': market_metrics['market_concentration'],
                        'illiquid_markets': len(df[df['volume_24h'] < df['volume_24h'].median()]),
                    }
                },
                'recommendations': [
                    {
                        'token': opp['token'],
                        'type': 'long' if opp['predicted_funding_rate'] > opp['current_funding_rate'] else 'short',
                        'confidence': min(abs(opp['opportunity_score']) / df['opportunity_score'].max() * 100, 100)
                    }
                    for opp in opportunities['best_opportunities'][:3]
                ]
            }
            
            # Save detailed analysis
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = Path(self.output_dir) / f"funding_analysis_{timestamp}.json"
            
            with open(output_file, 'w') as f:
                json.dump(analysis, f, indent=2, default=str)
            
            # Print summary
            self._print_analysis_summary(analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error generating analysis: {str(e)}")
            raise

    def _print_analysis_summary(self, analysis: Dict):
        """Print formatted analysis summary"""
        print("\n" + "="*80)
        print("📊 Market Summary:")
        print(f"Total Markets: {analysis['market_summary']['total_markets']}")
        print(f"Total Open Interest: ${analysis['market_summary']['total_open_interest']:,.2f}")
        print(f"24h Volume: ${analysis['market_summary']['total_volume_24h']:,.2f}")
        print(f"Weighted Funding Rate: {analysis['market_summary']['weighted_funding_rate']*100:.4f}%")
        
        print("\n🔥 Top Opportunities:")
        for opp in analysis['opportunities']['best_opportunities'][:3]:
            print(f"• {opp['token']}: Current {opp['current_funding_rate']*100:.4f}% → "
                  f"Predicted {opp['predicted_funding_rate']*100:.4f}% "
                  f"(OI: ${opp['notional_open_interest']:,.2f})")
        
        print("\n⚠️ Risk Metrics:")
        print(f"Market Concentration: {analysis['risk_metrics']['liquidity_metrics']['volume_concentration']:.1f}%")
        print(f"Illiquid Markets: {analysis['risk_metrics']['liquidity_metrics']['illiquid_markets']}")
        
        print("\n" + "="*80 + "\n")

def main():
    try:
        analyzer = FundingRateAnalyzer()
        analysis = analyzer.generate_analysis()
        logger.info("✅ Analysis completed successfully")
    except Exception as e:
        logger.error(f"❌ Analysis failed: {str(e)}")
        raise

if __name__ == "__main__":
    main() 