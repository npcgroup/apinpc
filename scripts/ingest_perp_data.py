import asyncio
import aiohttp
import pandas as pd
from datetime import datetime, timedelta
import json
import os
import logging
from dotenv import load_dotenv

load_dotenv()

HYPERLIQUID_API = "https://api.hyperliquid.xyz/info"
DEXSCREENER_API = "https://api.dexscreener.com"
DEXSCREENER_ENDPOINTS = {
    'search': f"{DEXSCREENER_API}/latest/dex/search",
    'pairs': f"{DEXSCREENER_API}/latest/dex/pairs/solana",
    'orders': f"{DEXSCREENER_API}/orders/v1/solana"
}
SOLSCAN_API = "https://api.solscan.io/v2"

TOKENS = [
    "POPCAT", "WIF", "GOAT", "PNUT", 
    "CHILLGUY", "MOODENG", "MEW", "BRETT"
]

# Token addresses on Solana
TOKEN_ADDRESSES = {
    "POPCAT": "7GCihgDB8fe6KNjn2MYtkzZcRjQy3t9GHdC8uHYmW2hr", 
    "WIF": "EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm",
    "GOAT": "CzLSujWBLFsSjncfkh59rUFqvafWcY5tzedWJSuypump",
    "PNUT": "2qEHjDLDLbuBgRYvsxhc5D6uDWAivNFZGan56P1tpump",
    "CHILLGUY": "Df6yfrKC8kZE3KNkrHERKzAetSxbrWeniQfyJY4Jpump",
    "MOODENG": "ED5nyyWEzpPPiWimP8vYm7sD7TD3LAt3Q3gRTWHzPJBY",
    "MEW": "MEW1gQWJ3nEXg2qgERiKu7FAFj79PHvQVREQUzScPP5",
    "BRETT": "BRETTqYJxZ3qZzFrcJLtQwEqNRGZjxj7PvzjzwJhGXL"
}

SOLSCAN_API_KEY = os.getenv('SOLSCAN_API_KEY')
SOLSCAN_HEADERS = {
    'token': SOLSCAN_API_KEY,
    'Accept': 'application/json'
}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def save_debug_output(data, filename):
    """Save debug output to a file in the debug directory"""
    debug_dir = os.path.join('data', 'debug')
    os.makedirs(debug_dir, exist_ok=True)
    
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    filepath = os.path.join(debug_dir, f'{filename}_{timestamp}.json')
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Debug data saved to {filepath}")

def parse_hyperliquid_raw(raw_data):
    """Convert raw Hyperliquid data into a more readable format with token names"""
    
    # Extract universe and market data from raw response
    if not isinstance(raw_data, list) or len(raw_data) < 2:
        logger.error("Invalid Hyperliquid raw data format")
        return {}
        
    universe_data = raw_data[0].get('universe', [])
    market_data = raw_data[1]
    
    # Map market data to tokens
    token_markets = {}
    
    # Verify we have same number of markets as universe tokens
    if len(universe_data) != len(market_data):
        logger.warning(f"Mismatch in data lengths: {len(universe_data)} tokens vs {len(market_data)} markets")
    
    # Create mapping using universe order
    for idx, token_info in enumerate(universe_data):
        if idx >= len(market_data):
            break
            
        token = token_info.get('name')
        market = market_data[idx]
        
        token_markets[token] = {
            'funding_rate': market.get('funding'),
            'open_interest': market.get('openInterest'),
            'price_24h_ago': market.get('prevDayPx'),
            'volume_24h': market.get('dayNtlVlm'),
            'premium': market.get('premium'),
            'oracle_price': market.get('oraclePx'),
            'mark_price': market.get('markPx'),
            'mid_price': market.get('midPx'),
            'impact_prices': market.get('impactPxs'),
            'base_volume_24h': market.get('dayBaseVlm'),
            'decimals': token_info.get('szDecimals'),
            'max_leverage': token_info.get('maxLeverage'),
            'only_isolated': token_info.get('onlyIsolated', False)
        }
    
    # Save mapped data
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    debug_dir = os.path.join('data', 'debug')
    filepath = os.path.join(debug_dir, f'hyperliquid_mapped_{timestamp}.json')
    
    with open(filepath, 'w') as f:
        json.dump(token_markets, f, indent=2, sort_keys=True)
    logger.info(f"Mapped Hyperliquid data saved to {filepath}")
    
    # Also save a more readable format focusing on our tokens
    our_tokens = {
        token: data for token, data in token_markets.items() 
        if token in TOKENS
    }
    
    readable_filepath = os.path.join(debug_dir, f'hyperliquid_our_tokens_{timestamp}.json')
    with open(readable_filepath, 'w') as f:
        json.dump(our_tokens, f, indent=2, sort_keys=True)
    logger.info(f"Our tokens' data saved to {readable_filepath}")
    
    return token_markets

async def fetch_hyperliquid_data():
    try:
        async with aiohttp.ClientSession() as session:
            logger.info("Fetching data from Hyperliquid API...")
            
            # Get meta and market data in one call
            async with session.post(HYPERLIQUID_API, 
                json={"type": "metaAndAssetCtxs"}) as response:
                raw_data = await response.json()
                save_debug_output(raw_data, 'hyperliquid_raw')
                
                # Parse and map the raw data
                mapped_data = parse_hyperliquid_raw(raw_data)
                
            # Get funding rates
            async with session.post(HYPERLIQUID_API,
                json={"type": "fundingAll"}) as response:
                funding_data = await response.json()
                save_debug_output(funding_data, 'hyperliquid_funding_raw')
            
            # Process only our tokens
            markets = {}
            for token in TOKENS:
                try:
                    market = mapped_data.get(token, {})
                    funding = next((f for f in funding_data if f.get('coin') == token), None)
                    
                    if market or funding:
                        markets[token] = {
                            'funding_rate': float(funding.get('funding', 0)) if funding else 0,
                            'volume_24h': float(market.get('volume_24h', 0)),
                            'open_interest': float(market.get('open_interest', 0)),
                            'mark_price': float(market.get('mark_price', 0))
                        }
                        logger.info(f"Found market data for {token}: {markets[token]}")
                except Exception as e:
                    logger.error(f"Error processing {token}: {e}")
                    markets[token] = {
                        'funding_rate': 0,
                        'volume_24h': 0,
                        'open_interest': 0,
                        'mark_price': 0
                    }
            
            return markets

    except Exception as e:
        logger.error(f"Error in fetch_hyperliquid_data: {e}")
        logger.exception(e)
        return {}

async def fetch_dexscreener_data(token_addresses):
    results = {}
    all_responses = {}
    
    async with aiohttp.ClientSession() as session:
        for symbol, address in token_addresses.items():
            try:
                # 1. First get all pairs for the token
                search_url = f"{DEXSCREENER_ENDPOINTS['search']}?q={address}"
                logger.info(f"Fetching DexScreener pairs for {symbol} from {search_url}")
                
                async with session.get(search_url) as response:
                    if response.status == 200:
                        search_data = await response.json()
                        all_responses[f"{symbol}_search"] = search_data
                        
                        if 'pairs' in search_data and search_data['pairs']:
                            # Filter Solana pairs and sort by liquidity
                            solana_pairs = [p for p in search_data['pairs'] if p.get('chainId') == 'solana']
                            if solana_pairs:
                                # Get the pair with highest liquidity
                                pair = max(solana_pairs, key=lambda p: float(p.get('liquidity', {}).get('usd', 0) or 0))
                                pair_address = pair.get('pairAddress')
                                
                                # 2. Get detailed pair data
                                if pair_address:
                                    pair_url = f"{DEXSCREENER_ENDPOINTS['pairs']}/{pair_address}"
                                    async with session.get(pair_url) as pair_response:
                                        if pair_response.status == 200:
                                            pair_data = await pair_response.json()
                                            all_responses[f"{symbol}_pair"] = pair_data
                                
                                # 3. Get order data for token
                                orders_url = f"{DEXSCREENER_ENDPOINTS['orders']}/{address}"
                                async with session.get(orders_url) as orders_response:
                                    if orders_response.status == 200:
                                        orders_data = await orders_response.json()
                                        all_responses[f"{symbol}_orders"] = orders_data
                                
                                # Combine all data
                                results[symbol] = {
                                    'spot_price': float(pair.get('priceUsd', 0)),
                                    'spot_volume_24h': float(pair.get('volume', {}).get('h24', 0)),
                                    'liquidity': float(pair.get('liquidity', {}).get('usd', 0)),
                                    'holder_count': estimate_holder_count(
                                        pair_data.get('pair', {}),
                                        orders_data
                                    ),
                                    'market_cap': float(pair.get('fdv', 0)),
                                    'total_supply': float(pair.get('liquidity', {}).get('base', 0)),
                                    'price_change_24h': float(pair.get('priceChange', {}).get('h24', 0)),
                                    'txns_24h': sum([
                                        int(pair.get('txns', {}).get('h24', {}).get('buys', 0)),
                                        int(pair.get('txns', {}).get('h24', {}).get('sells', 0))
                                    ])
                                }
                                logger.info(f"Got DexScreener data for {symbol}: {results[symbol]}")
                
            except Exception as e:
                logger.error(f"Error fetching DexScreener data for {symbol}: {e}")
                results[symbol] = {
                    'spot_price': 0,
                    'spot_volume_24h': 0,
                    'liquidity': 0,
                    'holder_count': 0,
                    'market_cap': 0,
                    'total_supply': 0,
                    'price_change_24h': 0,
                    'txns_24h': 0
                }
    
    # Save raw responses
    save_debug_output(all_responses, 'dexscreener_raw')
    
    # Save readable format
    readable_filepath = os.path.join('data', 'debug', f'dexscreener_readable_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.json')
    with open(readable_filepath, 'w') as f:
        json.dump(results, f, indent=2, sort_keys=True)
    logger.info(f"Readable DexScreener data saved to {readable_filepath}")
    
    return results

def estimate_holder_count(pair_data, orders_data):
    """Estimate holder count from pair and order data"""
    unique_addresses = set()
    
    # Add liquidity providers from pair data
    if 'liquidityProviders' in pair_data:
        for lp in pair_data.get('liquidityProviders', []):
            if 'address' in lp:
                unique_addresses.add(lp['address'])
    
    # Add unique traders from orders
    if 'orders' in orders_data:
        for order in orders_data.get('orders', []):
            if 'maker' in order:
                unique_addresses.add(order['maker'])
            if 'taker' in order:
                unique_addresses.add(order['taker'])
    
    # Add any other unique addresses from transactions
    if 'transactions' in pair_data:
        for tx in pair_data.get('transactions', []):
            if 'from' in tx:
                unique_addresses.add(tx['from'])
            if 'to' in tx:
                unique_addresses.add(tx['to'])
    
    # Return total unique addresses found
    return len(unique_addresses)

async def fetch_solscan_data(token_addresses):
    results = {}
    all_responses = {}
    
    async with aiohttp.ClientSession(headers=SOLSCAN_HEADERS) as session:
        for symbol, address in token_addresses.items():
            try:
                # Get token metadata and holder stats
                meta_url = f"{SOLSCAN_API}/token/{address}"
                holders_url = f"{SOLSCAN_API}/token/holders/{address}"
                
                logger.info(f"Fetching Solscan metadata for {symbol} from {meta_url}")
                
                # Get metadata
                async with session.get(meta_url) as response:
                    if response.status == 200:
                        meta_data = await response.json()
                        all_responses[f"{symbol}_meta"] = meta_data
                        
                        # Get holder stats
                        async with session.get(holders_url) as holder_response:
                            if holder_response.status == 200:
                                holder_data = await holder_response.json()
                                all_responses[f"{symbol}_holders"] = holder_data
                                
                                results[symbol] = {
                                    'holder_count': int(holder_data.get('total', 0)),
                                    'symbol': meta_data.get('symbol', ''),
                                    'name': meta_data.get('name', ''),
                                    'decimals': meta_data.get('decimals', 0),
                                    'supply': meta_data.get('supply', 0),
                                    'volume_24h': float(meta_data.get('volume24h', 0)),
                                    'price_usd': float(meta_data.get('priceUsd', 0)),
                                    'market_cap': float(meta_data.get('marketCapUsd', 0)),
                                    'top_holders': holder_data.get('data', [])[:10]  # Get top 10 holders
                                }
                                logger.info(f"Got Solscan data for {symbol}: {results[symbol]}")
                            else:
                                logger.warning(f"Failed to get Solscan holder data for {symbol}: {holder_response.status}")
                                results[symbol] = {'holder_count': 0}
                    else:
                        logger.warning(f"Failed to get Solscan metadata for {symbol}: {response.status}")
                        results[symbol] = {'holder_count': 0}
                        
            except Exception as e:
                logger.error(f"Error fetching Solscan data for {symbol}: {e}")
                results[symbol] = {'holder_count': 0}
                
    # Save raw responses
    save_debug_output(all_responses, 'solscan_raw')
    
    # Save a more readable format
    readable_filepath = os.path.join('data', 'debug', f'solscan_readable_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.json')
    with open(readable_filepath, 'w') as f:
        json.dump(results, f, indent=2, sort_keys=True)
    logger.info(f"Readable Solscan data saved to {readable_filepath}")
    
    return results

async def verify_hyperliquid_markets():
    try:
        async with aiohttp.ClientSession() as session:
            # Get meta info first
            async with session.post(HYPERLIQUID_API, 
                json={"type": "meta"}) as response:
                meta = await response.json()
                logger.info(f"Available markets in meta: {meta}")
                
            # Get all coins
            coins = []
            if isinstance(meta, dict):
                for coin in meta.get('universe', []):
                    coins.append(coin.get('name'))
                    
            logger.info(f"All available coins: {coins}")
            
            # Check which of our tokens exist
            for token in TOKENS:
                if token in coins:
                    logger.info(f"✅ {token} found in Hyperliquid markets")
                else:
                    logger.warning(f"❌ {token} not found in Hyperliquid markets")
                    
            return coins
                    
    except Exception as e:
        logger.error(f"Error verifying markets: {e}")
        return []

def save_all_data(combined_data, hl_data, dex_data, holder_data):
    """Save all data to separate files"""
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    data_dir = 'data'
    os.makedirs(data_dir, exist_ok=True)

    # Save combined metrics
    with open(os.path.join(data_dir, 'perp_metrics.json'), 'w') as f:
        json.dump(combined_data, f, indent=2)

    # Save raw data from each source
    raw_data = {
        'timestamp': timestamp,
        'hyperliquid': hl_data,
        'dexscreener': dex_data,
        'solscan': holder_data,
        'combined': combined_data
    }
    
    with open(os.path.join(data_dir, f'all_data_{timestamp}.json'), 'w') as f:
        json.dump(raw_data, f, indent=2)

    logger.info(f"All data saved to data/all_data_{timestamp}.json")
    logger.info("Combined metrics saved to data/perp_metrics.json")

async def main():
    try:
        logger.info("Starting data collection...")
        
        # Verify Hyperliquid markets
        logger.info("Verifying Hyperliquid markets...")
        available_markets = await verify_hyperliquid_markets()
        logger.info(f"Available markets: {available_markets}")
        
        # Fetch data from all sources
        logger.info("Fetching Hyperliquid data...")
        hl_data = await fetch_hyperliquid_data()
        logger.info(f"Hyperliquid data fetched: {hl_data}")
        
        logger.info("Fetching DexScreener data...")
        dex_data = await fetch_dexscreener_data(TOKEN_ADDRESSES)
        logger.info(f"DexScreener data fetched: {dex_data}")
        
        logger.info("Fetching Solscan data...")
        holder_data = await fetch_solscan_data(TOKEN_ADDRESSES)
        logger.info(f"Solscan data fetched: {holder_data}")

        # Combine data
        combined_data = []
        timestamp = datetime.utcnow()

        for token in TOKENS:
            metric = {
                "symbol": token,
                "timestamp": timestamp.isoformat(),
                **(hl_data.get(token, {
                    'funding_rate': 0,
                    'volume_24h': 0,
                    'open_interest': 0,
                    'mark_price': 0
                })),
                **(dex_data.get(token, {
                    'spot_price': 0,
                    'spot_volume_24h': 0,
                    'liquidity': 0
                })),
                **(holder_data.get(token, {
                    'holder_count': 0
                }))
            }
            combined_data.append(metric)
            logger.info(f"Combined data for {token}")

        # Save all data
        save_all_data(combined_data, hl_data, dex_data, holder_data)

    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 