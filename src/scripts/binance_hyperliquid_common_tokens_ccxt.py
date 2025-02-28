#!/usr/bin/env python3
import ccxt
import asyncio
import logging
import time
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def get_common_tokens():
    """
    Fetch and compare available futures markets on Binance and HyperLiquid 
    to find common tokens.
    """
    try:
        # Initialize exchange clients
        logger.info("Initializing Binance client...")
        binance = ccxt.binance({
            'options': {'defaultType': 'future'},
            'enableRateLimit': True
        })
        
        logger.info("Initializing HyperLiquid client...")
        hyperliquid = ccxt.hyperliquid({
            'enableRateLimit': True
        })
        
        # Fetch markets
        logger.info("Fetching Binance futures markets...")
        binance_markets = binance.load_markets()
        
        logger.info("Fetching HyperLiquid markets...")
        hyperliquid_markets = hyperliquid.load_markets()
        
        # Extract base symbols from market keys
        logger.info("Processing Binance symbols...")
        binance_symbols = set()
        for market_key in binance_markets.keys():
            # Typical format: 'BTC/USDT:USDT'
            if ':USDT' in market_key:
                parts = market_key.split('/')
                if len(parts) > 0:
                    symbol = parts[0]
                    binance_symbols.add(symbol)
        
        logger.info("Processing HyperLiquid symbols...")
        hyperliquid_symbols = set()
        for market_key in hyperliquid_markets.keys():
            # Check for various formats to ensure we catch all symbols
            if '/USDC:USDC' in market_key:
                parts = market_key.split('/')
                if len(parts) > 0:
                    symbol = parts[0]
                    hyperliquid_symbols.add(symbol)
        
        # Find common symbols
        common_symbols = binance_symbols.intersection(hyperliquid_symbols)
        logger.info(f"Found {len(common_symbols)} common symbols")
        
        # Convert to sorted list for better readability
        common_symbols_list = sorted(list(common_symbols))
        
        # Print the results in different formats
        logger.info("Common symbols as Python list:")
        python_list_format = "['" + "', '".join(common_symbols_list) + "']"
        print(python_list_format)
        
        logger.info("Common symbols as JSON:")
        json_format = json.dumps(common_symbols_list)
        print(json_format)
        
        # Save to file
        with open('common_tokens.txt', 'w') as f:
            f.write("Python list format:\n")
            f.write(python_list_format + "\n\n")
            f.write("JSON format:\n")
            f.write(json_format)
        
        logger.info("Results saved to common_tokens.txt")
        
        # Print some additional information for validation
        logger.info(f"Total Binance futures symbols: {len(binance_symbols)}")
        logger.info(f"Total HyperLiquid symbols: {len(hyperliquid_symbols)}")
        
        # Print a few examples of symbols from each exchange
        logger.info(f"Sample Binance symbols: {list(binance_symbols)[:10]}")
        logger.info(f"Sample HyperLiquid symbols: {list(hyperliquid_symbols)[:10]}")
        
        # Return the common symbols for potential further use
        return common_symbols_list
        
    except Exception as e:
        logger.error(f"Error finding common tokens: {e}")
        return []

# Alternative function to try direct API calls if needed
async def check_token_support_direct():
    """
    Alternative approach using direct API calls to check token support
    """
    try:
        logger.info("Initializing exchange clients for direct API testing...")
        binance = ccxt.binance({
            'options': {'defaultType': 'future'},
            'enableRateLimit': True
        })
        
        hyperliquid = ccxt.hyperliquid({
            'enableRateLimit': True
        })
        
        # Test tokens to check
        test_tokens = [
            'BTC', 'ETH', 'SOL', 'AVAX', 'MATIC', 'DOGE', 'LINK', 
            'FTM', 'XRP', 'APT', 'AAVE', 'UNI', 'TRX', 'DOT', 
            'NEAR', 'FIL', 'IMX', 'GALA', 'OP', 'ARB', 'SUI', 'LTC'
        ]
        
        supported_tokens = []
        
        for token in test_tokens:
            binance_supported = False
            hyperliquid_supported = False
            
            # Check Binance
            try:
                binance_symbol = f"{token}/USDT:USDT"
                rates = binance.fetchFundingRateHistory(
                    binance_symbol,
                    int(time.time() * 1000) - 86400000, # 24 hours ago
                    1
                )
                binance_supported = len(rates) > 0
                logger.info(f"Binance support for {token}: {binance_supported}")
            except Exception as e:
                logger.warning(f"Error checking Binance support for {token}: {e}")
            
            # Check HyperLiquid
            try:
                hyperliquid_symbol = f"{token}/USDC:USDC"
                rates = hyperliquid.fetchFundingRateHistory(
                    hyperliquid_symbol,
                    int(time.time() * 1000) - 86400000, # 24 hours ago
                    1
                )
                hyperliquid_supported = len(rates) > 0
                logger.info(f"HyperLiquid support for {token}: {hyperliquid_supported}")
            except Exception as e:
                logger.warning(f"Error checking HyperLiquid support for {token}: {e}")
            
            # If supported on both, add to list
            if binance_supported and hyperliquid_supported:
                supported_tokens.append(token)
                logger.info(f"✅ {token} is supported on both exchanges")
            else:
                logger.info(f"❌ {token} is not supported on both exchanges")
            
            # Rate limiting to avoid API issues
            await asyncio.sleep(0.5)
        
        logger.info(f"Tokens supported on both exchanges via direct API calls: {supported_tokens}")
        return supported_tokens
    
    except Exception as e:
        logger.error(f"Error in direct API check: {e}")
        return []

async def main():
    logger.info("Starting to find common tokens on Binance and HyperLiquid...")
    
    # First try the market comparison approach
    common_tokens = await get_common_tokens()
    
    # If we didn't find any common tokens or want to double-check, try direct API calls
    if not common_tokens:
        logger.info("No common tokens found through market comparison, trying direct API checks...")
        common_tokens = await check_token_support_direct()
    
    logger.info("Script execution completed.")
    return common_tokens

if __name__ == "__main__":
    asyncio.run(main())