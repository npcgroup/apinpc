#!/usr/bin/env python3
"""
Hyblock Data Collector

This script collects data from the Hyblock API for various crypto metrics
and stores it in a PostgreSQL database.
"""

import os
import sys
import json
import time
import logging
import requests
import schedule
from datetime import datetime, timedelta
import concurrent.futures
from typing import Dict, List, Any, Optional, Tuple
import threading
from dotenv import load_dotenv
import random

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.database import connect_to_database, execute_query, get_logger

# Set up logger
logger = get_logger("hyblock_collector")

# Configuration
API_BASE_URL = "https://api1.hyblockcapital.com/v1"
AUTH_BASE_URL = "https://auth-api.hyblockcapital.com/oauth2/token"
API_KEY = os.environ.get("HYBLOCK_API_KEY", "")
CLIENT_ID = os.environ.get("HYBLOCK_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("HYBLOCK_CLIENT_SECRET", "")
ACCESS_TOKEN = None
TOKEN_EXPIRY = 0  # Unix timestamp when token expires
CATALOG_FILE = "catalog.json"
MAX_WORKERS = 10  # Increased from 5 to 10 for better parallelization
RATE_LIMIT_DELAY = 0.5  # Reduced from 1 to 0.5 seconds
MAX_RETRIES = 3  # Maximum number of retries for failed API requests
RETRY_DELAY = 2  # Base delay between retries in seconds

# Metric categories and endpoints
METRICS = {
    "orderbook": [
        "asksIncreaseDecrease",
        "bidAsk",
        "bidsIncreaseDecrease",
        "bidAskRatio",
        "bidAskDelta",
        "bidAskRatioDiff",
        "combinedBook",
        "bidsAskSpread"
    ],
    "options": [
        "bvol",
        "dvol"
    ],
    "orderflow": [
        "botTracker",
        "buyVolume",
        "klines",
        "sellVolume",
        "volumeDelta",
        "anchoredCVD",
        "marketOrderCount",
        "limitOrderCount",
        "marketOrderAverageSize",
        "limitOrderAverageSize",
        "pdLevels",
        "pwLevels",
        "pmLevels",
        "slippage",
        "transferofcontracts",
        "participationratio"
    ],
    "open_interest": [
        "openInterest",
        "openInterestDelta",
        "anchoredOIDelta",
        "openInterestProfile"
    ],
    "liquidity": [
        "cumulativeLiqLevel",
        "liquidationLevels",
        "liquidation",
        "liquidationHeatmap",
        "averageLeverageUsed",
        "averageLeverageDelta",
        "anchoredLLC",
        "anchoredLLS",
        "anchoredCLLCD",
        "anchoredCLLSD"
    ],
    "funding_rate": [
        "fundingRate"
    ],
    "long_short": [
        "binanceGlobalAccounts",
        "anchoredBinanceGlobalAccounts",
        "binanceTopTraderAccounts",
        "anchoredBinanceTopTraderAccounts",
        "binanceTopTraderPositions",
        "anchoredBinanceTopTraderPositions",
        "binanceTrueRetailLongShort",
        "binanceWhaleRetailDelta",
        "anchoredBinanceWhaleRetailDelta",
        "traderSentimentGap",
        "whalePositionDominance",
        "bybitGlobalAccounts",
        "huobiTopTraderAccounts",
        "huobiTopTraderAccountsQuarterly",
        "huobiTopTraderPositions",
        "huobiTopTraderPositionsQuarterly",
        "netLongShort",
        "anchoredCLS",
        "netLongShortDelta",
        "anchoredCLSD",
        "okxGlobalAccounts",
        "okxTopTraderAccounts",
        "okxWhaleRetailDelta"
    ],
    "sentiment": [
        "bitmexLeaderboardNotionalProfit",
        "bitmexLeaderboardROEProfit",
        "fearAndGreed",
        "marginLendingRatio",
        "trollbox",
        "userBotRatio",
        "stablecoinPremiumP2P",
        "wbtcMintBurn"
    ],
    "profile": [
        "openInterestProfile",
        "volumeProfile"
    ],
    "catalog": [
        "catalog"
    ],
    "api_usage": [
        "remainingHitBalance"
    ]
}

# Timeframes to collect data for
TIMEFRAMES = ["1m", "5m", "15m", "1h", "4h", "1d"]

# Exchanges with good API support
PRIORITY_EXCHANGES = [
    "binance",
    "bybit",
    "coinbase",
    "deribit",
    "okx"
]

# Database connection pool
db_connection_pool = []
DB_POOL_SIZE = 10  # Increased from 5 to 10 for better parallelization
DB_POOL_LOCK = threading.Lock()
DB_POOL_TIMEOUT = 30  # Seconds to wait for a connection before timing out

# Collection statistics
collection_stats = {}
STATS_LOCK = threading.Lock()

# Load compatibility configuration
def load_compatibility_config() -> Dict[str, Any]:
    """Load the endpoint compatibility configuration."""
    try:
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "endpoint_compatibility.json")
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Loaded compatibility configuration from {config_path}")
            return config
        else:
            logger.warning(f"Compatibility configuration file not found: {config_path}")
            return {
                "endpoint_exchange_compatibility": {},
                "default_compatibility": {
                    "supported_exchanges": PRIORITY_EXCHANGES,
                    "supported_coins": []
                }
            }
    except Exception as e:
        logger.error(f"Error loading compatibility configuration: {e}")
        return {
            "endpoint_exchange_compatibility": {},
            "default_compatibility": {
                "supported_exchanges": PRIORITY_EXCHANGES,
                "supported_coins": []
            }
        }

# Global compatibility configuration
COMPATIBILITY_CONFIG = load_compatibility_config()

def is_compatible(endpoint: str, coin: str, exchange: str) -> bool:
    """Check if the endpoint, coin, and exchange combination is compatible."""
    # Get endpoint-specific compatibility if available
    endpoint_config = COMPATIBILITY_CONFIG.get("endpoint_exchange_compatibility", {}).get(endpoint)
    
    if endpoint_config:
        # Check if exchange is supported for this endpoint
        supported_exchanges = endpoint_config.get("supported_exchanges", [])
        if supported_exchanges and supported_exchanges != ["all"] and exchange.lower() not in [ex.lower() for ex in supported_exchanges]:
            logger.debug(f"Exchange {exchange} not supported for endpoint {endpoint}")
            return False
        
        # Check if coin is supported for this endpoint
        supported_coins = endpoint_config.get("supported_coins", [])
        if supported_coins and coin.upper() not in [c.upper() for c in supported_coins]:
            logger.debug(f"Coin {coin} not supported for endpoint {endpoint}")
            return False
        
        return True
    else:
        # Fall back to default compatibility
        default_config = COMPATIBILITY_CONFIG.get("default_compatibility", {})
        
        # Check if exchange is supported by default
        supported_exchanges = default_config.get("supported_exchanges", [])
        if supported_exchanges and supported_exchanges != ["all"] and exchange.lower() not in [ex.lower() for ex in supported_exchanges]:
            logger.debug(f"Exchange {exchange} not supported by default")
            return False
        
        # Check if coin is supported by default
        supported_coins = default_config.get("supported_coins", [])
        if supported_coins and coin.upper() not in [c.upper() for c in supported_coins]:
            logger.debug(f"Coin {coin} not supported by default")
            return False
        
        return True

# Initialize connection pool
def init_db_pool():
    """Initialize the database connection pool"""
    global db_connection_pool
    with DB_POOL_LOCK:
        for _ in range(DB_POOL_SIZE):
            conn = connect_to_database()
            if conn:
                db_connection_pool.append(conn)
                logger.debug(f"Added connection to pool, size: {len(db_connection_pool)}")
            else:
                logger.error("Failed to create database connection for pool")

# Get a connection from the pool
def get_db_connection():
    """Get a database connection from the pool or create a new one if needed"""
    global db_connection_pool
    conn = None
    start_time = time.time()
    
    while time.time() - start_time < DB_POOL_TIMEOUT:
        with DB_POOL_LOCK:
            if db_connection_pool:
                conn = db_connection_pool.pop()
                logger.debug(f"Got connection from pool, remaining: {len(db_connection_pool)}")
                break
            else:
                logger.debug("Pool empty, waiting for a connection to become available")
        
        # Wait a bit before trying again
        time.sleep(0.1)
    
    # If we still don't have a connection, create a new one
    if not conn:
        logger.debug("Pool empty or timed out, creating new connection")
        conn = connect_to_database()
    
    # Test if connection is valid
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        except Exception as e:
            logger.warning(f"Connection test failed, creating new connection: {e}")
            try:
                conn.close()
            except:
                pass
            conn = connect_to_database()
    
    return conn

# Return a connection to the pool
def return_db_connection(conn):
    """Return a database connection to the pool"""
    global db_connection_pool
    if not conn:
        return
    
    try:
        # Test if connection is still valid
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        
        # Connection is valid, return to pool
        with DB_POOL_LOCK:
            if len(db_connection_pool) < DB_POOL_SIZE:
                db_connection_pool.append(conn)
                logger.debug(f"Returned connection to pool, size: {len(db_connection_pool)}")
            else:
                conn.close()
                logger.debug("Pool full, closed connection")
    except Exception as e:
        # Connection is invalid, close it
        logger.warning(f"Invalid connection, closing: {e}")
        try:
            conn.close()
        except:
            pass

def load_catalog() -> Dict[str, List[str]]:
    """Load the catalog of available coins for each exchange."""
    try:
        if not os.path.exists(CATALOG_FILE):
            logger.warning(f"Catalog file not found: {CATALOG_FILE}")
            return {}
        
        with open(CATALOG_FILE, 'r') as f:
            catalog_data = json.load(f)
        
        return catalog_data.get("data", {})
    except Exception as e:
        logger.error(f"Error loading catalog: {e}")
        return {}

def get_access_token() -> str:
    """Get a new access token from the Hyblock API."""
    global ACCESS_TOKEN, TOKEN_EXPIRY
    
    # Check if we have a valid token
    current_time = int(time.time())
    if ACCESS_TOKEN and TOKEN_EXPIRY > current_time + 300:  # Token still valid for at least 5 minutes
        return ACCESS_TOKEN
    
    try:
        logger.info("Getting new access token")
        
        # Prepare the request
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'client_credentials',
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }
        
        response = requests.post(AUTH_BASE_URL, headers=headers, data=data, timeout=10)
        
        if response.status_code == 200:
            token_data = response.json()
            ACCESS_TOKEN = token_data.get('access_token')
            # Set expiry time (tokens usually valid for 1 day)
            expires_in = token_data.get('expires_in', 86400)  # Default to 24 hours
            TOKEN_EXPIRY = current_time + expires_in
            
            logger.info(f"Got new access token, valid until {datetime.fromtimestamp(TOKEN_EXPIRY)}")
            return ACCESS_TOKEN
        else:
            logger.error(f"Failed to get access token: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error getting access token: {e}")
        return None

def fetch_data(endpoint: str, coin: str, exchange: str = None, timeframe: str = None) -> Optional[Dict[str, Any]]:
    """Fetch data from the Hyblock API for a specific endpoint, coin, exchange, and timeframe."""
    global collection_stats
    
    # Check compatibility before making API call
    if exchange and not is_compatible(endpoint, coin, exchange):
        logger.info(f"Skipping incompatible combination: {endpoint} - {coin} - {exchange}")
        
        # Update collection stats
        with STATS_LOCK:
            key = f"{endpoint}_{coin}_{exchange}_{timeframe}"
            if key not in collection_stats:
                collection_stats[key] = {
                    "success": 0,
                    "failure": 0,
                    "last_success": None,
                    "last_failure": None,
                    "last_error": None,
                    "skipped": 0
                }
            collection_stats[key]["skipped"] = collection_stats[key].get("skipped", 0) + 1
        
        return None
    
    # Get access token
    token = get_access_token()
    if not token:
        logger.error("Failed to get access token")
        return None
    
    # Build URL and parameters
    url = f"{API_BASE_URL}/{endpoint}"
    params = {
        "coin": coin.upper(),
        "sort": "asc",
        "limit": 50  # Fetch up to 50 data points
    }
    
    # Add exchange parameter if provided
    if exchange:
        params["exchange"] = exchange.upper()
    
    # Add timeframe parameter if provided and handle time ranges based on timeframe
    end_time = int(time.time())  # Current time in seconds
    
    if timeframe:
        params["timeframe"] = timeframe
        
        # Adjust the time range based on the timeframe to get appropriate amount of data
        # For smaller timeframes, we fetch less historical data to avoid excessive data points
        if timeframe in ["1m", "3m", "5m", "15m"]:
            # For minute-level timeframes, fetch past 24 hours
            start_time = end_time - (24 * 60 * 60)
        elif timeframe in ["30m", "1h", "2h", "4h"]:
            # For hour-level timeframes, fetch past 7 days
            start_time = end_time - (7 * 24 * 60 * 60)
        elif timeframe in ["6h", "8h", "12h"]:
            # For larger hour-level timeframes, fetch past 14 days
            start_time = end_time - (14 * 24 * 60 * 60)
        else:
            # For day-level timeframes (1d, 3d, 1w, etc.), fetch past 30 days
            start_time = end_time - (30 * 24 * 60 * 60)
    else:
        # Default to 30 days if no timeframe specified
        start_time = end_time - (30 * 24 * 60 * 60)
    
    # Add time range parameters
    params["startTime"] = str(start_time)
    params["endTime"] = str(end_time)
    
    logger.debug(f"Time range for {endpoint} {timeframe}: {datetime.fromtimestamp(start_time)} to {datetime.fromtimestamp(end_time)}")
    
    # Set up headers
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {token}",
        "x-api-key": API_KEY
    }
    
    logger.debug(f"Using headers: {headers}")
    logger.debug(f"Fetching {endpoint} with params: {params}")
    
    # Implement exponential backoff for retries
    retry_count = 0
    max_retries = MAX_RETRIES
    base_delay = RETRY_DELAY
    
    while retry_count <= max_retries:
        try:
            # Make the request
            response = requests.get(url, params=params, headers=headers, timeout=30)
            
            # Check if the request was successful
            if response.status_code == 200:
                # Parse the response
                data = response.json()
                
                # Update collection stats
                with STATS_LOCK:
                    key = f"{endpoint}_{coin}_{exchange}_{timeframe}"
                    if key not in collection_stats:
                        collection_stats[key] = {
                            "success": 0,
                            "failure": 0,
                            "last_success": None,
                            "last_failure": None,
                            "last_error": None,
                            "skipped": 0
                        }
                    collection_stats[key]["success"] += 1
                    collection_stats[key]["last_success"] = datetime.now().isoformat()
                
                # Add a small delay to avoid hitting rate limits
                time.sleep(RATE_LIMIT_DELAY)
                
                return data
            else:
                # Log the error
                error_msg = f"{response.status_code} - {response.text}"
                logger.warning(f"Failed to fetch data for {endpoint} - {coin} - {exchange} - {timeframe}: {error_msg}")
                
                # Update collection stats
                with STATS_LOCK:
                    key = f"{endpoint}_{coin}_{exchange}_{timeframe}"
                    if key not in collection_stats:
                        collection_stats[key] = {
                            "success": 0,
                            "failure": 0,
                            "last_success": None,
                            "last_failure": None,
                            "last_error": None,
                            "skipped": 0
                        }
                    collection_stats[key]["failure"] += 1
                    collection_stats[key]["last_failure"] = datetime.now().isoformat()
                    collection_stats[key]["last_error"] = error_msg
                
                # If we get a 400 error with "Invalid coin" or "Invalid exchange", update compatibility config
                if response.status_code == 400 and ("Invalid coin" in response.text or "Invalid exchange" in response.text):
                    logger.info(f"Adding incompatible combination to blocklist: {endpoint} - {coin} - {exchange}")
                    # This is a permanent error, no need to retry
                    return None
                
                # Check if we should retry based on the status code
                if response.status_code in [429, 500, 502, 503, 504]:
                    # These status codes indicate temporary issues that might be resolved by retrying
                    retry_count += 1
                    if retry_count <= max_retries:
                        # Calculate delay with exponential backoff and jitter
                        delay = base_delay * (2 ** (retry_count - 1)) + (random.random() * 0.5)
                        logger.info(f"Retrying in {delay:.2f} seconds (attempt {retry_count}/{max_retries})...")
                        time.sleep(delay)
                        continue
                
                # For other status codes or if we've exhausted retries, return None
                return None
        
        except requests.exceptions.RequestException as e:
            # Log the error
            logger.error(f"Request error for {endpoint} - {coin} - {exchange} - {timeframe}: {e}")
            
            # Update collection stats
            with STATS_LOCK:
                key = f"{endpoint}_{coin}_{exchange}_{timeframe}"
                if key not in collection_stats:
                    collection_stats[key] = {
                        "success": 0,
                        "failure": 0,
                        "last_success": None,
                        "last_failure": None,
                        "last_error": None,
                        "skipped": 0
                    }
                collection_stats[key]["failure"] += 1
                collection_stats[key]["last_failure"] = datetime.now().isoformat()
                collection_stats[key]["last_error"] = str(e)
            
            # Retry for network-related errors
            retry_count += 1
            if retry_count <= max_retries:
                # Calculate delay with exponential backoff and jitter
                delay = base_delay * (2 ** (retry_count - 1)) + (random.random() * 0.5)
                logger.info(f"Retrying in {delay:.2f} seconds (attempt {retry_count}/{max_retries})...")
                time.sleep(delay)
                continue
            
            return None
    
    # If we've exhausted all retries, return None
    return None

def store_data_in_hyblock_table(endpoint: str, coin: str, exchange: str, timeframe: str, data: Dict[str, Any]) -> bool:
    """Store the raw data in the hyblock_data table."""
    max_retries = 3
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        conn = None
        try:
            # Get a connection from the pool
            conn = get_db_connection()
            if not conn:
                logger.error(f"Failed to get connection from pool on attempt {attempt + 1}/{max_retries}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                return False
            
            # Determine market cap category
            market_cap_category = get_market_cap_category(coin)
            
            # Convert timestamps if present in the data
            current_year = datetime.now().year
            min_valid_year = current_year - 5  # Data older than 5 years is likely invalid
            max_valid_year = current_year + 5  # Data more than 5 years in the future is likely invalid
            
            if isinstance(data, dict) and "data" in data and isinstance(data["data"], list):
                for item in data["data"]:
                    # Process openDate to create proper timestamp
                    if "openDate" in item and isinstance(item["openDate"], (int, float)):
                        # Store the original timestamp if one exists
                        if "timestamp" in item:
                            item["original_timestamp"] = item["timestamp"]
                            
                        # Use our utility function to convert timestamp
                        dt = convert_timestamp(
                            item["openDate"], 
                            f"{endpoint} - {coin} - {exchange} - {timeframe}"
                        )
                        
                        # Set the corrected timestamp if conversion succeeded
                        if dt:
                            item["timestamp"] = dt.isoformat()
            
            # Standardize exchange name to lowercase for database storage
            exchange_standardized = exchange.lower() if exchange else None
            
            # Use the current timestamp instead of DEFAULT NOW()
            current_timestamp = datetime.utcnow()
            
            query = """
                INSERT INTO hyblock_data (endpoint, coin, exchange, timeframe, market_cap_category, data, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (endpoint, coin, exchange, timeframe, timestamp)
                DO UPDATE SET data = EXCLUDED.data
            """
            
            # Convert data to JSON string if it's not already
            data_json = json.dumps(data) if not isinstance(data, str) else data
            
            params = (
                endpoint,
                coin,
                exchange_standardized,
                timeframe,
                market_cap_category,
                data_json,
                current_timestamp
            )
            
            # Use execute_query with the connection from the pool
            result = execute_query(conn, query, params, fetch=False)
            
            if result:
                logger.debug(f"Successfully stored {endpoint} data for {coin} on {exchange} ({timeframe}) at {current_timestamp}")
                return True
            else:
                logger.warning(f"Failed to store {endpoint} data for {coin} on {exchange} ({timeframe})")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                return False
                
        except Exception as e:
            logger.error(f"Error storing data in hyblock_data table (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2
                continue
            return False
        finally:
            # Always return the connection to the pool if it exists
            if conn:
                return_db_connection(conn)
    
    return False

def process_orderbook_data(coin: str, exchange: str, data: Dict[str, Any]) -> bool:
    """Process and store orderbook data."""
    try:
        if not data or "data" not in data:
            return False
        
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to get connection from pool")
            return False
        
        try:
            data_points = data["data"]
            if not isinstance(data_points, list) or not data_points:
                return False
            
            # Get the latest data point
            latest = data_points[0]
            
            query = """
                INSERT INTO orderbook_data (
                    coin, exchange, bid_price, ask_price, bid_size, ask_size, bid_ask_ratio, spread
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (coin, exchange, timestamp)
                DO UPDATE SET 
                    bid_price = EXCLUDED.bid_price,
                    ask_price = EXCLUDED.ask_price,
                    bid_size = EXCLUDED.bid_size,
                    ask_size = EXCLUDED.ask_size,
                    bid_ask_ratio = EXCLUDED.bid_ask_ratio,
                    spread = EXCLUDED.spread
            """
            
            params = (
                coin,
                exchange,
                latest.get("bidPrice"),
                latest.get("askPrice"),
                latest.get("bidSize"),
                latest.get("askSize"),
                latest.get("bidAskRatio"),
                latest.get("spread")
            )
            
            result = execute_query(conn, query, params, fetch=False)
            return result
        finally:
            # Return the connection to the pool
            return_db_connection(conn)
    except Exception as e:
        logger.error(f"Error processing orderbook data: {e}")
        return False

def process_options_data(coin: str, exchange: str, data: Dict[str, Any]) -> bool:
    """Process and store options data."""
    try:
        if not data or "data" not in data:
            return False
        
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to get connection from pool")
            return False
        
        try:
            data_points = data["data"]
            if not isinstance(data_points, list) or not data_points:
                return False
            
            # Get the latest data point
            latest = data_points[0]
            
            query = """
                INSERT INTO options_data (
                    coin, exchange, bvol, dvol, term_structure
                )
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (coin, exchange, timestamp)
                DO UPDATE SET 
                    bvol = EXCLUDED.bvol,
                    dvol = EXCLUDED.dvol,
                    term_structure = EXCLUDED.term_structure
            """
            
            params = (
                coin,
                exchange,
                latest.get("bvol"),
                latest.get("dvol"),
                json.dumps(latest.get("termStructure", {}))
            )
            
            result = execute_query(conn, query, params, fetch=False)
            return result
        finally:
            # Return the connection to the pool
            return_db_connection(conn)
    except Exception as e:
        logger.error(f"Error processing options data: {e}")
        return False

def process_orderflow_data(coin: str, exchange: str, timeframe: str, data: Dict[str, Any]) -> bool:
    """Process and store orderflow data."""
    try:
        if not data or "data" not in data:
            return False
        
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to get connection from pool")
            return False
        
        try:
            data_points = data["data"]
            if not isinstance(data_points, list) or not data_points:
                return False
            
            # Get the latest data point
            latest = data_points[0]
            
            query = """
                INSERT INTO orderflow_data (
                    coin, exchange, timeframe, buy_volume, sell_volume, volume_delta, market_orders, limit_orders
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (coin, exchange, timeframe, timestamp)
                DO UPDATE SET 
                    buy_volume = EXCLUDED.buy_volume,
                    sell_volume = EXCLUDED.sell_volume,
                    volume_delta = EXCLUDED.volume_delta,
                    market_orders = EXCLUDED.market_orders,
                    limit_orders = EXCLUDED.limit_orders
            """
            
            params = (
                coin,
                exchange,
                timeframe,
                latest.get("buyVolume"),
                latest.get("sellVolume"),
                latest.get("volumeDelta"),
                latest.get("marketOrders"),
                latest.get("limitOrders")
            )
            
            result = execute_query(conn, query, params, fetch=False)
            return result
        finally:
            # Return the connection to the pool
            return_db_connection(conn)
    except Exception as e:
        logger.error(f"Error processing orderflow data: {e}")
        return False

def process_open_interest_data(coin: str, exchange: str, data: Dict[str, Any]) -> bool:
    """Process and store open interest data."""
    try:
        if not data or "data" not in data:
            return False
        
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to get connection from pool")
            return False
        
        try:
            data_points = data["data"]
            if not isinstance(data_points, list) or not data_points:
                return False
            
            # Get the latest data point
            latest = data_points[0]
            
            query = """
                INSERT INTO open_interest_data (
                    coin, exchange, open_interest, open_interest_delta, open_interest_usd
                )
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (coin, exchange, timestamp)
                DO UPDATE SET 
                    open_interest = EXCLUDED.open_interest,
                    open_interest_delta = EXCLUDED.open_interest_delta,
                    open_interest_usd = EXCLUDED.open_interest_usd
            """
            
            params = (
                coin,
                exchange,
                latest.get("openInterest"),
                latest.get("openInterestDelta"),
                latest.get("openInterestUsd")
            )
            
            result = execute_query(conn, query, params, fetch=False)
            return result
        finally:
            # Return the connection to the pool
            return_db_connection(conn)
    except Exception as e:
        logger.error(f"Error processing open interest data: {e}")
        return False

def process_liquidity_data(coin: str, exchange: str, data: Dict[str, Any]) -> bool:
    """Process and store liquidity data."""
    try:
        if not data or "data" not in data:
            return False
        
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to get connection from pool")
            return False
        
        try:
            data_points = data["data"]
            if not isinstance(data_points, list) or not data_points:
                return False
            
            # Get the latest data point
            latest = data_points[0]
            
            query = """
                INSERT INTO liquidity_data (
                    coin, exchange, liquidation_levels, average_leverage, liquidity_score
                )
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (coin, exchange, timestamp)
                DO UPDATE SET 
                    liquidation_levels = EXCLUDED.liquidation_levels,
                    average_leverage = EXCLUDED.average_leverage,
                    liquidity_score = EXCLUDED.liquidity_score
            """
            
            liquidation_levels = latest.get("liquidationLevels", {})
            
            params = (
                coin,
                exchange,
                json.dumps(liquidation_levels) if liquidation_levels else None,
                latest.get("averageLeverage"),
                latest.get("liquidityScore")
            )
            
            result = execute_query(conn, query, params, fetch=False)
            return result
        finally:
            # Return the connection to the pool
            return_db_connection(conn)
    except Exception as e:
        logger.error(f"Error processing liquidity data: {e}")
        return False

def process_funding_rate_data(coin: str, exchange: str, data: Dict[str, Any]) -> bool:
    """Process and store funding rate data."""
    try:
        if not data or "data" not in data:
            return False
        
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to get connection from pool")
            return False
        
        try:
            data_points = data["data"]
            if not isinstance(data_points, list) or not data_points:
                return False
            
            # Get the latest data point
            latest = data_points[0]
            
            query = """
                INSERT INTO funding_rate_data (
                    coin, exchange, funding_rate, next_funding_time, predicted_funding_rate
                )
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (coin, exchange, timestamp)
                DO UPDATE SET 
                    funding_rate = EXCLUDED.funding_rate,
                    next_funding_time = EXCLUDED.next_funding_time,
                    predicted_funding_rate = EXCLUDED.predicted_funding_rate
            """
            
            # Convert next funding time from Unix timestamp to datetime
            next_funding_time = None
            if "nextFundingTime" in latest and latest["nextFundingTime"]:
                try:
                    next_funding_time = datetime.fromtimestamp(latest["nextFundingTime"] / 1000)
                except (ValueError, TypeError):
                    pass
            
            params = (
                coin,
                exchange,
                latest.get("fundingRate"),
                next_funding_time,
                latest.get("predictedFundingRate")
            )
            
            result = execute_query(conn, query, params, fetch=False)
            
            # Also process for hyblock_funding_data table
            process_hyblock_funding_data(coin, exchange, data_points)
            
            return result
        finally:
            # Return the connection to the pool
            return_db_connection(conn)
    except Exception as e:
        logger.error(f"Error processing funding rate data: {e}")
        return False

def process_hyblock_funding_data(coin: str, exchange: str, data_points: List[Dict[str, Any]]) -> bool:
    """Process and store funding rate data in the hyblock_funding_data table."""
    try:
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to get connection from pool")
            return False
        
        try:
            success = True
            # Process each data point
            for point in data_points:
                if "openDate" not in point or "fundingRate" not in point:
                    continue
                
                # Convert timestamp
                try:
                    open_date = int(point["openDate"])
                    timestamp = datetime.fromtimestamp(open_date / 1000)
                except (ValueError, TypeError, OverflowError):
                    logger.warning(f"Invalid timestamp for funding_rate: {point.get('openDate')}")
                    continue
                
                # Convert next funding time
                next_funding_time = None
                if "nextFundingTime" in point and point["nextFundingTime"]:
                    try:
                        next_funding_time = datetime.fromtimestamp(point["nextFundingTime"] / 1000)
                    except (ValueError, TypeError, OverflowError):
                        pass
                
                query = """
                    INSERT INTO hyblock_funding_data (
                        coin, exchange, timestamp, funding_rate, next_funding_time, 
                        predicted_funding_rate, additional_data
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (coin, exchange, timestamp)
                    DO UPDATE SET 
                        funding_rate = EXCLUDED.funding_rate,
                        next_funding_time = EXCLUDED.next_funding_time,
                        predicted_funding_rate = EXCLUDED.predicted_funding_rate,
                        additional_data = EXCLUDED.additional_data
                """
                
                params = (
                    coin,
                    exchange,
                    timestamp,
                    point.get("fundingRate"),
                    next_funding_time,
                    point.get("predictedFundingRate"),
                    json.dumps(point)
                )
                
                result = execute_query(conn, query, params, fetch=False)
                if not result:
                    logger.warning(f"Failed to insert funding_rate data for {coin} at {timestamp}")
                    success = False
            
            return success
        finally:
            return_db_connection(conn)
    except Exception as e:
        logger.error(f"Error processing hyblock funding rate data: {e}")
        return False

def process_long_short_data(coin: str, exchange: str, data: Dict[str, Any]) -> bool:
    """Process and store long/short data."""
    try:
        if not data or "data" not in data:
            return False
        
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to get connection from pool")
            return False
        
        try:
            data_points = data["data"]
            if not isinstance(data_points, list) or not data_points:
                return False
            
            # Get the latest data point
            latest = data_points[0]
            
            query = """
                INSERT INTO long_short_data (
                    coin, exchange, long_positions, short_positions, net_long_short, 
                    net_long_short_delta, long_short_ratio
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (coin, exchange, timestamp)
                DO UPDATE SET 
                    long_positions = EXCLUDED.long_positions,
                    short_positions = EXCLUDED.short_positions,
                    net_long_short = EXCLUDED.net_long_short,
                    net_long_short_delta = EXCLUDED.net_long_short_delta,
                    long_short_ratio = EXCLUDED.long_short_ratio
            """
            
            params = (
                coin,
                exchange,
                latest.get("longPositions"),
                latest.get("shortPositions"),
                latest.get("netLongShort"),
                latest.get("netLongShortDelta"),
                latest.get("longShortRatio")
            )
            
            result = execute_query(conn, query, params, fetch=False)
            return result
        finally:
            # Return the connection to the pool
            return_db_connection(conn)
    except Exception as e:
        logger.error(f"Error processing long/short data: {e}")
        return False

def process_sentiment_data(coin: str, data: Dict[str, Any]) -> bool:
    """Process and store sentiment data."""
    try:
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to get connection from pool")
            return False
        
        try:
            # Extract data
            timestamp = datetime.now()
            fear_greed_value = None
            fear_greed_classification = None
            margin_lending_ratio = None
            user_bot_ratio = None
            bitmex_leaderboard_notional_profit = None
            bitmex_leaderboard_roe_profit = None
            trollbox_sentiment = None
            stablecoin_premium_p2p = None
            wbtc_mint_burn = None
            
            if "fearAndGreed" in data:
                fear_greed_data = data.get("fearAndGreed", {})
                fear_greed_value = fear_greed_data.get("value")
                fear_greed_classification = fear_greed_data.get("classification")
            
            if "marginLendingRatio" in data:
                margin_lending_ratio = data.get("marginLendingRatio", {}).get("value")
            
            if "userBotRatio" in data:
                user_bot_ratio = data.get("userBotRatio", {}).get("value")
            
            if "bitmexLeaderboardNotionalProfit" in data:
                bitmex_leaderboard_notional_profit = json.dumps(data.get("bitmexLeaderboardNotionalProfit", {}))
            
            if "bitmexLeaderboardROEProfit" in data:
                bitmex_leaderboard_roe_profit = json.dumps(data.get("bitmexLeaderboardROEProfit", {}))
            
            if "trollbox" in data:
                trollbox_sentiment = json.dumps(data.get("trollbox", {}))
            
            if "stablecoinPremiumP2P" in data:
                stablecoin_premium_p2p = data.get("stablecoinPremiumP2P", {}).get("value")
            
            if "wbtcMintBurn" in data:
                wbtc_mint_burn = json.dumps(data.get("wbtcMintBurn", {}))
            
            # Insert or update data
            query = """
                INSERT INTO sentiment_data (
                    coin, timestamp, fear_greed_value, fear_greed_classification,
                    margin_lending_ratio, user_bot_ratio, bitmex_leaderboard_notional_profit,
                    bitmex_leaderboard_roe_profit, trollbox_sentiment, stablecoin_premium_p2p,
                    wbtc_mint_burn
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (coin, timestamp)
                DO UPDATE SET
                    fear_greed_value = EXCLUDED.fear_greed_value,
                    fear_greed_classification = EXCLUDED.fear_greed_classification,
                    margin_lending_ratio = EXCLUDED.margin_lending_ratio,
                    user_bot_ratio = EXCLUDED.user_bot_ratio,
                    bitmex_leaderboard_notional_profit = EXCLUDED.bitmex_leaderboard_notional_profit,
                    bitmex_leaderboard_roe_profit = EXCLUDED.bitmex_leaderboard_roe_profit,
                    trollbox_sentiment = EXCLUDED.trollbox_sentiment,
                    stablecoin_premium_p2p = EXCLUDED.stablecoin_premium_p2p,
                    wbtc_mint_burn = EXCLUDED.wbtc_mint_burn
            """
            
            params = (
                coin, timestamp, fear_greed_value, fear_greed_classification,
                margin_lending_ratio, user_bot_ratio, bitmex_leaderboard_notional_profit,
                bitmex_leaderboard_roe_profit, trollbox_sentiment, stablecoin_premium_p2p,
                wbtc_mint_burn
            )
            
            result = execute_query(conn, query, params, fetch=False)
            return result
        finally:
            # Return the connection to the pool
            return_db_connection(conn)
    except Exception as e:
        logger.error(f"Error processing sentiment data: {e}")
        return False

def process_profile_data(coin: str, exchange: str, data: Dict[str, Any]) -> bool:
    """Process and store profile data."""
    try:
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to get connection from pool")
            return False
        
        try:
            # Extract data
            timestamp = datetime.now()
            open_interest_profile = None
            volume_profile = None
            
            if "openInterestProfile" in data:
                open_interest_profile = json.dumps(data.get("openInterestProfile", {}))
            
            if "volumeProfile" in data:
                volume_profile = json.dumps(data.get("volumeProfile", {}))
            
            # Insert or update data
            query = """
                INSERT INTO profile_data (
                    coin, exchange, timestamp, open_interest_profile, volume_profile
                )
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (coin, exchange, timestamp)
                DO UPDATE SET
                    open_interest_profile = EXCLUDED.open_interest_profile,
                    volume_profile = EXCLUDED.volume_profile
            """
            
            params = (
                coin, exchange, timestamp, open_interest_profile, volume_profile
            )
            
            result = execute_query(conn, query, params, fetch=False)
            return result
        finally:
            # Return the connection to the pool
            return_db_connection(conn)
    except Exception as e:
        logger.error(f"Error processing profile data: {e}")
        return False

def get_market_cap_category(coin: str) -> Optional[str]:
    """Get the market cap category for a coin from the database."""
    try:
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to get connection from pool")
            return None
        
        try:
            query = """
                SELECT category
                FROM market_cap_categories
                WHERE coin = %s
            """
            
            results = execute_query(conn, query, (coin,), fetch=True)
            
            if results and results[0]:
                return results[0][0]
            return None
        finally:
            # Return the connection to the pool
            return_db_connection(conn)
    except Exception as e:
        logger.error(f"Error getting market cap category: {e}")
        return None

def update_market_cap_categories() -> bool:
    """Update market cap categories for all coins."""
    try:
        # Define market cap categories
        large_cap = ["BTC", "ETH"]
        mid_cap = ["SOL", "XRP", "BNB", "ADA", "DOGE", "AVAX", "DOT", "LINK", "MATIC", "UNI"]
        # All other coins are considered small cap
        
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to get connection from pool")
            return False
        
        try:
            # Get all coins from the catalog
            catalog = load_catalog()
            all_coins = set()
            
            for exchange, coins in catalog.items():
                all_coins.update(coins)
            
            # Update categories
            for coin in all_coins:
                category = "large_cap" if coin in large_cap else "mid_cap" if coin in mid_cap else "small_cap"
                
                query = """
                    INSERT INTO market_cap_categories (coin, category)
                    VALUES (%s, %s)
                    ON CONFLICT (coin)
                    DO UPDATE SET 
                        category = EXCLUDED.category,
                        last_updated = NOW()
                """
                
                execute_query(conn, query, (coin, category), fetch=False)
            
            return True
        finally:
            # Return the connection to the pool
            return_db_connection(conn)
    except Exception as e:
        logger.error(f"Error updating market cap categories: {e}")
        return False

def collect_data_for_coin_exchange(coin: str, exchange: str) -> Tuple[int, int]:
    """Collect data for a specific coin-exchange pair across all metric categories."""
    total_endpoints = 0
    successful_endpoints = 0
    
    logger.info(f"Collecting data for {coin} on {exchange}")
    
    # Initialize collection stats for this coin-exchange pair
    coin_exchange_key = f"{coin}_{exchange}"
    with STATS_LOCK:
        if coin_exchange_key not in collection_stats:
            collection_stats[coin_exchange_key] = {
                "total_endpoints": 0,
                "successful_endpoints": 0,
                "started_at": datetime.now(),
                "completed_at": None
            }
            
    # Collect orderbook data for different timeframes
    for endpoint in METRICS["orderbook"]:
        for timeframe in TIMEFRAMES:
            total_endpoints += 1
            try:
                data = fetch_data(endpoint, coin, exchange, timeframe)
                if data:
                    # Store raw data
                    success = store_data_in_hyblock_table(endpoint, coin, exchange, timeframe, data)
                    if success:
                        successful_endpoints += 1
                        
                    # Process specific endpoints
                    if endpoint == "asksIncreaseDecrease":
                        process_asks_increase_decrease(coin, exchange, timeframe, data)
                    elif endpoint == "bidsIncreaseDecrease":
                        process_bids_increase_decrease(coin, exchange, timeframe, data)
                    elif endpoint == "bidAsk":
                        process_orderbook_data(coin, exchange, data)
                time.sleep(RATE_LIMIT_DELAY)
            except Exception as e:
                logger.error(f"Error collecting {endpoint} data for {coin} on {exchange} ({timeframe}): {e}")
    
    # Collect options data for different timeframes
    for endpoint in METRICS["options"]:
        for timeframe in TIMEFRAMES:
            total_endpoints += 1
            try:
                data = fetch_data(endpoint, coin, exchange, timeframe)
                if data:
                    if store_data_in_hyblock_table(endpoint, coin, exchange, timeframe, data):
                        successful_endpoints += 1
                    if endpoint == "bvol" or endpoint == "dvol":
                        process_options_data(coin, exchange, data)
                time.sleep(RATE_LIMIT_DELAY)
            except Exception as e:
                logger.error(f"Error collecting {endpoint} data for {coin} on {exchange} ({timeframe}): {e}")
    
    # Collect orderflow data for different timeframes
    for endpoint in METRICS["orderflow"]:
        for timeframe in TIMEFRAMES:
            total_endpoints += 1
            try:
                data = fetch_data(endpoint, coin, exchange, timeframe)
                if data:
                    if store_data_in_hyblock_table(endpoint, coin, exchange, timeframe, data):
                        successful_endpoints += 1
                    if endpoint in ["buyVolume", "sellVolume", "volumeDelta"]:
                        process_orderflow_data(coin, exchange, timeframe, data)
                time.sleep(RATE_LIMIT_DELAY)
            except Exception as e:
                logger.error(f"Error collecting {endpoint} data for {coin} on {exchange} ({timeframe}): {e}")
    
    # Collect open interest data
    for endpoint in METRICS["open_interest"]:
        for timeframe in TIMEFRAMES if endpoint != "openInterestProfile" else ["1d"]:
            total_endpoints += 1
            try:
                data = fetch_data(endpoint, coin, exchange, timeframe)
                if data:
                    if store_data_in_hyblock_table(endpoint, coin, exchange, timeframe, data):
                        successful_endpoints += 1
                    if endpoint == "openInterest":
                        process_open_interest_data(coin, exchange, data)
                time.sleep(RATE_LIMIT_DELAY)
            except Exception as e:
                logger.error(f"Error collecting {endpoint} data for {coin} on {exchange} ({timeframe}): {e}")
    
    # Collect liquidity data
    for endpoint in METRICS["liquidity"]:
        for timeframe in TIMEFRAMES:
            total_endpoints += 1
            try:
                data = fetch_data(endpoint, coin, exchange, timeframe)
                if data:
                    if store_data_in_hyblock_table(endpoint, coin, exchange, timeframe, data):
                        successful_endpoints += 1
                    if endpoint == "liquidationLevels":
                        process_liquidity_data(coin, exchange, data)
                time.sleep(RATE_LIMIT_DELAY)
            except Exception as e:
                logger.error(f"Error collecting {endpoint} data for {coin} on {exchange} ({timeframe}): {e}")
    
    # Collect funding rate data
    for endpoint in METRICS["funding_rate"]:
        total_endpoints += 1
        try:
            # Funding rate doesn't need timeframe
            data = fetch_data(endpoint, coin, exchange)
            if data:
                if store_data_in_hyblock_table(endpoint, coin, exchange, None, data):
                    successful_endpoints += 1
                process_funding_rate_data(coin, exchange, data)
            time.sleep(RATE_LIMIT_DELAY)
        except Exception as e:
            logger.error(f"Error collecting {endpoint} data for {coin} on {exchange}: {e}")
    
    # Update collection stats for this coin-exchange pair
    with STATS_LOCK:
        if coin_exchange_key in collection_stats:
            collection_stats[coin_exchange_key]["total_endpoints"] += total_endpoints
            collection_stats[coin_exchange_key]["successful_endpoints"] += successful_endpoints
            collection_stats[coin_exchange_key]["completed_at"] = datetime.now()
    
    return total_endpoints, successful_endpoints

def collect_sentiment_data(coin: str) -> None:
    """Collect sentiment data for a specific coin."""
    logger.info(f"Collecting sentiment data for {coin}")
    
    for endpoint in METRICS["sentiment"]:
        data = fetch_data(endpoint, coin)
        if data:
            store_data_in_hyblock_table(endpoint, coin, None, None, data)
            process_sentiment_data(coin, data)
        time.sleep(RATE_LIMIT_DELAY)

def log_collection_stats() -> None:
    """Log detailed statistics after collection."""
    try:
        # Print overall statistics
        total_pairs = len(collection_stats)
        total_endpoints = sum(stats["total_endpoints"] for stats in collection_stats.values())
        successful_endpoints = sum(stats["successful_endpoints"] for stats in collection_stats.values())
        success_rate = (successful_endpoints / total_endpoints * 100) if total_endpoints > 0 else 0
        
        logger.info(f"Collection summary: {successful_endpoints}/{total_endpoints} endpoints successful ({success_rate:.2f}%) across {total_pairs} coin-exchange pairs")
        
        # Print per-table statistics
        conn = get_db_connection()
        if conn:
            try:
                tables = [
                    "hyblock_data",
                    "hyblock_asks_increase_decrease_data",
                    "hyblock_bids_increase_decrease_data",
                    "hyblock_market_data",
                    "hyblock_open_interest_data",
                    "hyblock_liquidity_data",
                    "hyblock_funding_data",
                    "funding_rate_data",
                    "orderbook_data",
                    "options_data",
                    "orderflow_data",
                    "open_interest_data",
                    "liquidity_data",
                    "long_short_data",
                    "market_cap_categories",
                    "api_usage"
                ]
                
                for table in tables:
                    try:
                        query = f"SELECT COUNT(*) FROM {table}"
                        result = execute_query(conn, query)
                        if result and result[0] and hasattr(result[0], "__getitem__"):
                            count = result[0][0]
                            logger.info(f"Table {table}: {count} records")
                    except Exception as e:
                        logger.warning(f"Failed to get count for table {table}: {e}")
            finally:
                return_db_connection(conn)
        else:
            logger.warning("Could not get database connection for statistics reporting")
        
        # Print performance information
        try:
            # Find the fastest and slowest operations
            with STATS_LOCK:
                if collection_stats:
                    for pair, stats in collection_stats.items():
                        if "started_at" in stats and "completed_at" in stats and stats["started_at"] and stats["completed_at"]:
                            duration = (stats["completed_at"] - stats["started_at"]).total_seconds()
                            logger.info(f"Collection for {pair} took {duration:.2f} seconds")
        except Exception as e:
            logger.error(f"Error generating performance statistics: {e}")
            
    except Exception as e:
        logger.error(f"Error logging collection statistics: {e}")
        import traceback
        logger.error(traceback.format_exc())

# Define endpoint priorities (higher number = higher priority)
ENDPOINT_PRIORITIES = {
    # High priority endpoints (critical for analysis)
    "bidAsk": 10,
    "bidAskRatio": 10,
    "bidAskDelta": 10,
    "openInterest": 10,
    "fundingRate": 10,
    "liquidation": 10,
    
    # Medium priority endpoints
    "buyVolume": 7,
    "sellVolume": 7,
    "volumeDelta": 7,
    "klines": 7,
    "marketOrderCount": 7,
    "limitOrderCount": 7,
    "pdLevels": 7,
    "bvol": 7,
    
    # Lower priority endpoints
    "asksIncreaseDecrease": 5,
    "bidsIncreaseDecrease": 5,
    "combinedBook": 5,
    "bidsAskSpread": 5,
    "bidAskRatioDiff": 5,
    "botTracker": 5,
    "marketOrderAverageSize": 5,
    "limitOrderAverageSize": 5,
    "pwLevels": 5,
    "pmLevels": 5,
    
    # Lowest priority endpoints
    "anchoredCVD": 3,
    "anchoredOIDelta": 3,
    "anchoredLLC": 3,
    "anchoredLLS": 3,
    "anchoredCLLCD": 3,
    "anchoredCLLSD": 3,
    "anchoredBinanceGlobalAccounts": 3,
    "anchoredBinanceTopTraderAccounts": 3,
    "anchoredBinanceTopTraderPositions": 3,
    "anchoredBinanceWhaleRetailDelta": 3,
    "anchoredCLS": 3,
    "anchoredCLSD": 3,
    
    # Default priority for all other endpoints
    "default": 1
}

# Define coin priorities (higher number = higher priority)
COIN_PRIORITIES = {
    "BTC": 10,
    "ETH": 9,
    "SOL": 8,
    "XRP": 7,
    "BNB": 7,
    "AVAX": 6,
    "LINK": 6,
    "DOT": 5,
    "ADA": 5,
    "DOGE": 5,
    "default": 3
}

# Define exchange priorities (higher number = higher priority)
EXCHANGE_PRIORITIES = {
    "binance": 10,
    "bybit": 8,
    "okx": 7,
    "deribit": 6,
    "coinbase": 5,
    "default": 3
}

def get_endpoint_priority(endpoint: str) -> int:
    """Get the priority of an endpoint."""
    return ENDPOINT_PRIORITIES.get(endpoint, ENDPOINT_PRIORITIES["default"])

def get_coin_priority(coin: str) -> int:
    """Get the priority of a coin."""
    return COIN_PRIORITIES.get(coin, COIN_PRIORITIES["default"])

def get_exchange_priority(exchange: str) -> int:
    """Get the priority of an exchange."""
    return EXCHANGE_PRIORITIES.get(exchange, EXCHANGE_PRIORITIES["default"])

def run_data_collection() -> None:
    """Run the data collection process."""
    logger.info("Starting data collection process")
    
    # Initialize database connection pool
    init_db_pool()
    
    # Load catalog of available coins for each exchange
    catalog = load_catalog()
    
    # Update market cap categories
    update_market_cap_categories()
    
    # Get API usage information
    api_usage = get_api_usage()
    if api_usage:
        logger.info(f"API usage: {api_usage}")
    
    # Create a list of all collection tasks
    collection_tasks = []
    
    # Add tasks for each endpoint, coin, exchange, and timeframe combination
    for category, endpoints in METRICS.items():
        for endpoint in endpoints:
            # Skip catalog and api_usage endpoints
            if category in ["catalog", "api_usage"]:
                continue
            
            # Get endpoint priority
            endpoint_priority = get_endpoint_priority(endpoint)
            
            # For each coin in the catalog
            for exchange, coins in catalog.items():
                # Get exchange priority
                exchange_priority = get_exchange_priority(exchange)
                
                # Skip if exchange is not in priority exchanges
                if exchange.lower() not in [ex.lower() for ex in PRIORITY_EXCHANGES]:
                    continue
                
                for coin in coins:
                    # Get coin priority
                    coin_priority = get_coin_priority(coin)
                    
                    # Skip if not compatible
                    if not is_compatible(endpoint, coin, exchange):
                        continue
                    
                    # For endpoints that require timeframes
                    if category not in ["sentiment"]:
                        for timeframe in TIMEFRAMES:
                            # Calculate overall priority
                            priority = endpoint_priority + coin_priority + exchange_priority
                            
                            # Add task to the list
                            collection_tasks.append({
                                "endpoint": endpoint,
                                "coin": coin,
                                "exchange": exchange,
                                "timeframe": timeframe,
                                "priority": priority
                            })
                    else:
                        # For endpoints that don't require timeframes
                        # Calculate overall priority
                        priority = endpoint_priority + coin_priority + exchange_priority
                        
                        # Add task to the list
                        collection_tasks.append({
                            "endpoint": endpoint,
                            "coin": coin,
                            "exchange": exchange,
                            "timeframe": None,
                            "priority": priority
                        })
    
    # Sort tasks by priority (highest first)
    collection_tasks.sort(key=lambda x: x["priority"], reverse=True)
    
    # Calculate total number of tasks
    total_tasks = len(collection_tasks)
    logger.info(f"Total collection tasks: {total_tasks}")
    
    # Set up thread pool for parallel collection
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit tasks to the executor
        futures = []
        for task in collection_tasks:
            endpoint = task["endpoint"]
            coin = task["coin"]
            exchange = task["exchange"]
            timeframe = task["timeframe"]
            
            # Submit the task
            if timeframe:
                logger.debug(f"Submitting task: {endpoint} - {coin} - {exchange} - {timeframe}")
                future = executor.submit(collect_data_for_endpoint, endpoint, coin, exchange, timeframe)
            else:
                logger.debug(f"Submitting task: {endpoint} - {coin} - {exchange}")
                future = executor.submit(collect_data_for_endpoint, endpoint, coin, exchange)
            
            futures.append(future)
            
            # Add a small delay to avoid overwhelming the API
            time.sleep(0.01)
        
        # Process results as they complete
        completed = 0
        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
                completed += 1
                if completed % 100 == 0 or completed == total_tasks:
                    logger.info(f"Completed {completed}/{total_tasks} tasks ({completed/total_tasks*100:.1f}%)")
            except Exception as e:
                logger.error(f"Error in collection task: {e}")
    
    # Log collection statistics
    log_collection_stats()
    
    logger.info("Data collection process completed")

def collect_data_for_endpoint(endpoint: str, coin: str, exchange: str, timeframe: str = None) -> bool:
    """Collect data for a specific endpoint, coin, exchange, and timeframe."""
    try:
        # Fetch data from the API
        if timeframe:
            data = fetch_data(endpoint, coin, exchange, timeframe)
        else:
            data = fetch_data(endpoint, coin, exchange)
        
        if not data:
            return False
        
        # Store data in the database
        if timeframe:
            return store_data_in_hyblock_table(endpoint, coin, exchange, timeframe, data)
        else:
            return store_data_in_hyblock_table(endpoint, coin, exchange, "all", data)
    except Exception as e:
        logger.error(f"Error collecting data for {endpoint} - {coin} - {exchange} - {timeframe}: {e}")
        return False

def schedule_data_collection() -> None:
    """Schedule regular data collection."""
    # Run immediately on startup
    run_data_collection()
    
    # Schedule to run every 15 minutes
    schedule.every(15).minutes.do(run_data_collection)
    
    # Keep the script running
    while True:
        schedule.run_pending()
        time.sleep(1)

# Add a utility function to standardize timestamp conversion
def convert_timestamp(timestamp_value, source_description=None):
    """
    Convert a timestamp value to a datetime object with standardized handling.
    
    Args:
        timestamp_value (int/float): The timestamp value to convert, either in seconds or milliseconds
        source_description (str, optional): Description of the source for better error messages
        
    Returns:
        datetime or None: The converted datetime object, or None if conversion failed
    """
    if not timestamp_value or not isinstance(timestamp_value, (int, float)):
        return None
    
    try:
        # Check if timestamp is in seconds (10 digits) or milliseconds (13 digits)
        timestamp_ms = timestamp_value
        if len(str(int(timestamp_ms))) <= 10:
            # Convert seconds to milliseconds
            timestamp_ms = timestamp_ms * 1000
        
        # Convert to datetime
        dt = datetime.fromtimestamp(timestamp_ms / 1000)
        
        # Validate the timestamp is in a reasonable range
        current_year = datetime.now().year
        min_valid_year = current_year - 5  # Data older than 5 years is likely invalid
        max_valid_year = current_year + 5  # Data more than 5 years in the future is likely invalid
        
        if dt.year < min_valid_year or dt.year > max_valid_year:
            source_info = f" for {source_description}" if source_description else ""
            logger.warning(
                f"Suspicious timestamp detected: {dt} from value={timestamp_value}{source_info}. "
                f"Using current time instead."
            )
            # Use current time for suspicious timestamps
            return datetime.utcnow()
        
        return dt
    except (ValueError, OverflowError, OSError) as e:
        source_info = f" for {source_description}" if source_description else ""
        logger.warning(f"Error converting timestamp {timestamp_value}{source_info}: {e}")
        return None

def process_asks_increase_decrease(coin: str, exchange: str, timeframe: str, data: Dict[str, Any]) -> bool:
    """Process and store asks increase/decrease data."""
    try:
        if not data or "data" not in data:
            return False
        
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to get connection from pool")
            return False
        
        try:
            data_points = data["data"]
            if not isinstance(data_points, list) or not data_points:
                return False
            
            # Process each data point
            for point in data_points:
                if "openDate" not in point or "asks_increase_decrease" not in point:
                    continue
                
                # Convert timestamp using utility function
                open_date = point["openDate"]
                timestamp = convert_timestamp(
                    open_date, 
                    f"asks_increase_decrease - {coin} - {exchange} - {timeframe}"
                )
                
                if timestamp is None:
                    logger.warning(f"Skipping record with invalid timestamp: {open_date}")
                    continue
                
                query = """
                    INSERT INTO hyblock_asks_increase_decrease_data (
                        coin, timeframe, open_date, timestamp, asks_increase_decrease, additional_data
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (coin, timeframe, open_date) DO UPDATE SET
                        asks_increase_decrease = EXCLUDED.asks_increase_decrease,
                        additional_data = EXCLUDED.additional_data
                """
                
                params = (
                    coin,
                    timeframe,
                    open_date,
                    timestamp,
                    point.get("asks_increase_decrease"),
                    json.dumps(point)
                )
                
                result = execute_query(conn, query, params, fetch=False)
                if not result:
                    logger.warning(f"Failed to insert asks_increase_decrease data for {coin} at {timestamp}")
            
            return True
        finally:
            return_db_connection(conn)
    except Exception as e:
        logger.error(f"Error processing asks increase/decrease data: {e}")
        return False

def process_bids_increase_decrease(coin: str, exchange: str, timeframe: str, data: Dict[str, Any]) -> bool:
    """Process and store bids increase/decrease data."""
    try:
        if not data or "data" not in data:
            return False
        
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to get connection from pool")
            return False
        
        try:
            data_points = data["data"]
            if not isinstance(data_points, list) or not data_points:
                return False
            
            # Process each data point
            for point in data_points:
                if "openDate" not in point or "bids_increase_decrease" not in point:
                    continue
                
                # Convert timestamp using utility function
                open_date = point["openDate"]
                timestamp = convert_timestamp(
                    open_date, 
                    f"bids_increase_decrease - {coin} - {exchange} - {timeframe}"
                )
                
                if timestamp is None:
                    logger.warning(f"Skipping record with invalid timestamp: {open_date}")
                    continue
                
                query = """
                    INSERT INTO hyblock_bids_increase_decrease_data (
                        coin, timeframe, open_date, timestamp, bids_increase_decrease, additional_data
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (coin, timeframe, open_date) DO UPDATE SET
                        bids_increase_decrease = EXCLUDED.bids_increase_decrease,
                        additional_data = EXCLUDED.additional_data
                """
                
                params = (
                    coin,
                    timeframe,
                    open_date,
                    timestamp,
                    point.get("bids_increase_decrease"),
                    json.dumps(point)
                )
                
                result = execute_query(conn, query, params, fetch=False)
                if not result:
                    logger.warning(f"Failed to insert bids_increase_decrease data for {coin} at {timestamp}")
            
            return True
        finally:
            return_db_connection(conn)
    except Exception as e:
        logger.error(f"Error processing bids increase/decrease data: {e}")
        return False

def test_api_connection():
    """Test connection to the Hyblock API."""
    logger.info("Testing API connection...")
    
    # First test if we can get an access token
    access_token = get_access_token()
    if not access_token:
        logger.error("Failed to get access token. Check your CLIENT_ID and CLIENT_SECRET environment variables.")
        return False
    
    # Now test if we can access an endpoint
    test_endpoint = "fundingRate"
    test_coin = "BTC"
    test_exchange = "BINANCE"
    test_timeframe = "1h"  # Adding timeframe parameter
    
    try:
        url = f"{API_BASE_URL}/{test_endpoint}"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {access_token}",
            "x-api-key": API_KEY
        }
        
        logger.info(f"Testing API connection to {url}")
        
        # Add timeframe parameter to the query
        params = {
            "coin": test_coin,
            "exchange": test_exchange,
            "timeframe": test_timeframe,
            "sort": "asc",
            "limit": 10  # Changed from 1 to 10
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        if response.status_code == 200:
            logger.info("API connection successful")
            return True
        else:
            logger.error(f"API connection failed with status code {response.status_code}: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error testing API connection: {e}")
        return False

def get_api_usage() -> Dict[str, Any]:
    """Get the current API usage and remaining hits."""
    try:
        # Get the access token
        access_token = get_access_token()
        if not access_token:
            logger.error("No access token available, cannot get API usage")
            return {"remainingHits": 1000, "resetTime": int(time.time() * 1000)}
            
        url = f"{API_BASE_URL}/remainingHitBalance"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {access_token}",
            "x-api-key": API_KEY
        }
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            
            # Store API usage in database
            conn = get_db_connection()
            if conn:
                try:
                    query = """
                        INSERT INTO api_usage (endpoint, remaining_hits, reset_time)
                        VALUES (%s, %s, %s)
                    """
                    
                    reset_time = datetime.fromtimestamp(data.get("resetTime", 0) / 1000)
                    params = ("remainingHitBalance", data.get("remainingHits", 0), reset_time)
                    
                    execute_query(conn, query, params, fetch=False)
                    
                finally:
                    return_db_connection(conn)
            
            return data
        else:
            logger.warning(f"Failed to get API usage: {response.status_code} - {response.text}")
            # Return a default value with high remaining hits to avoid early exit
            return {"remainingHits": 1000, "resetTime": int(time.time() * 1000)}
    except Exception as e:
        logger.error(f"Error getting API usage: {e}")
        # Return a default value with high remaining hits to avoid early exit
        return {"remainingHits": 1000, "resetTime": int(time.time() * 1000)}

if __name__ == "__main__":
    if not API_KEY:
        # Check if there's a .env file with the API key
        try:
            from dotenv import load_dotenv
            load_dotenv()
            API_KEY = os.environ.get("HYBLOCK_API_KEY", "")
            if API_KEY:
                logger.info("Loaded API key from environment")
            else:
                logger.error("No API key found. Make sure to set HYBLOCK_API_KEY environment variable")
                sys.exit(1)
        except ImportError:
            logger.error("python-dotenv not installed and no API key found in environment. Make sure to set HYBLOCK_API_KEY environment variable")
            sys.exit(1)
    
    # Test database connection before starting
    try:
        logger.info("Testing database connection...")
        conn = connect_to_database()
        if conn:
            logger.info("Database connection successful")
            conn.close()
            
            # Test API connection
            if test_api_connection():
                # Initialize connection pool
                init_db_pool()
                # Start data collection
                schedule_data_collection()
            else:
                logger.error("API connection test failed. Check your API key and network connection.")
                sys.exit(1)
        else:
            logger.error("Failed to connect to database. Check database configuration.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        sys.exit(1) 