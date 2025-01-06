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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FundingRateAnalyzer:
    def __init__(self):
        self.data_dir = "data/funding_rates"
        self.output_dir = "data/analysis"
        os.makedirs(self.output_dir, exist_ok=True)

    def load_latest_data(self) -> pd.DataFrame:
        """Load the most recent funding rate data with better error handling"""
        try:
            # Get latest funding rate file
            files = [f for f in os.listdir(self.data_dir) if f.startswith('funding_raw_')]
            if not files:
                raise FileNotFoundError("No funding rate data files found")
            
            latest_file = max(files)
            logger.info(f"Loading data from {latest_file}")
            
            with open(os.path.join(self.data_dir, latest_file)) as f:
                data = json.load(f)
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            # Add timestamp if missing
            if 'timestamp' not in df.columns:
                logger.warning("Timestamp column missing, adding current timestamp")
                df['timestamp'] = datetime.now().isoformat()
            
            # Ensure all required columns exist
            required_columns = [
                'token', 
                'current_funding_rate', 
                'predicted_funding_rate',
                'mark_price',
                'open_interest',
                'volume_24h'
            ]
            
            for col in required_columns:
                if col not in df.columns:
                    logger.warning(f"Missing column {col}, adding with default values")
                    df[col] = 0.0
            
            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Clean up data
            df = df.fillna(0)  # Fill NaN values with 0
            df = df.replace([np.inf, -np.inf], 0)  # Replace infinite values
            
            # Validate numeric columns
            numeric_columns = ['current_funding_rate', 'predicted_funding_rate', 'mark_price', 'open_interest', 'volume_24h']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

            logger.info(f"Successfully loaded {len(df)} records")
            return df

        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            # Return empty DataFrame with required columns
            return pd.DataFrame(columns=[
                'timestamp',
                'token',
                'current_funding_rate',
                'predicted_funding_rate',
                'mark_price',
                'open_interest',
                'volume_24h'
            ])

    def generate_analysis(self):
        """Generate comprehensive funding rate analysis with error handling"""
        try:
            df = self.load_latest_data()
            
            if len(df) == 0:
                logger.warning("No data available for analysis")
                return {
                    "timestamp": datetime.now().isoformat(),
                    "market_summary": {
                        "total_markets": 0,
                        "error": "No data available for analysis"
                    }
                }

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            analysis = {
                "timestamp": datetime.now().isoformat(),
                "market_summary": self._generate_market_summary(df),
                "opportunities": self._identify_opportunities(df),
                "risk_metrics": self._calculate_risk_metrics(df),
                "volume_analysis": self._analyze_volume(df),
                "recommendations": self._generate_recommendations(df)
            }

            # Save analysis
            output_file = f"{self.output_dir}/funding_analysis_{timestamp}.json"
            with open(output_file, 'w') as f:
                json.dump(analysis, f, indent=2, default=str)
            
            logger.info(f"Analysis saved to {output_file}")
            
            # Print report
            self._print_report(analysis)
            
            return analysis

        except Exception as e:
            logger.error(f"Error generating analysis: {str(e)}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "market_summary": {
                    "total_markets": 0,
                    "error": "Analysis failed"
                }
            }

    def _generate_market_summary(self, df: pd.DataFrame) -> Dict:
        """Generate market overview statistics"""
        return {
            "total_markets": len(df),
            "total_volume_24h": df['volume_24h'].sum(),
            "total_open_interest": df['open_interest'].sum(),
            "avg_funding_rate": df['current_funding_rate'].mean() * 100,
            "median_funding_rate": df['current_funding_rate'].median() * 100,
            "highest_funding_rate": df['current_funding_rate'].max() * 100,
            "lowest_funding_rate": df['current_funding_rate'].min() * 100,
            "positive_funding_markets": len(df[df['current_funding_rate'] > 0]),
            "negative_funding_markets": len(df[df['current_funding_rate'] < 0])
        }

    def _identify_opportunities(self, df: pd.DataFrame) -> Dict:
        """Identify trading opportunities"""
        df['funding_difference'] = df['predicted_funding_rate'] - df['current_funding_rate']
        df['annualized_funding'] = df['current_funding_rate'] * 365 * 100

        return {
            "highest_current_rates": df.nlargest(5, 'current_funding_rate')[
                ['token', 'current_funding_rate', 'predicted_funding_rate', 'annualized_funding']
            ].to_dict('records'),
            
            "largest_predicted_changes": df.nlargest(5, 'funding_difference')[
                ['token', 'current_funding_rate', 'predicted_funding_rate', 'funding_difference']
            ].to_dict('records'),
            
            "high_volume_opportunities": df[df['volume_24h'] > df['volume_24h'].quantile(0.75)].nlargest(5, 'funding_difference')[
                ['token', 'current_funding_rate', 'predicted_funding_rate', 'volume_24h', 'funding_difference']
            ].to_dict('records')
        }

    def _calculate_risk_metrics(self, df: pd.DataFrame) -> Dict:
        """Calculate risk-related metrics"""
        return {
            "high_risk_markets": df[
                (df['volume_24h'] < df['volume_24h'].quantile(0.25)) & 
                (abs(df['current_funding_rate']) > df['current_funding_rate'].quantile(0.75))
            ]['token'].tolist(),
            "liquidity_metrics": {
                "avg_volume_per_market": df['volume_24h'].mean(),
                "median_open_interest": df['open_interest'].median(),
                "volume_concentration": (df.nlargest(5, 'volume_24h')['volume_24h'].sum() / df['volume_24h'].sum()) * 100
            }
        }

    def _analyze_volume(self, df: pd.DataFrame) -> Dict:
        """Analyze volume patterns"""
        return {
            "top_volume_markets": df.nlargest(5, 'volume_24h')[
                ['token', 'volume_24h', 'open_interest']
            ].to_dict('records'),
            "volume_distribution": {
                "low_volume": len(df[df['volume_24h'] < df['volume_24h'].quantile(0.25)]),
                "medium_volume": len(df[
                    (df['volume_24h'] >= df['volume_24h'].quantile(0.25)) & 
                    (df['volume_24h'] < df['volume_24h'].quantile(0.75))
                ]),
                "high_volume": len(df[df['volume_24h'] >= df['volume_24h'].quantile(0.75)])
            }
        }

    def _generate_recommendations(self, df: pd.DataFrame) -> List[Dict]:
        """Generate trading recommendations"""
        recommendations = []
        
        # High funding rate with good volume
        high_funding = df[
            (df['current_funding_rate'] > df['current_funding_rate'].quantile(0.75)) & 
            (df['volume_24h'] > df['volume_24h'].median())
        ]
        
        for _, market in high_funding.iterrows():
            recommendations.append({
                "token": market['token'],
                "type": "high_funding",
                "current_rate": market['current_funding_rate'],
                "predicted_rate": market['predicted_funding_rate'],
                "confidence": "high" if market['volume_24h'] > df['volume_24h'].quantile(0.9) else "medium"
            })

        return recommendations

    def _print_report(self, analysis: Dict):
        """Print formatted analysis report"""
        print("\n" + "="*80)
        print("🔍 FUNDING RATE ANALYSIS REPORT")
        print("="*80 + "\n")

        print("📊 Market Summary:")
        print(f"Total Markets: {analysis['market_summary']['total_markets']}")
        print(f"Average Funding Rate: {analysis['market_summary']['avg_funding_rate']:.4f}%")
        print(f"Total 24h Volume: ${analysis['market_summary']['total_volume_24h']:,.2f}")
        print(f"Total Open Interest: ${analysis['market_summary']['total_open_interest']:,.2f}\n")

        print("💰 Top Opportunities:")
        for opp in analysis['opportunities']['highest_current_rates'][:3]:
            print(f"• {opp['token']}: Current Rate = {opp['current_funding_rate']*100:.4f}% "
                  f"(Predicted: {opp['predicted_funding_rate']*100:.4f}%)")

        print("\n⚠️ Risk Metrics:")
        print(f"Volume Concentration (Top 5): {analysis['risk_metrics']['liquidity_metrics']['volume_concentration']:.1f}%")
        
        print("\n📈 Recommendations:")
        for rec in analysis['recommendations'][:3]:
            print(f"• {rec['token']}: {rec['type'].replace('_', ' ').title()} "
                  f"(Confidence: {rec['confidence']})")

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