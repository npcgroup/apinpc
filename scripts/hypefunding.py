import aiohttp
import asyncio
import json
from datetime import datetime, timedelta
import pandas as pd
import logging
import os
from tqdm import tqdm
from tabulate import tabulate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HyperliquidFundingCollector:
    def __init__(self):
        self.base_url = 'https://api.hyperliquid.xyz/info'
        
    async def get_all_markets(self):
        """Fetch all available markets from Hyperliquid"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.base_url,
                json={"type": "metaAndAssetCtxs"},
                headers={'Content-Type': 'application/json'}
            ) as response:
                if response.status != 200:
                    raise Exception(f"Failed to fetch markets: {response.status}")
                data = await response.json()
                if isinstance(data, list) and len(data) > 0:
                    universe = data[0].get('universe', [])
                    return [market['name'] for market in universe]
                return []

    async def get_predicted_funding_rates(self):
        """Fetch predicted funding rates for all venues"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.base_url,
                json={"type": "predictedFundings"},
                headers={'Content-Type': 'application/json'}
            ) as response:
                if response.status != 200:
                    return {}
                data = await response.json()
                predicted_rates = {}
                for item in data:
                    if isinstance(item, list) and len(item) > 1:
                        coin = item[0]
                        venues = item[1]
                        for venue in venues:
                            if venue[0] == "HlPerp":
                                predicted_rates[coin] = venue[1].get("fundingRate", 0)
                return predicted_rates

    async def get_funding_data(self, token: str):
        """Fetch current, predicted, and historical funding rates for a token"""
        async with aiohttp.ClientSession() as session:
            # Get current market data
            current_payload = {
                "type": "metaAndAssetCtxs"
            }
            
            # Get historical funding rates (last 24h)
            yesterday = int((datetime.now() - timedelta(days=1)).timestamp() * 1000)
            historical_payload = {
                "type": "fundingHistory",
                "coin": token,
                "startTime": yesterday
            }
            
            # Make parallel requests
            current_response = await session.post(
                self.base_url,
                json=current_payload,
                headers={'Content-Type': 'application/json'}
            )
            historical_response = await session.post(
                self.base_url,
                json=historical_payload,
                headers={'Content-Type': 'application/json'}
            )
            
            if current_response.status != 200 or historical_response.status != 200:
                logger.error(f"Failed to fetch data for {token}")
                return None
            
            current_data = await current_response.json()
            historical_data = await historical_response.json()
            
            # Extract current market data
            if isinstance(current_data, list) and len(current_data) > 1:
                market_info = None
                asset_contexts = current_data[1]
                for context in asset_contexts:
                    if isinstance(context, dict) and 'funding' in context:
                        market_info = context
                        break
                
                if market_info:
                    current_funding = float(market_info.get('funding', 0))
                    open_interest = float(market_info.get('openInterest', 0))
                    mark_price = float(market_info.get('markPx', 0))
                    
                    # Calculate notional open interest in USD
                    notional_open_interest = open_interest * mark_price
                    
                    # Process historical rates
                    historical_rates = []
                    for entry in historical_data:
                        if isinstance(entry, dict):
                            historical_rates.append({
                                'timestamp': datetime.fromtimestamp(entry.get('time', 0) / 1000),
                                'rate': float(entry.get('fundingRate', 0))
                            })
                    
                    return {
                        'token': token,
                        'current_funding_rate': current_funding,
                        'mark_price': mark_price,
                        'open_interest': open_interest,
                        'notional_open_interest': notional_open_interest,
                        'volume_24h': float(market_info.get('dayNtlVlm', 0)),
                        'historical_rates': historical_rates
                    }
            
            return None

async def main():
    # Create output directory if it doesn't exist
    output_dir = "data/funding_rates"
    os.makedirs(output_dir, exist_ok=True)
    
    collector = HyperliquidFundingCollector()
    
    try:
        print("\n🌟 Starting Hyperliquid Funding Rate Collection 🌟\n")
        
        # Get all markets
        markets = await collector.get_all_markets()
        logger.info(f"📊 Found {len(markets)} markets")
        
        # Get predicted funding rates
        predicted_rates = await collector.get_predicted_funding_rates()
        
        # Progress bar setup
        with tqdm(total=len(markets), desc="Collecting market data") as pbar:
            # Fetch funding data for all markets
            results = []
            for token in markets:
                try:
                    data = await collector.get_funding_data(token)
                    if data:
                        data['predicted_funding_rate'] = predicted_rates.get(token, 0)
                        results.append(data)
                        pbar.update(1)
                except Exception as e:
                    logger.error(f"Error processing {token}: {str(e)}")
                    pbar.update(1)

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if results:
            # Create summary DataFrame with proper type conversion
            summary = pd.DataFrame([{
                'token': r['token'],
                'current_funding_rate': float(r['current_funding_rate']),
                'predicted_funding_rate': float(r['predicted_funding_rate']),
                'mark_price': r['mark_price'],
                'open_interest': r['open_interest'],
                'volume_24h': r['volume_24h'],
                'avg_24h_funding_rate': sum(h['rate'] for h in r['historical_rates']) / len(r['historical_rates']) if r['historical_rates'] else None
            } for r in results])
            
            # Calculate additional metrics
            summary['funding_difference'] = summary['predicted_funding_rate'] - summary['current_funding_rate']
            summary['annualized_funding'] = summary['current_funding_rate'] * 365 * 100
            
            # Save files
            json_file = os.path.join(output_dir, f'funding_analysis_{timestamp}.json')
            csv_file = os.path.join(output_dir, f'funding_summary_{timestamp}.csv')
            raw_file = os.path.join(output_dir, f'funding_raw_{timestamp}.json')
            
            # Save all data files
            detailed_summary = create_detailed_summary(summary, timestamp)
            save_files(detailed_summary, summary, results, json_file, csv_file, raw_file)
            
            # Print beautiful terminal summary
            print_terminal_summary(summary, json_file, csv_file, raw_file)
            
        else:
            logger.error("❌ No results were collected")
            
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")

def create_detailed_summary(summary, timestamp):
    return {
        'timestamp': datetime.now().isoformat(),
        'market_summary': {
            'total_markets': len(summary),
            'positive_funding_markets': len(summary[summary['current_funding_rate'] > 0]),
            'negative_funding_markets': len(summary[summary['current_funding_rate'] < 0]),
            'highest_annual_funding': float(summary['annualized_funding'].max()),
            'lowest_annual_funding': float(summary['annualized_funding'].min()),
        },
        'funding_opportunities': {
            'highest_positive_current_rates': summary[summary['current_funding_rate'] > 0].nlargest(5, 'current_funding_rate')[
                ['token', 'current_funding_rate', 'predicted_funding_rate', 'annualized_funding']
            ].to_dict('records'),
            'lowest_negative_current_rates': summary[summary['current_funding_rate'] < 0].nsmallest(5, 'current_funding_rate')[
                ['token', 'current_funding_rate', 'predicted_funding_rate', 'annualized_funding']
            ].to_dict('records'),
            'largest_positive_differences': summary[summary['funding_difference'] > 0].nlargest(5, 'funding_difference')[
                ['token', 'current_funding_rate', 'predicted_funding_rate', 'funding_difference']
            ].to_dict('records'),
            'largest_negative_differences': summary[summary['funding_difference'] < 0].nsmallest(5, 'funding_difference')[
                ['token', 'current_funding_rate', 'predicted_funding_rate', 'funding_difference']
            ].to_dict('records')
        },
        'all_markets': summary.to_dict('records')
    }

def save_files(detailed_summary, summary, results, json_file, csv_file, raw_file):
    # Save detailed JSON analysis
    with open(json_file, 'w') as f:
        json.dump(detailed_summary, f, indent=2, default=str)
    
    # Save CSV summary
    summary.to_csv(csv_file, index=False)
    
    # Save raw data
    with open(raw_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)

def print_terminal_summary(summary, json_file, csv_file, raw_file):
    print("\n" + "="*80)
    print("🚀 HYPERLIQUID FUNDING RATE ANALYSIS COMPLETE 🚀".center(80))
    print("="*80 + "\n")

    print("📊 Market Overview:")
    print(f"  • Total Markets Analyzed: {len(summary)}")
    print(f"  • Markets with Positive Funding: {len(summary[summary['current_funding_rate'] > 0])}")
    print(f"  • Markets with Negative Funding: {len(summary[summary['current_funding_rate'] < 0])}\n")

    print("💰 Top 5 Highest Positive Funding Rates (Annualized):")
    print(tabulate(
        summary[summary['current_funding_rate'] > 0].nlargest(5, 'annualized_funding')[
            ['token', 'current_funding_rate', 'predicted_funding_rate', 'annualized_funding']
        ],
        headers=['Token', 'Current Rate', 'Predicted Rate', 'Annual %'],
        floatfmt=".4f",
        tablefmt="pretty"
    ))

    print("\n📉 Top 5 Lowest Negative Funding Rates (Annualized):")
    print(tabulate(
        summary[summary['current_funding_rate'] < 0].nsmallest(5, 'current_funding_rate')[
            ['token', 'current_funding_rate', 'predicted_funding_rate', 'annualized_funding']
        ],
        headers=['Token', 'Current Rate', 'Predicted Rate', 'Annual %'],
        floatfmt=".4f",
        tablefmt="pretty"
    ))

    print("\n📁 Output Files:")
    print(f"  • Detailed Analysis: {json_file}")
    print(f"  • Summary CSV: {csv_file}")
    print(f"  • Raw Data: {raw_file}")
    
    print("\n💡 Next Steps:")
    print("  1. Review the detailed analysis in the JSON file")
    print("  2. Import the CSV into your preferred analysis tool")
    print("  3. Use the raw data for custom analysis")
    
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    # Run the main function
    asyncio.run(main())