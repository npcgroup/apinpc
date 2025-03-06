import asyncio
import sys
import json
import os
import logging

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from collector.hyblock_api import HyblockAPI
from utils.database import get_logger

# Set up logger
logger = get_logger("test_auth")

async def test_auth():
    """Test authentication with the Hyblock API"""
    logger.info("Testing Hyblock API authentication...")
    
    # Initialize API client
    api = await HyblockAPI().initialize()
    
    try:
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
            logger.info(f"Successfully authenticated with asksIncreaseDecrease endpoint")
            logger.info(f"Data sample: {json.dumps(result['data'])[:200]}...")
            return True
        else:
            logger.error("Failed to authenticate with asksIncreaseDecrease endpoint")
            
            # Try with a different endpoint
            logger.info("Testing market/kline endpoint...")
            result = await api.fetch_endpoint('market/kline', {
                'coin': 'SUI',
                'exchange': 'BINANCE',
                'timeframe': '1h'
            })
            
            if result:
                logger.info(f"Successfully authenticated with market/kline endpoint")
                logger.info(f"Data sample: {json.dumps(result['data'])[:200]}...")
                return True
            else:
                logger.error("Failed to authenticate with market/kline endpoint")
                return False
    
    except Exception as e:
        logger.error(f"Error testing authentication: {e}")
        return False
    
    finally:
        await api.close()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    success = loop.run_until_complete(test_auth())
    
    if success:
        print("Authentication test completed successfully")
    else:
        print("Authentication test failed")
        sys.exit(1) 