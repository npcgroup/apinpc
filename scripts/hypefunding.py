import aiohttp
import asyncio
import json
from datetime import datetime, timedelta
import pandas as pd
import logging
import os
from tqdm import tqdm
from tabulate import tabulate
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HyperliquidFundingCollector:
    def __init__(self):
        self.base_urls = [
            'https://api.hyperliquid.xyz/info'  # Use only the most reliable endpoint
        ]
        self.session = None
        self.batch_size = 20
        self.retry_attempts = 3
        self.cache = {}
        self.current_url_index = 0
        
    async def __aenter__(self):
        # Configure session with proper SSL and timeout settings
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(
                ssl=False,  # Disable SSL verification if needed
                force_close=True,
                enable_cleanup_closed=True,
                ttl_dns_cache=300
            )
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def test_connection(self):
        """Test connection to available endpoints"""
        for i, url in enumerate(self.base_urls):
            try:
                async with self.session.post(
                    url,
                    json={"type": "metaAndAssetCtxs"},
                    headers={'Content-Type': 'application/json'}
                ) as response:
                    if response.status == 200:
                        self.current_url_index = i
                        logger.info(f"✅ Connected successfully to {url}")
                        return True
            except Exception as e:
                logger.warning(f"Failed to connect to {url}: {str(e)}")
                continue
        return False

    async def make_request(self, payload: Dict, max_retries: int = 3) -> Optional[Dict]:
        """Enhanced request method with better error handling and retries"""
        for attempt in range(max_retries):
            for url_index, base_url in enumerate(self.base_urls):
                try:
                    async with self.session.post(
                        base_url,
                        json=payload,
                        headers={
                            'Content-Type': 'application/json',
                            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
                            'Accept': 'application/json'
                        },
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        if response.status == 200:
                            self.current_url_index = url_index
                            return await response.json()
                except Exception as e:
                    logger.warning(f"Attempt {attempt + 1} failed for {base_url}: {str(e)}")
                    continue
            
            # Wait before retrying
            await asyncio.sleep(1 * (attempt + 1))
        
        raise Exception(f"Failed to fetch data after {max_retries} attempts")

    async def get_all_markets(self):
        """Fetch all available markets with improved error handling"""
        try:
            data = await self.make_request({"type": "metaAndAssetCtxs"})
            if isinstance(data, list) and len(data) > 0:
                universe = data[0].get('universe', [])
                markets = [market['name'] for market in universe]
                logger.info(f"📊 Found {len(markets)} markets")
                return markets
            return []
        except Exception as e:
            logger.error(f"Failed to fetch markets: {str(e)}")
            raise

    async def get_predicted_funding_rates(self):
        """Fetch predicted funding rates for all venues"""
        try:
            data = await self.make_request({"type": "predictedFundings"})
            predicted_rates = {}
            for item in data:
                if isinstance(item, list) and len(item) > 1:
                    coin = item[0]
                    venues = item[1]
                    for venue in venues:
                        if venue[0] == "HlPerp":
                            predicted_rates[coin] = venue[1].get("fundingRate", 0)
            return predicted_rates
        except Exception as e:
            logger.error(f"Failed to fetch predicted rates: {str(e)}")
            return {}

    async def get_funding_data(self, token: str):
        """Fetch current, predicted, and historical funding rates for a token"""
        try:
            # Get historical funding rates (last 24h)
            yesterday = int((datetime.now() - timedelta(days=1)).timestamp() * 1000)
            historical_payload = {
                "type": "fundingHistory",
                "coin": token,
                "startTime": yesterday
            }
            
            # Use make_request instead of direct session usage
            historical_data = await self.make_request(historical_payload)
            
            # Get current market data
            current_data = await self.make_request({"type": "metaAndAssetCtxs"})
            
            if not historical_data or not current_data:
                logger.warning(f"Failed to fetch complete data for {token}")
                return None
            
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
                                'rate': float(entry.get('funding', 0))
                            })
                    
                    return {
                        'token': token,
                        'current_funding_rate': current_funding,
                        'mark_price': mark_price,
                        'open_interest': open_interest,
                        'notional_open_interest': notional_open_interest,
                        'historical_rates': historical_rates
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching funding data for {token}: {str(e)}")
            return None

    async def get_market_data(self):
        """Enhanced market data collection with fallback values"""
        try:
            # Fetch all required data in parallel with retries
            async def fetch_with_retry(payload, max_retries=3):
                for attempt in range(max_retries):
                    try:
                        data = await self.make_request(payload)
                        return data
                    except Exception as e:
                        logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                        await asyncio.sleep(1)
                return None

            prices_data = await fetch_with_retry({"type": "allMids"})
            stats_data = await fetch_with_retry({"type": "stats"})
            
            market_data = {}
            for market in (stats_data or []):
                try:
                    token = market.get('name', '')
                    if token and token in (prices_data or {}):
                        # Use defensive data extraction with fallbacks
                        market_data[token] = {
                            'mark_price': float(prices_data.get(token, 0) or 0),
                            'open_interest': float(market.get('oiUsd', 0) or 0),
                            'volume_24h': float(market.get('volUsd24h', 0) or 0),
                            'notional_open_interest': float(market.get('oiUsd', 0) or 0)
                        }
                except (ValueError, TypeError, KeyError) as e:
                    logger.warning(f"Error processing market {token}, using default values: {str(e)}")
                    market_data[token] = {
                        'mark_price': 0.0,
                        'open_interest': 0.0,
                        'volume_24h': 0.0,
                        'notional_open_interest': 0.0
                    }

            return market_data, stats_data

        except Exception as e:
            logger.error(f"Market data collection error: {str(e)}")
            return {}, []

    async def collect_funding_data(self):
        """Resilient funding data collection"""
        try:
            markets = await self.get_all_markets()
            if not markets:
                logger.warning("No markets found, but continuing...")
                markets = []

            predicted_rates = await self.get_predicted_funding_rates()
            market_data, _ = await self.get_market_data()

            funding_data = []
            timestamp = datetime.now(datetime.UTC)

            async def process_market_batch(batch_tokens):
                batch_data = []
                for token in batch_tokens:
                    try:
                        info = market_data.get(token, {
                            'mark_price': 0.0,
                            'open_interest': 0.0,
                            'volume_24h': 0.0,
                            'notional_open_interest': 0.0
                        })
                        
                        current_rate = await self.get_current_funding_rate(token)
                        predicted_rate = predicted_rates.get(token, 0)

                        batch_data.append({
                            'timestamp': timestamp.isoformat(),
                            'token': token,
                            'current_funding_rate': current_rate,
                            'predicted_funding_rate': predicted_rate,
                            'mark_price': info['mark_price'],
                            'open_interest': info['open_interest'],
                            'volume_24h': info['volume_24h'],
                            'notional_open_interest': info['notional_open_interest'],
                            'annualized_funding': current_rate * 365 * 100,
                            'funding_difference': predicted_rate - current_rate
                        })
                    except Exception as e:
                        logger.warning(f"Error processing {token}: {str(e)}")
                        # Add minimal data even if there's an error
                        batch_data.append({
                            'timestamp': timestamp.isoformat(),
                            'token': token,
                            'current_funding_rate': 0,
                            'predicted_funding_rate': 0,
                            'mark_price': 0,
                            'open_interest': 0,
                            'volume_24h': 0,
                            'notional_open_interest': 0,
                            'annualized_funding': 0,
                            'funding_difference': 0
                        })
                return batch_data

            # Process in batches with progress bar
            batches = [markets[i:i + self.batch_size] for i in range(0, len(markets), self.batch_size)]
            all_results = []
            
            with tqdm(total=len(markets), desc="Collecting market data") as pbar:
                for batch in batches:
                    results = await process_market_batch(batch)
                    all_results.extend(results)
                    pbar.update(len(batch))

            # Always save data, even if incomplete
            if all_results:
                timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_dir = "data/funding_rates"
                os.makedirs(output_dir, exist_ok=True)
                
                # Save raw data
                with open(f'{output_dir}/funding_raw_{timestamp_str}.json', 'w') as f:
                    json.dump(all_results, f, indent=2, default=str)
                
                logger.info(f"✅ Saved {len(all_results)} market records")
                return all_results
            else:
                logger.warning("No results collected, saving empty dataset")
                return []

        except Exception as e:
            logger.error(f"Error in collect_funding_data: {str(e)}")
            return []

    async def get_current_funding_rate(self, token: str) -> float:
        """Get current funding rate with caching"""
        cache_key = f"funding_rate_{token}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
            data = await self.make_request({
                "type": "fundingHistory",
                "coin": token,
                "startTime": int((datetime.now(datetime.UTC) - timedelta(hours=1)).timestamp() * 1000)
            })
            
            rate = float(data[0].get('funding', 0)) if data and len(data) > 0 else 0
            self.cache[cache_key] = rate
            return rate
        except Exception:
            return 0

async def main():
    output_dir = "data/funding_rates"
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        print("\n🌟 Starting Hyperliquid Funding Rate Collection 🌟\n")
        
        async with HyperliquidFundingCollector() as collector:
            # Test connection before proceeding
            if not await collector.test_connection():
                raise Exception("Failed to connect to Hyperliquid API")
            
            markets = await collector.get_all_markets()
            if not markets:
                raise Exception("No markets found")
                
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
        sys.exit(1)

def create_detailed_summary(summary, timestamp):
    return {
        'timestamp': datetime.now().isoformat(),
        'market_summary': {
            'total_markets': len(summary),
            'positive_funding_markets': len(summary[summary['current_funding_rate'] > 0]),
            'negative_funding_markets': len(summary[summary['current_funding_rate'] < 0]),
            'highest_predicted_funding': float(summary['predicted_funding_rate'].max()),
            'lowest_predicted_funding': float(summary['predicted_funding_rate'].min()),
            'highest_annual_funding': float(summary['annualized_funding'].max()),
            'lowest_annual_funding': float(summary['annualized_funding'].min()),
        },
        'funding_opportunities': {
            'highest_predicted_rates': summary.nlargest(5, 'predicted_funding_rate')[
                ['token', 'predicted_funding_rate', 'current_funding_rate', 'annualized_funding']
            ].to_dict('records'),
            'lowest_predicted_rates': summary.nsmallest(5, 'predicted_funding_rate')[
                ['token', 'predicted_funding_rate', 'current_funding_rate', 'annualized_funding']
            ].to_dict('records'),
            'highest_positive_current_rates': summary[summary['current_funding_rate'] > 0].nlargest(5, 'current_funding_rate')[
                ['token', 'current_funding_rate', 'predicted_funding_rate', 'annualized_funding']
            ].to_dict('records'),
            'largest_prediction_differences': summary.nlargest(5, 'rate_difference')[
                ['token', 'predicted_funding_rate', 'current_funding_rate', 'rate_difference']
            ].to_dict('records'),
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

    # Add predicted funding rate analysis
    print("🔮 Top 5 Highest Predicted Funding Rates:")
    print(tabulate(
        summary.nlargest(5, 'predicted_funding_rate')[
            ['token', 'predicted_funding_rate', 'current_funding_rate', 'annualized_funding']
        ],
        headers=['Token', 'Predicted Rate', 'Current Rate', 'Annual %'],
        floatfmt=".4f",
        tablefmt="pretty"
    ))

    print("\n📉 Top 5 Lowest Predicted Funding Rates:")
    print(tabulate(
        summary.nsmallest(5, 'predicted_funding_rate')[
            ['token', 'predicted_funding_rate', 'current_funding_rate', 'annualized_funding']
        ],
        headers=['Token', 'Predicted Rate', 'Current Rate', 'Annual %'],
        floatfmt=".4f",
        tablefmt="pretty"
    ))

    # Add largest predicted vs current differences
    print("\n💫 Largest Predicted vs Current Rate Differences:")
    summary['rate_difference'] = summary['predicted_funding_rate'] - summary['current_funding_rate']
    print(tabulate(
        summary.nlargest(5, 'rate_difference')[
            ['token', 'predicted_funding_rate', 'current_funding_rate', 'rate_difference']
        ],
        headers=['Token', 'Predicted Rate', 'Current Rate', 'Difference'],
        floatfmt=".4f",
        tablefmt="pretty"
    ))

    print("\n💰 Top 5 Highest Current Funding Rates (Annualized):")
    print(tabulate(
        summary[summary['current_funding_rate'] > 0].nlargest(5, 'annualized_funding')[
            ['token', 'current_funding_rate', 'predicted_funding_rate', 'annualized_funding']
        ],
        headers=['Token', 'Current Rate', 'Predicted Rate', 'Annual %'],
        floatfmt=".4f",
        tablefmt="pretty"
    ))

    print("\n📉 Output Files:")
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