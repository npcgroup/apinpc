import asyncio
import sys
import json
import os

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from collector.hyblock_api import HyblockAPI
from utils.database import get_logger

# Set up logger
logger = get_logger("test_api")

async def test_api():
    """Test the Hyblock API client"""
    logger.info("Testing Hyblock API client...")
    
    # Initialize API client
    api = await HyblockAPI().initialize()
    
    try:
        # Test market/kline endpoint
        logger.info("Testing market/kline endpoint...")
        result = await api.fetch_endpoint('market/kline', {
            'coin': 'SUI',
            'exchange': 'BINANCE',
            'timeframe': '1h'
        })
        
        if result:
            logger.info(f"Successfully fetched data for {result['params']['coin']} on {result['params']['exchange']}")
            logger.info(f"Data sample: {json.dumps(result['data'])[:200]}...")
        else:
            logger.error("Failed to fetch data from market/kline endpoint")
        
        # Test asksIncreaseDecrease endpoint
        logger.info("Testing asksIncreaseDecrease endpoint...")
        result = await api.fetch_endpoint('asksIncreaseDecrease', {
            'coin': 'BTC',
            'timeframe': '1m',
            'marketTypes': 'All',
            'sort': 'asc',
            'limit': 50
        })
        
        if result:
            logger.info(f"Successfully fetched asks increase/decrease data for {result['params']['coin']}")
            logger.info(f"Data sample: {json.dumps(result['data'])[:200]}...")
            return True
        else:
            logger.error("Failed to fetch data from asksIncreaseDecrease endpoint")
            return False
    
    except Exception as e:
        logger.error(f"Error testing API: {e}")
        return False
    
    finally:
        await api.close()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    success = loop.run_until_complete(test_api())
    
    if success:
        print("API test completed successfully")
    else:
        print("API test failed")
        sys.exit(1) 