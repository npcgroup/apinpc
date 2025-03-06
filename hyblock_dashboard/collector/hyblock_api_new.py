import os
import sys
import json
import time
import asyncio
import requests
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.database import get_logger
from utils.api_parser import get_all_endpoints, get_required_params

# Load environment variables
load_dotenv()

# Set up logger
logger = get_logger("hyblock_api")

# API configuration
API_BASE_URL = "https://api1.hyblockcapital.com/v1"
API_KEY = os.getenv("HYBLOCK_API_KEY", "")
BEARER_TOKEN = os.getenv("HYBLOCK_BEARER_TOKEN", "")
CLIENT_ID = os.getenv("HYBLOCK_CLIENT_ID", "")

# Default parameters for API requests
DEFAULT_COINS = ["SUI", "BTC", "ETH", "SOL", "AVAX", "BNB", "XRP", "ADA", "DOGE", "DOT"]
DEFAULT_EXCHANGES = ["BINANCE", "BYBIT", "COINBASE", "KRAKEN", "KUCOIN", "OKEX"]
DEFAULT_TIMEFRAMES = ["1m", "5m", "15m", "1h", "4h", "1d"]

class HyblockAPI:
    def __init__(self):
        self.base_url = API_BASE_URL
        self.api_key = API_KEY
        self.bearer_token = BEARER_TOKEN
        self.client_id = CLIENT_ID
        self.endpoints = get_all_endpoints()
        
        if not self.api_key:
            logger.warning("HYBLOCK_API_KEY not set in environment variables")
        
        if not self.bearer_token:
            logger.warning("HYBLOCK_BEARER_TOKEN not set in environment variables")
        
        if not self.client_id:
            logger.warning("HYBLOCK_CLIENT_ID not set in environment variables")
    
    async def initialize(self):
        """Initialize the API client"""
        return self
    
    async def close(self):
        """Close the API client"""
        pass
    
    async def fetch_endpoint(self, endpoint_name, params=None):
        """Fetch data from the specified endpoint with the given parameters"""
        if endpoint_name not in self.endpoints:
            logger.error(f"Unknown endpoint: {endpoint_name}")
            return None
        
        endpoint_info = self.endpoints[endpoint_name]
        endpoint_path = endpoint_info['path']
        
        # Check required parameters
        required_params = get_required_params(endpoint_info)
        if params is None:
            params = {}
        
        for param in required_params:
            if param not in params:
                logger.error(f"Missing required parameter '{param}' for endpoint '{endpoint_name}'")
                return None
        
        # Fix the endpoint path - remove the 'market/' prefix if it exists
        if endpoint_path.startswith('/market/'):
            endpoint_path = endpoint_path.replace('/market/', '/')
        
        # Add sort and limit parameters if not already present
        if 'sort' not in params:
            params['sort'] = 'asc'
        if 'limit' not in params:
            params['limit'] = 50
        
        # Use the exact same approach as in test_curl.py
        url = f"{self.base_url}{endpoint_path}"
        
        # Use the exact same headers format as in test_curl.py
        headers = {
            "accept": "application/json",
            "authorization": f"Bearer {self.bearer_token}",
            "x-api-key": self.api_key
        }
        
        try:
            logger.debug(f"Fetching {endpoint_name} with params: {params}")
            logger.debug(f"Using headers: {headers}")
            logger.debug(f"URL: {url}")
            
            response = requests.get(url, params=params, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "endpoint": endpoint_name,
                    "params": params,
                    "data": data,
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                logger.error(f"Error fetching {endpoint_name}: {response.status_code} - {response.text}")
                
                # Special handling for asksIncreaseDecrease endpoint which seems to work differently
                if endpoint_name == "asksIncreaseDecrease":
                    # Try without the authorization header
                    headers_no_auth = {
                        "accept": "application/json",
                        "x-api-key": self.api_key
                    }
                    
                    response_no_auth = requests.get(url, params=params, headers=headers_no_auth)
                    
                    if response_no_auth.status_code == 200:
                        data = response_no_auth.json()
                        logger.info(f"Successfully fetched {endpoint_name} without authorization header")
                        return {
                            "endpoint": endpoint_name,
                            "params": params,
                            "data": data,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                
                return None
        
        except Exception as e:
            logger.error(f"Exception fetching {endpoint_name}: {e}")
            return None
    
    async def fetch_all_for_coin(self, coin, exchanges=None, timeframes=None):
        """Fetch data from all endpoints for a specific coin"""
        if exchanges is None:
            exchanges = DEFAULT_EXCHANGES
        
        if timeframes is None:
            timeframes = DEFAULT_TIMEFRAMES
        
        results = []
        
        for endpoint_name, endpoint_info in self.endpoints.items():
            # Check if the endpoint requires a coin parameter
            has_coin_param = any(param.get('name') == 'coin' for param in endpoint_info.get('parameters', []))
            
            if has_coin_param:
                # Prepare parameters
                params = {"coin": coin}
                
                # Check if the endpoint requires an exchange parameter
                has_exchange_param = any(param.get('name') == 'exchange' for param in endpoint_info.get('parameters', []))
                
                # Check if the endpoint requires a timeframe parameter
                has_timeframe_param = any(param.get('name') == 'timeframe' for param in endpoint_info.get('parameters', []))
                
                if has_exchange_param and has_timeframe_param:
                    # Fetch for each exchange and timeframe combination
                    for exchange in exchanges:
                        for timeframe in timeframes:
                            params.update({"exchange": exchange, "timeframe": timeframe})
                            result = await self.fetch_endpoint(endpoint_name, params)
                            if result:
                                results.append(result)
                            # Add a small delay to avoid rate limiting
                            await asyncio.sleep(0.1)
                
                elif has_exchange_param:
                    # Fetch for each exchange
                    for exchange in exchanges:
                        params.update({"exchange": exchange})
                        result = await self.fetch_endpoint(endpoint_name, params)
                        if result:
                            results.append(result)
                        # Add a small delay to avoid rate limiting
                        await asyncio.sleep(0.1)
                
                elif has_timeframe_param:
                    # Fetch for each timeframe
                    for timeframe in timeframes:
                        params.update({"timeframe": timeframe})
                        result = await self.fetch_endpoint(endpoint_name, params)
                        if result:
                            results.append(result)
                        # Add a small delay to avoid rate limiting
                        await asyncio.sleep(0.1)
                
                else:
                    # Fetch with just the coin parameter
                    result = await self.fetch_endpoint(endpoint_name, params)
                    if result:
                        results.append(result)
                    # Add a small delay to avoid rate limiting
                    await asyncio.sleep(0.1)
        
        return results

async def test_api():
    """Test the Hyblock API client"""
    api = await HyblockAPI().initialize()
    
    try:
        # Test a specific endpoint with the exact parameters from the curl command
        result = await api.fetch_endpoint('market/open_interest', {
            'coin': 'BTC',
            'timeframe': '15m',
            'exchange': 'BINANCE',
            'sort': 'asc',
            'limit': 50
        })
        
        if result:
            print(f"Successfully fetched data from market/open_interest endpoint")
            print(f"Data sample: {json.dumps(result['data'])[:500]}...")
        else:
            print("Failed to fetch data from market/open_interest endpoint")
        
        # Fetch data for SUI from a few endpoints
        results = await api.fetch_all_for_coin("SUI", exchanges=["BINANCE"], timeframes=["1h"])
        
        print(f"Fetched {len(results)} results")
        
        # Print the first result
        if results:
            print(f"\nSample result from {results[0]['endpoint']}:")
            print(json.dumps(results[0]['data'], indent=2)[:500] + "...")
    
    finally:
        await api.close()

if __name__ == "__main__":
    asyncio.run(test_api()) 