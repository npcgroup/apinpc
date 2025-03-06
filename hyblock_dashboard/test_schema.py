import sys
import os
import json
from datetime import datetime

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.database import connect_to_database, execute_query, get_logger

# Set up logger
logger = get_logger("test_schema")

def test_schema():
    """Test the database schema by inserting sample data"""
    logger.info("Testing database schema...")
    
    # Connect to database
    conn = connect_to_database()
    if not conn:
        logger.error("Failed to connect to database")
        return False
    
    try:
        # Sample data
        timestamp = datetime.utcnow()
        coin = "SUI"
        exchange = "BINANCE"
        timeframe = "1h"
        
        # Test hyblock_data table
        logger.info("Testing hyblock_data table...")
        data = {
            "open": 1.0,
            "high": 1.1,
            "low": 0.9,
            "close": 1.05,
            "volume": 1000.0
        }
        
        query = """
            INSERT INTO hyblock_data 
            (timestamp, endpoint, coin, exchange, timeframe, data)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        
        params = (
            timestamp,
            "market/kline",
            coin,
            exchange,
            timeframe,
            json.dumps(data)
        )
        
        result = execute_query(conn, query, params)
        if not result:
            logger.error("Failed to insert data into hyblock_data table")
            return False
        
        logger.info(f"Inserted data into hyblock_data table with ID {result[0][0]}")
        
        # Test hyblock_market_data table
        logger.info("Testing hyblock_market_data table...")
        query = """
            INSERT INTO hyblock_market_data 
            (timestamp, coin, exchange, timeframe, open, high, low, close, volume, additional_data)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        
        params = (
            timestamp,
            coin,
            exchange,
            timeframe,
            data["open"],
            data["high"],
            data["low"],
            data["close"],
            data["volume"],
            json.dumps(data)
        )
        
        result = execute_query(conn, query, params)
        if not result:
            logger.error("Failed to insert data into hyblock_market_data table")
            return False
        
        logger.info(f"Inserted data into hyblock_market_data table with ID {result[0][0]}")
        
        # Test hyblock_liquidity_data table
        logger.info("Testing hyblock_liquidity_data table...")
        orderbook = {
            "bids": [[1.0, 100.0], [0.9, 200.0]],
            "asks": [[1.1, 100.0], [1.2, 200.0]]
        }
        
        query = """
            INSERT INTO hyblock_liquidity_data 
            (timestamp, coin, exchange, timeframe, bid_depth, ask_depth, spread, orderbook)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        
        params = (
            timestamp,
            coin,
            exchange,
            timeframe,
            300.0,  # bid_depth
            300.0,  # ask_depth
            0.1,    # spread
            json.dumps(orderbook)
        )
        
        result = execute_query(conn, query, params)
        if not result:
            logger.error("Failed to insert data into hyblock_liquidity_data table")
            return False
        
        logger.info(f"Inserted data into hyblock_liquidity_data table with ID {result[0][0]}")
        
        # Test hyblock_funding_data table
        logger.info("Testing hyblock_funding_data table...")
        funding_data = {
            "fundingRate": 0.001,
            "fundingInterval": "8h",
            "nextFundingTime": timestamp.isoformat()
        }
        
        query = """
            INSERT INTO hyblock_funding_data 
            (timestamp, coin, exchange, funding_rate, funding_interval, next_funding_time, additional_data)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        
        params = (
            timestamp,
            coin,
            exchange,
            funding_data["fundingRate"],
            funding_data["fundingInterval"],
            timestamp,
            json.dumps(funding_data)
        )
        
        result = execute_query(conn, query, params)
        if not result:
            logger.error("Failed to insert data into hyblock_funding_data table")
            return False
        
        logger.info(f"Inserted data into hyblock_funding_data table with ID {result[0][0]}")
        
        # Test hyblock_open_interest_data table
        logger.info("Testing hyblock_open_interest_data table...")
        oi_data = {
            "openInterest": 1000000.0,
            "openInterestUsd": 1000000.0
        }
        
        query = """
            INSERT INTO hyblock_open_interest_data 
            (timestamp, coin, exchange, timeframe, open_interest, open_interest_usd, additional_data)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        
        params = (
            timestamp,
            coin,
            exchange,
            timeframe,
            oi_data["openInterest"],
            oi_data["openInterestUsd"],
            json.dumps(oi_data)
        )
        
        result = execute_query(conn, query, params)
        if not result:
            logger.error("Failed to insert data into hyblock_open_interest_data table")
            return False
        
        logger.info(f"Inserted data into hyblock_open_interest_data table with ID {result[0][0]}")
        
        # Query the data to verify it was inserted correctly
        logger.info("Querying data to verify it was inserted correctly...")
        
        # Query hyblock_data table
        query = """
            SELECT * FROM hyblock_data
            WHERE coin = %s AND exchange = %s AND timeframe = %s
            ORDER BY timestamp DESC
            LIMIT 1
        """
        
        params = (coin, exchange, timeframe)
        
        result = execute_query(conn, query, params)
        if not result:
            logger.error("Failed to query data from hyblock_data table")
            return False
        
        logger.info(f"Successfully queried data from hyblock_data table: {result[0]}")
        
        # Query hyblock_market_data table
        query = """
            SELECT * FROM hyblock_market_data
            WHERE coin = %s AND exchange = %s AND timeframe = %s
            ORDER BY timestamp DESC
            LIMIT 1
        """
        
        result = execute_query(conn, query, params)
        if not result:
            logger.error("Failed to query data from hyblock_market_data table")
            return False
        
        logger.info(f"Successfully queried data from hyblock_market_data table: {result[0]}")
        
        logger.info("All schema tests passed successfully!")
        return True
    
    except Exception as e:
        logger.error(f"Error testing schema: {e}")
        return False
    
    finally:
        conn.close()

if __name__ == "__main__":
    if test_schema():
        logger.info("Schema test completed successfully")
    else:
        logger.error("Schema test failed")
        sys.exit(1) 