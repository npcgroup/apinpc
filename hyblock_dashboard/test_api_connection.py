import sys
import os
import json
import asyncio
from datetime import datetime

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from collector.hyblock_api import HyblockAPI
from utils.database import get_logger

# Set up logger
logger = get_logger("test_api_connection")

async def test_api_connection():
    """Test the connection to the Hyblock API"""
    logger.info("Testing Hyblock API connection...")
    
    # Initialize API client
    api = await HyblockAPI().initialize()
    
    try:
        # Test with a simple endpoint that requires minimal parameters
        # Using the catalog endpoint which should list available coins and exchanges
        result = await api.fetch_endpoint("catalog", {})
        
        if result:
            logger.info("Successfully connected to Hyblock API")
            logger.info(f"Received data from catalog endpoint")
            
            # Print a sample of the data
            data = result.get("data", {})
            if data:
                logger.info("Sample of available data:")
                
                # Check if there's a 'data' field in the response
                if isinstance(data, dict) and 'data' in data:
                    sample_data = data['data']
                    if isinstance(sample_data, list) and len(sample_data) > 0:
                        logger.info(f"Found {len(sample_data)} items")
                        
                        # Print the first item as a sample
                        if len(sample_data) > 0:
                            logger.info(f"Sample item: {json.dumps(sample_data[0], indent=2)}")
                else:
                    logger.info(f"Data structure: {json.dumps(data, indent=2)[:500]}...")
            
            return True
        else:
            logger.error("Failed to connect to Hyblock API")
            logger.error("Please check your API key in the .env file")
            return False
    
    except Exception as e:
        logger.error(f"Error testing API connection: {e}")
        return False
    
    finally:
        await api.close()

async def main():
    """Main function"""
    success = await test_api_connection()
    
    if success:
        print("Hyblock API connection test passed!")
        return 0
    else:
        print("Hyblock API connection test failed!")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 