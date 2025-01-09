import json
import os
from datetime import datetime
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarketBlogGenerator:
    def __init__(self):
        self.pipeline_dir = Path("data/pipeline")
        self.blog_dir = Path("public/market-updates")
        self.blog_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup plotting style
        plt.style.use('dark_background')
        sns.set_theme(style="darkgrid")

    def load_latest_pipeline_data(self) -> Dict:
        """Load the most recent pipeline data"""
        try:
            # Get latest pipeline summary
            summaries = list(self.pipeline_dir.glob("pipeline_summary_*.json"))
            if not summaries:
                raise FileNotFoundError("No pipeline summaries found")
            
            latest_summary = max(summaries, key=lambda x: x.stat().st_mtime)
            
            with open(latest_summary) as f:
                summary = json.load(f)
                
            # Load corresponding raw data
            raw_data_file = Path(summary["raw_data_file"])
            with open(raw_data_file) as f:
                raw_data = json.load(f)
                
            return {
                "summary": summary,
                "raw_data": raw_data,
                "timestamp": datetime.fromisoformat(summary["timestamp"])
            }
            
        except Exception as e:
            logger.error(f"Error loading pipeline data: {str(e)}")
            raise

    def generate_market_charts(self, data: List[Dict], timestamp: datetime) -> Dict[str, str]:
        """Generate market analysis charts"""
        try:
            df = pd.DataFrame(data)
            
            # Calculate notional open interest
            df['notional_open_interest'] = df['open_interest'] * df['mark_price']
            
            charts = {}
            
            # 1. Funding Rate Distribution
            plt.figure(figsize=(10, 6))
            sns.histplot(data=df, x='current_funding_rate', bins=30)
            plt.title('Funding Rate Distribution')
            plt.xlabel('Current Funding Rate')
            plt.ylabel('Count')
            filename = f'funding_dist_{timestamp:%Y%m%d_%H%M}.png'
            plt.savefig(self.blog_dir / filename)
            plt.close()
            charts['funding_distribution'] = f'/market-updates/{filename}'

            # 2. Top Markets by Open Interest
            plt.figure(figsize=(12, 6))
            top_markets = df.nlargest(10, 'notional_open_interest')
            sns.barplot(data=top_markets, x='token', y='notional_open_interest')
            plt.xticks(rotation=45)
            plt.title('Top 10 Markets by Open Interest')
            plt.xlabel('Token')
            plt.ylabel('Notional Open Interest ($)')
            plt.ticklabel_format(style='plain', axis='y')
            filename = f'top_markets_{timestamp:%Y%m%d_%H%M}.png'
            plt.savefig(self.blog_dir / filename)
            plt.close()
            charts['top_markets'] = f'/market-updates/{filename}'

            # 3. Funding Rate vs Volume Scatter
            plt.figure(figsize=(10, 6))
            sns.scatterplot(data=df, x='current_funding_rate', y='volume_24h', 
                          size='notional_open_interest', alpha=0.6)
            plt.title('Funding Rate vs Volume')
            plt.xlabel('Current Funding Rate')
            plt.ylabel('24h Volume ($)')
            plt.ticklabel_format(style='plain', axis='y')
            filename = f'funding_volume_{timestamp:%Y%m%d_%H%M}.png'
            plt.savefig(self.blog_dir / filename)
            plt.close()
            charts['funding_volume'] = f'/market-updates/{filename}'

            return charts
            
        except Exception as e:
            logger.error(f"Error generating charts: {str(e)}")
            raise

    def generate_blog_post(self, data: Dict, charts: Dict[str, str]) -> Dict:
        """Generate blog post content"""
        try:
            df = pd.DataFrame(data['raw_data'])
            timestamp = data['timestamp']
            
            # Calculate notional open interest
            df['notional_open_interest'] = df['open_interest'] * df['mark_price']
            
            # Get highest funding rate market
            highest_funding_market = df.nlargest(1, 'current_funding_rate').iloc[0]
            lowest_funding_market = df.nsmallest(1, 'current_funding_rate').iloc[0]
            most_active_market = df.nlargest(1, 'volume_24h').iloc[0]
            largest_oi_market = df.nlargest(1, 'notional_open_interest').iloc[0]
            
            # Calculate key metrics with primitive types
            metrics = {
                'total_markets': int(len(df)),
                'total_volume': float(df['volume_24h'].sum()),
                'total_oi': float(df['notional_open_interest'].sum()),
                'avg_funding': float(df['current_funding_rate'].mean() * 100),
                'highest_funding': {
                    'token': str(highest_funding_market['token']),
                    'current_funding_rate': float(highest_funding_market['current_funding_rate'])
                },
                'lowest_funding': {
                    'token': str(lowest_funding_market['token']),
                    'current_funding_rate': float(lowest_funding_market['current_funding_rate'])
                }
            }

            # Generate blog content with serializable data
            blog_post = {
                'timestamp': timestamp.isoformat(),
                'title': f'Market Update: {timestamp:%Y-%m-%d %H:%M} UTC',
                'summary': f"""
                    Market overview across {metrics['total_markets']} trading pairs with 
                    ${metrics['total_volume']:,.0f} 24h volume and 
                    ${metrics['total_oi']:,.0f} open interest.
                """.strip(),
                'metrics': metrics,
                'charts': charts,
                'highlights': [
                    {
                        'title': 'Highest Funding Rate',
                        'content': f"{highest_funding_market['token']}: {float(highest_funding_market['current_funding_rate'])*100:.4f}%"
                    },
                    {
                        'title': 'Most Active Market',
                        'content': f"{most_active_market['token']}: ${float(most_active_market['volume_24h']):,.0f}"
                    },
                    {
                        'title': 'Largest Open Interest',
                        'content': f"{largest_oi_market['token']}: ${float(largest_oi_market['notional_open_interest']):,.0f}"
                    }
                ],
                'market_data': {
                    'highest_funding': {
                        'token': str(highest_funding_market['token']),
                        'rate': float(highest_funding_market['current_funding_rate']),
                        'volume': float(highest_funding_market['volume_24h'])
                    },
                    'most_active': {
                        'token': str(most_active_market['token']),
                        'volume': float(most_active_market['volume_24h']),
                        'rate': float(most_active_market['current_funding_rate'])
                    },
                    'largest_oi': {
                        'token': str(largest_oi_market['token']),
                        'oi': float(largest_oi_market['notional_open_interest']),
                        'rate': float(largest_oi_market['current_funding_rate'])
                    }
                }
            }

            # Save blog post
            output_file = self.blog_dir / f'market_update_{timestamp:%Y%m%d_%H%M}.json'
            with open(output_file, 'w') as f:
                json.dump(blog_post, f, indent=2)

            # Also save as latest.json for easy access
            latest_file = self.blog_dir / 'latest.json'
            with open(latest_file, 'w') as f:
                json.dump(blog_post, f, indent=2)

            logger.info(f"✅ Generated blog post: {output_file}")
            return blog_post
            
        except Exception as e:
            logger.error(f"Error generating blog post: {str(e)}")
            raise

async def main():
    try:
        generator = MarketBlogGenerator()
        
        # Load pipeline data
        data = generator.load_latest_pipeline_data()
        
        # Generate charts
        charts = generator.generate_market_charts(data['raw_data'], data['timestamp'])
        
        # Generate blog post
        blog_post = generator.generate_blog_post(data, charts)
        
        logger.info(f"✅ Generated market update blog post: {blog_post['title']}")
        
    except Exception as e:
        logger.error(f"❌ Failed to generate market blog: {str(e)}")
        raise

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 