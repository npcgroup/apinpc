import os
import sys
import json
import time
import asyncio
from datetime import datetime, timezone

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.database import connect_to_database, execute_query, get_logger
from collector.hyblock_api import HyblockAPI, DEFAULT_COINS, DEFAULT_EXCHANGES, DEFAULT_TIMEFRAMES

# Set up logger
logger = get_logger("data_collector")

async def store_data(conn, results):
    """Store the collected data in the database"""
    try:
        stored_count = 0  # Add counter to track stored records
        
        for result in results:
            endpoint = result["endpoint"]
            params = result["params"]
            data = result["data"]
            timestamp = datetime.fromisoformat(result["timestamp"])
            
            # Extract common parameters
            coin = params.get("coin")
            exchange = params.get("exchange")
            timeframe = params.get("timeframe")
            
            # Store in main hyblock_data table
            query = """
                INSERT INTO hyblock_data (timestamp, endpoint, coin, exchange, timeframe, data)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (timestamp, endpoint, coin, exchange, timeframe)
                DO UPDATE SET data = EXCLUDED.data
            """
            
            await conn.execute(
                query,
                (timestamp, endpoint, coin, exchange, timeframe, json.dumps(data))
            )
            
            # Process specialized data based on endpoint type
            await process_specialized_data(conn, endpoint, coin, exchange, timeframe, timestamp, data)
            stored_count += 1  # Increment counter on successful storage
            
        await conn.commit()
        logger.info(f"Successfully stored {len(results)} results in the database")
        
        return stored_count  # Return the number of items stored
        
    except Exception as e:
        logger.error(f"Error storing data: {e}")
        await conn.rollback()
        raise

async def process_specialized_data(conn, endpoint, coin, exchange, timeframe, timestamp, data):
    """Process and store data in specialized tables based on endpoint type"""
    try:
        # Determine endpoint type and store in appropriate table
        if "market" in endpoint.lower() or any(x in endpoint.lower() for x in ["kline", "candle", "ohlcv"]):
            await store_market_data(conn, coin, exchange, timeframe, timestamp, data)
            
        elif "orderbook" in endpoint.lower() or "depth" in endpoint.lower():
            await store_orderbook_data(conn, coin, exchange, timestamp, data)
            
        elif "funding" in endpoint.lower():
            await store_funding_data(conn, coin, exchange, timestamp, data)
            
        elif "open_interest" in endpoint.lower() or "oi" in endpoint.lower():
            await store_open_interest_data(conn, coin, exchange, timestamp, data)
            
        elif "liquidation" in endpoint.lower():
            await store_liquidation_data(conn, coin, exchange, timestamp, data)
            
        elif "trade" in endpoint.lower():
            await store_trade_data(conn, coin, exchange, timestamp, data)
            
        # Store in exchange_metrics for other types of data
        else:
            await store_exchange_metrics(conn, coin, exchange, endpoint, timestamp, data)
            
    except Exception as e:
        logger.error(f"Error processing specialized data: {e}")
        raise

async def store_market_data(conn, coin, exchange, timeframe, timestamp, data):
    """Store market data in the market_data table"""
    try:
        # Try to get the "data" field or use the entire dict
        if isinstance(data, dict):
            market_data = data.get("data", data)
            
            # Handle single entry as dict
            if isinstance(market_data, dict):
                query = """
                    INSERT INTO market_data 
                    (timestamp, coin, exchange, timeframe, open, high, low, close, volume, volume_usd)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    ON CONFLICT (timestamp, coin, exchange, timeframe) 
                    DO UPDATE SET 
                        open = EXCLUDED.open,
                        high = EXCLUDED.high,
                        low = EXCLUDED.low,
                        close = EXCLUDED.close,
                        volume = EXCLUDED.volume,
                        volume_usd = EXCLUDED.volume_usd
                """
                
                # Extract with safer conversions
                try:
                    open_price = float(market_data.get("open", 0))
                except (ValueError, TypeError):
                    open_price = 0
                    
                try:
                    high_price = float(market_data.get("high", 0))
                except (ValueError, TypeError):
                    high_price = 0
                    
                try:
                    low_price = float(market_data.get("low", 0))
                except (ValueError, TypeError):
                    low_price = 0
                    
                try:
                    close_price = float(market_data.get("close", 0))
                except (ValueError, TypeError):
                    close_price = 0
                    
                try:
                    volume = float(market_data.get("volume", 0))
                except (ValueError, TypeError):
                    volume = 0
                    
                try:
                    volume_usd = float(market_data.get("volumeUsd", market_data.get("volume_usd", 0)))
                except (ValueError, TypeError):
                    volume_usd = 0
                
                await conn.execute(
                    query,
                    timestamp,
                    coin,
                    exchange,
                    timeframe,
                    open_price,
                    high_price,
                    low_price,
                    close_price,
                    volume,
                    volume_usd
                )
                logger.info(f"Stored market data for {coin} on {exchange} with timeframe {timeframe}")
                
            # Handle multiple entries as list
            elif isinstance(market_data, list) and market_data:
                count = 0
                for item in market_data:
                    if isinstance(item, dict):
                        query = """
                            INSERT INTO market_data 
                            (timestamp, coin, exchange, timeframe, open, high, low, close, volume, volume_usd)
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                            ON CONFLICT (timestamp, coin, exchange, timeframe) 
                            DO UPDATE SET 
                                open = EXCLUDED.open,
                                high = EXCLUDED.high,
                                low = EXCLUDED.low,
                                close = EXCLUDED.close,
                                volume = EXCLUDED.volume,
                                volume_usd = EXCLUDED.volume_usd
                        """
                        
                        # Use item timestamp if available, otherwise use the main timestamp
                        item_timestamp = item.get("timestamp")
                        if item_timestamp:
                            try:
                                if isinstance(item_timestamp, str):
                                    item_timestamp = datetime.fromisoformat(item_timestamp)
                                elif isinstance(item_timestamp, (int, float)):
                                    item_timestamp = datetime.fromtimestamp(item_timestamp)
                            except (ValueError, TypeError):
                                item_timestamp = timestamp
                        else:
                            item_timestamp = timestamp
                        
                        # Extract with safer conversions
                        try:
                            open_price = float(item.get("open", 0))
                        except (ValueError, TypeError):
                            open_price = 0
                            
                        try:
                            high_price = float(item.get("high", 0))
                        except (ValueError, TypeError):
                            high_price = 0
                            
                        try:
                            low_price = float(item.get("low", 0))
                        except (ValueError, TypeError):
                            low_price = 0
                            
                        try:
                            close_price = float(item.get("close", 0))
                        except (ValueError, TypeError):
                            close_price = 0
                            
                        try:
                            volume = float(item.get("volume", 0))
                        except (ValueError, TypeError):
                            volume = 0
                            
                        try:
                            volume_usd = float(item.get("volumeUsd", item.get("volume_usd", 0)))
                        except (ValueError, TypeError):
                            volume_usd = 0
                        
                        await conn.execute(
                            query,
                            item_timestamp,
                            coin,
                            exchange,
                            timeframe,
                            open_price,
                            high_price,
                            low_price,
                            close_price,
                            volume,
                            volume_usd
                        )
                        count += 1
                
                if count > 0:
                    logger.info(f"Stored {count} market data entries for {coin} on {exchange} with timeframe {timeframe}")
    except Exception as e:
        logger.error(f"Error storing market data: {e}")
        raise

async def store_orderbook_data(conn, coin, exchange, timestamp, data):
    """Store orderbook data in the orderbook_data table"""
    try:
        if isinstance(data, dict):
            ob_data = data.get("data", data)  # Try to get "data" field or use the entire dict
            
            if isinstance(ob_data, dict):
                bids = ob_data.get("bids", [])
                asks = ob_data.get("asks", [])
                
                if bids and asks:
                    try:
                        best_bid = float(bids[0][0])
                        best_bid_quantity = float(bids[0][1])
                    except (IndexError, ValueError, TypeError):
                        logger.warning(f"Invalid bid data format for {coin} on {exchange}: {bids[:2]}")
                        best_bid = 0
                        best_bid_quantity = 0
                    
                    try:
                        best_ask = float(asks[0][0])
                        best_ask_quantity = float(asks[0][1])
                    except (IndexError, ValueError, TypeError):
                        logger.warning(f"Invalid ask data format for {coin} on {exchange}: {asks[:2]}")
                        best_ask = 0
                        best_ask_quantity = 0
                    
                    # Only proceed if we have valid bid/ask prices
                    if best_bid > 0 and best_ask > 0:
                        spread = best_ask - best_bid
                        mid_price = (best_bid + best_ask) / 2
                        
                        # Calculate depth with error handling
                        try:
                            depth_1pct = calculate_depth(bids, asks, 0.01, mid_price)
                        except Exception as e:
                            logger.warning(f"Error calculating 1% depth: {e}")
                            depth_1pct = 0
                            
                        try:
                            depth_2pct = calculate_depth(bids, asks, 0.02, mid_price)
                        except Exception as e:
                            logger.warning(f"Error calculating 2% depth: {e}")
                            depth_2pct = 0
                            
                        try:
                            depth_5pct = calculate_depth(bids, asks, 0.05, mid_price)
                        except Exception as e:
                            logger.warning(f"Error calculating 5% depth: {e}")
                            depth_5pct = 0
                        
                        query = """
                            INSERT INTO orderbook_data 
                            (timestamp, coin, exchange, bid_price, bid_quantity, ask_price, ask_quantity, 
                             spread, mid_price, depth_1pct, depth_2pct, depth_5pct)
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                            ON CONFLICT (timestamp, coin, exchange) 
                            DO UPDATE SET 
                                bid_price = EXCLUDED.bid_price,
                                bid_quantity = EXCLUDED.bid_quantity,
                                ask_price = EXCLUDED.ask_price,
                                ask_quantity = EXCLUDED.ask_quantity,
                                spread = EXCLUDED.spread,
                                mid_price = EXCLUDED.mid_price,
                                depth_1pct = EXCLUDED.depth_1pct,
                                depth_2pct = EXCLUDED.depth_2pct,
                                depth_5pct = EXCLUDED.depth_5pct
                        """
                        
                        await conn.execute(
                            query,
                            timestamp,
                            coin,
                            exchange,
                            best_bid,
                            best_bid_quantity,
                            best_ask,
                            best_ask_quantity,
                            spread,
                            mid_price,
                            depth_1pct,
                            depth_2pct,
                            depth_5pct
                        )
                        logger.info(f"Stored orderbook data for {coin} on {exchange} with spread {spread:.6f}")
                    else:
                        logger.warning(f"Invalid bid/ask prices for {coin} on {exchange}: bid={best_bid}, ask={best_ask}")
                else:
                    logger.warning(f"Empty bids or asks for {coin} on {exchange}")
            else:
                logger.warning(f"Orderbook data not in expected dict format for {coin} on {exchange}: {type(ob_data)}")
        else:
            logger.warning(f"Data not in expected dict format for {coin} on {exchange}: {type(data)}")
            
    except Exception as e:
        logger.error(f"Error storing orderbook data: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise

async def store_funding_data(conn, coin, exchange, timestamp, data):
    """Store funding rate data in the funding_rates table"""
    try:
        if isinstance(data, dict):
            funding_data = data.get("data", data)  # Try to get "data" field or use entire dict
            
            # Handle both dict and list formats
            if isinstance(funding_data, dict):
                # Handle single funding rate item as dict
                query = """
                    INSERT INTO funding_rates 
                    (timestamp, coin, exchange, funding_rate, funding_interval, next_funding_time)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (timestamp, coin, exchange) 
                    DO UPDATE SET 
                        funding_rate = EXCLUDED.funding_rate,
                        funding_interval = EXCLUDED.funding_interval,
                        next_funding_time = EXCLUDED.next_funding_time
                """
                
                # Convert funding rate to float with safer handling
                funding_rate = funding_data.get("fundingRate") or funding_data.get("funding_rate") or 0
                try:
                    funding_rate = float(funding_rate)
                except (ValueError, TypeError):
                    funding_rate = 0
                
                # Convert funding interval to int with safer handling
                funding_interval = funding_data.get("fundingInterval") or funding_data.get("funding_interval") or 0
                try:
                    funding_interval = int(funding_interval)
                except (ValueError, TypeError):
                    funding_interval = 0
                
                # Get next funding time
                next_funding_time = funding_data.get("nextFundingTime") or funding_data.get("next_funding_time")
                
                await conn.execute(
                    query,
                    timestamp,
                    coin,
                    exchange,
                    funding_rate,
                    funding_interval,
                    next_funding_time
                )
                logger.info(f"Stored funding rate {funding_rate} for {coin} on {exchange}")
                
            elif isinstance(funding_data, list) and funding_data:
                # Handle multiple funding rates as list
                for item in funding_data:
                    if isinstance(item, dict):
                        query = """
                            INSERT INTO funding_rates 
                            (timestamp, coin, exchange, funding_rate, funding_interval, next_funding_time)
                            VALUES ($1, $2, $3, $4, $5, $6)
                            ON CONFLICT (timestamp, coin, exchange) 
                            DO UPDATE SET 
                                funding_rate = EXCLUDED.funding_rate,
                                funding_interval = EXCLUDED.funding_interval,
                                next_funding_time = EXCLUDED.next_funding_time
                        """
                        
                        # Extract fields safely
                        try:
                            funding_rate = float(item.get("fundingRate") or item.get("funding_rate") or 0)
                        except (ValueError, TypeError):
                            funding_rate = 0
                            
                        try:
                            funding_interval = int(item.get("fundingInterval") or item.get("funding_interval") or 0)
                        except (ValueError, TypeError):
                            funding_interval = 0
                            
                        next_funding_time = item.get("nextFundingTime") or item.get("next_funding_time")
                        
                        # Use item timestamp if available, otherwise use the main timestamp
                        item_timestamp = item.get("timestamp")
                        if item_timestamp:
                            try:
                                if isinstance(item_timestamp, str):
                                    item_timestamp = datetime.fromisoformat(item_timestamp)
                                elif isinstance(item_timestamp, (int, float)):
                                    item_timestamp = datetime.fromtimestamp(item_timestamp)
                            except (ValueError, TypeError):
                                item_timestamp = timestamp
                        else:
                            item_timestamp = timestamp
                        
                        await conn.execute(
                            query,
                            item_timestamp,
                            coin,
                            exchange,
                            funding_rate,
                            funding_interval,
                            next_funding_time
                        )
                logger.info(f"Stored {len(funding_data)} funding rates for {coin} on {exchange}")
    except Exception as e:
        logger.error(f"Error storing funding data: {e}")
        raise

async def store_open_interest_data(conn, coin, exchange, timestamp, data):
    """Store open interest data in the open_interest table"""
    try:
        if isinstance(data, dict):
            oi_data = data.get("data", data)  # Try to get "data" field or use entire dict
            
            if isinstance(oi_data, dict):
                # Handle single open interest item as dict
                query = """
                    INSERT INTO open_interest 
                    (timestamp, coin, exchange, open_interest, open_interest_usd)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (timestamp, coin, exchange) 
                    DO UPDATE SET 
                        open_interest = EXCLUDED.open_interest,
                        open_interest_usd = EXCLUDED.open_interest_usd
                """
                
                # Extract open interest with safer handling
                try:
                    open_interest = float(oi_data.get("openInterest") or oi_data.get("open_interest") or 0)
                except (ValueError, TypeError):
                    open_interest = 0
                
                # Extract open interest USD with safer handling
                try:
                    open_interest_usd = float(oi_data.get("openInterestUsd") or oi_data.get("open_interest_usd") or 0)
                except (ValueError, TypeError):
                    open_interest_usd = 0
                
                await conn.execute(
                    query,
                    timestamp,
                    coin,
                    exchange,
                    open_interest,
                    open_interest_usd
                )
                logger.info(f"Stored open interest {open_interest} for {coin} on {exchange}")
                
            elif isinstance(oi_data, list) and oi_data:
                # Handle multiple open interest entries as list
                for item in oi_data:
                    if isinstance(item, dict):
                        query = """
                            INSERT INTO open_interest 
                            (timestamp, coin, exchange, open_interest, open_interest_usd)
                            VALUES ($1, $2, $3, $4, $5)
                            ON CONFLICT (timestamp, coin, exchange) 
                            DO UPDATE SET 
                                open_interest = EXCLUDED.open_interest,
                                open_interest_usd = EXCLUDED.open_interest_usd
                        """
                        
                        # Extract fields safely
                        try:
                            open_interest = float(item.get("openInterest") or item.get("open_interest") or 0)
                        except (ValueError, TypeError):
                            open_interest = 0
                            
                        try:
                            open_interest_usd = float(item.get("openInterestUsd") or item.get("open_interest_usd") or 0)
                        except (ValueError, TypeError):
                            open_interest_usd = 0
                            
                        # Use item timestamp if available, otherwise use the main timestamp
                        item_timestamp = item.get("timestamp")
                        if item_timestamp:
                            try:
                                if isinstance(item_timestamp, str):
                                    item_timestamp = datetime.fromisoformat(item_timestamp)
                                elif isinstance(item_timestamp, (int, float)):
                                    item_timestamp = datetime.fromtimestamp(item_timestamp)
                            except (ValueError, TypeError):
                                item_timestamp = timestamp
                        else:
                            item_timestamp = timestamp
                        
                        await conn.execute(
                            query,
                            item_timestamp,
                            coin,
                            exchange,
                            open_interest,
                            open_interest_usd
                        )
                logger.info(f"Stored {len(oi_data)} open interest entries for {coin} on {exchange}")
    except Exception as e:
        logger.error(f"Error storing open interest data: {e}")
        raise

async def store_liquidation_data(conn, coin, exchange, timestamp, data):
    """Store liquidation data in the liquidations table"""
    try:
        if isinstance(data, dict):
            liq_data = data.get("data", data)  # Try to get "data" field or use entire dict
            
            # Handle both single entry and list formats
            if isinstance(liq_data, dict):
                # Single liquidation entry
                query = """
                    INSERT INTO liquidations 
                    (timestamp, coin, exchange, side, quantity, price, liquidation_value_usd)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT (timestamp, coin, exchange, side) 
                    DO UPDATE SET 
                        quantity = EXCLUDED.quantity,
                        price = EXCLUDED.price,
                        liquidation_value_usd = EXCLUDED.liquidation_value_usd
                """
                
                # Normalize the side value (buy/sell/long/short)
                raw_side = liq_data.get("side") or liq_data.get("direction") or liq_data.get("positionSide") or "unknown"
                if raw_side.lower() in ["buy", "long"]:
                    side = "buy"
                elif raw_side.lower() in ["sell", "short"]:
                    side = "sell"
                else:
                    side = raw_side.lower()
                
                # Extract quantity with safer handling
                try:
                    quantity = float(liq_data.get("quantity") or liq_data.get("amount") or liq_data.get("size") or liq_data.get("qty") or 0)
                except (ValueError, TypeError):
                    quantity = 0
                
                # Extract price with safer handling
                try:
                    price = float(liq_data.get("price") or liq_data.get("avgPrice") or liq_data.get("avg_price") or 0)
                except (ValueError, TypeError):
                    price = 0
                
                # Extract value with safer handling
                try:
                    value = float(liq_data.get("value") or liq_data.get("valueUsd") or liq_data.get("liquidation_value_usd") or 0)
                    if value == 0 and price > 0 and quantity > 0:
                        value = price * quantity  # Calculate if not provided
                except (ValueError, TypeError):
                    value = 0
                    if price > 0 and quantity > 0:
                        value = price * quantity
                
                # Only insert if we have meaningful liquidation data
                if quantity > 0 or value > 0:
                    await conn.execute(
                        query,
                        timestamp,
                        coin,
                        exchange,
                        side,
                        quantity,
                        price,
                        value
                    )
                    logger.info(f"Stored single liquidation data for {coin} on {exchange}: side={side}, value=${value:.2f}")
                else:
                    logger.warning(f"Skipping empty liquidation data for {coin} on {exchange}")
                
            elif isinstance(liq_data, list) and liq_data:
                # Multiple liquidation entries
                count = 0
                total_value = 0
                
                for item in liq_data:
                    if isinstance(item, dict):
                        query = """
                            INSERT INTO liquidations 
                            (timestamp, coin, exchange, side, quantity, price, liquidation_value_usd)
                            VALUES ($1, $2, $3, $4, $5, $6, $7)
                            ON CONFLICT (timestamp, coin, exchange, side) 
                            DO UPDATE SET 
                                quantity = EXCLUDED.quantity,
                                price = EXCLUDED.price,
                                liquidation_value_usd = EXCLUDED.liquidation_value_usd
                        """
                        
                        # Extract and process item timestamp if available
                        item_timestamp = item.get("timestamp") or item.get("time")
                        if item_timestamp:
                            try:
                                if isinstance(item_timestamp, str):
                                    item_timestamp = datetime.fromisoformat(item_timestamp.replace('Z', '+00:00'))
                                elif isinstance(item_timestamp, (int, float)):
                                    # Check if timestamp is in milliseconds (13 digits) or seconds (10 digits)
                                    if len(str(int(item_timestamp))) > 10:
                                        item_timestamp = datetime.fromtimestamp(item_timestamp / 1000)
                                    else:
                                        item_timestamp = datetime.fromtimestamp(item_timestamp)
                            except (ValueError, TypeError):
                                item_timestamp = timestamp
                        else:
                            item_timestamp = timestamp
                        
                        # Normalize the side value (buy/sell/long/short)
                        raw_side = item.get("side") or item.get("direction") or item.get("positionSide") or "unknown"
                        if raw_side.lower() in ["buy", "long"]:
                            side = "buy"
                        elif raw_side.lower() in ["sell", "short"]:
                            side = "sell"
                        else:
                            side = raw_side.lower()
                        
                        # Extract quantity with safer handling
                        try:
                            quantity = float(item.get("quantity") or item.get("amount") or item.get("size") or item.get("qty") or 0)
                        except (ValueError, TypeError):
                            quantity = 0
                        
                        # Extract price with safer handling
                        try:
                            price = float(item.get("price") or item.get("avgPrice") or item.get("avg_price") or 0)
                        except (ValueError, TypeError):
                            price = 0
                        
                        # Extract value with safer handling
                        try:
                            value = float(item.get("value") or item.get("valueUsd") or item.get("liquidation_value_usd") or 0)
                            if value == 0 and price > 0 and quantity > 0:
                                value = price * quantity  # Calculate if not provided
                        except (ValueError, TypeError):
                            value = 0
                            if price > 0 and quantity > 0:
                                value = price * quantity
                        
                        # Only insert if we have meaningful liquidation data
                        if quantity > 0 or value > 0:
                            await conn.execute(
                                query,
                                item_timestamp,
                                coin,
                                exchange,
                                side,
                                quantity,
                                price,
                                value
                            )
                            count += 1
                            total_value += value
                
                if count > 0:
                    logger.info(f"Stored {count} liquidation entries for {coin} on {exchange} with total value ${total_value:.2f}")
                else:
                    logger.warning(f"No valid liquidation entries found for {coin} on {exchange}")
            else:
                logger.warning(f"Liquidation data not in expected format for {coin} on {exchange}: {type(liq_data)}")
        else:
            logger.warning(f"Data not in expected dict format for {coin} on {exchange}: {type(data)}")
            
    except Exception as e:
        logger.error(f"Error storing liquidation data: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise

async def store_trade_data(conn, coin, exchange, timestamp, data):
    """Store trade data in the trades table"""
    try:
        if isinstance(data, dict):
            trade_data = data.get("data", data)  # Try to get "data" field or use entire dict
            
            # Handle both single entry and list formats
            if isinstance(trade_data, dict):
                # Single trade entry
                query = """
                    INSERT INTO trades 
                    (timestamp, coin, exchange, side, price, quantity, value_usd)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT (timestamp, coin, exchange, side, price) 
                    DO UPDATE SET 
                        quantity = EXCLUDED.quantity,
                        value_usd = EXCLUDED.value_usd
                """
                
                # Normalize side value
                raw_side = trade_data.get("side") or trade_data.get("direction") or trade_data.get("type") or "unknown"
                if raw_side.lower() in ["buy", "long", "bid"]:
                    side = "buy"
                elif raw_side.lower() in ["sell", "short", "ask"]:
                    side = "sell"
                else:
                    side = raw_side.lower()
                
                # Extract price with safer handling
                try:
                    price = float(trade_data.get("price") or trade_data.get("dealPrice") or trade_data.get("deal_price") or 0)
                except (ValueError, TypeError):
                    price = 0
                
                # Extract quantity with safer handling
                try:
                    quantity = float(trade_data.get("quantity") or trade_data.get("amount") or 
                                   trade_data.get("size") or trade_data.get("qty") or 
                                   trade_data.get("dealSize") or trade_data.get("deal_size") or 0)
                except (ValueError, TypeError):
                    quantity = 0
                
                # Extract or calculate value with safer handling
                try:
                    value = float(trade_data.get("value") or trade_data.get("valueUsd") or 
                                trade_data.get("value_usd") or trade_data.get("dealValue") or 
                                trade_data.get("deal_value") or 0)
                    if value == 0 and price > 0 and quantity > 0:
                        value = price * quantity  # Calculate value if not provided
                except (ValueError, TypeError):
                    value = 0
                    if price > 0 and quantity > 0:
                        value = price * quantity  # Calculate value if not provided
                
                # Only store meaningful trade data
                if price > 0 and quantity > 0:
                    await conn.execute(
                        query,
                        timestamp,
                        coin,
                        exchange,
                        side,
                        price,
                        quantity,
                        value
                    )
                    logger.info(f"Stored single trade data for {coin} on {exchange}: {side} {quantity} @ {price}, value=${value:.2f}")
                else:
                    logger.warning(f"Skipping invalid trade data for {coin} on {exchange}: price={price}, qty={quantity}")
                
            elif isinstance(trade_data, list) and trade_data:
                # Multiple trade entries
                count = 0
                total_value = 0
                timestamp_map = {}  # To track multiple trades at same timestamp
                
                for item in trade_data:
                    if isinstance(item, dict):
                        # Extract and process item timestamp if available
                        item_timestamp = item.get("timestamp") or item.get("time") or item.get("dealTime") or item.get("deal_time")
                        if item_timestamp:
                            try:
                                if isinstance(item_timestamp, str):
                                    item_timestamp = datetime.fromisoformat(item_timestamp.replace('Z', '+00:00'))
                                elif isinstance(item_timestamp, (int, float)):
                                    # Check if timestamp is in milliseconds (13 digits) or seconds (10 digits)
                                    if len(str(int(item_timestamp))) > 10:
                                        item_timestamp = datetime.fromtimestamp(item_timestamp / 1000)
                                    else:
                                        item_timestamp = datetime.fromtimestamp(item_timestamp)
                            except (ValueError, TypeError):
                                item_timestamp = timestamp
                        else:
                            item_timestamp = timestamp
                        
                        # Normalize side value
                        raw_side = item.get("side") or item.get("direction") or item.get("type") or "unknown"
                        if raw_side.lower() in ["buy", "long", "bid"]:
                            side = "buy"
                        elif raw_side.lower() in ["sell", "short", "ask"]:
                            side = "sell"
                        else:
                            side = raw_side.lower()
                        
                        # Extract price with safer handling
                        try:
                            price = float(item.get("price") or item.get("dealPrice") or item.get("deal_price") or 0)
                        except (ValueError, TypeError):
                            price = 0
                        
                        # Extract quantity with safer handling
                        try:
                            quantity = float(item.get("quantity") or item.get("amount") or 
                                           item.get("size") or item.get("qty") or 
                                           item.get("dealSize") or item.get("deal_size") or 0)
                        except (ValueError, TypeError):
                            quantity = 0
                        
                        # Extract or calculate value with safer handling
                        try:
                            value = float(item.get("value") or item.get("valueUsd") or 
                                        item.get("value_usd") or item.get("dealValue") or 
                                        item.get("deal_value") or 0)
                            if value == 0 and price > 0 and quantity > 0:
                                value = price * quantity  # Calculate value if not provided
                        except (ValueError, TypeError):
                            value = 0
                            if price > 0 and quantity > 0:
                                value = price * quantity
                        
                        # Skip invalid trades
                        if price <= 0 or quantity <= 0:
                            continue
                        
                        # Create a key to handle potential timestamp/side/price collisions
                        key = f"{item_timestamp}_{side}_{price}"
                        if key in timestamp_map:
                            # For duplicates, aggregate the quantity and value
                            timestamp_map[key]["quantity"] += quantity
                            timestamp_map[key]["value"] += value
                        else:
                            timestamp_map[key] = {
                                "timestamp": item_timestamp,
                                "side": side,
                                "price": price,
                                "quantity": quantity,
                                "value": value
                            }
                
                # Insert the aggregated trades
                for key, trade in timestamp_map.items():
                    query = """
                        INSERT INTO trades 
                        (timestamp, coin, exchange, side, price, quantity, value_usd)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                        ON CONFLICT (timestamp, coin, exchange, side, price) 
                        DO UPDATE SET 
                            quantity = EXCLUDED.quantity,
                            value_usd = EXCLUDED.value_usd
                    """
                    
                    await conn.execute(
                        query,
                        trade["timestamp"],
                        coin,
                        exchange,
                        trade["side"],
                        trade["price"],
                        trade["quantity"],
                        trade["value"]
                    )
                    count += 1
                    total_value += trade["value"]
                
                if count > 0:
                    logger.info(f"Stored {count} trade entries for {coin} on {exchange} with total value ${total_value:.2f}")
                else:
                    logger.warning(f"No valid trade entries found for {coin} on {exchange}")
            else:
                logger.warning(f"Trade data not in expected format for {coin} on {exchange}: {type(trade_data)}")
        else:
            logger.warning(f"Data not in expected dict format for {coin} on {exchange}: {type(data)}")
    
    except Exception as e:
        logger.error(f"Error storing trade data: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise

async def store_exchange_metrics(conn, coin, exchange, metric_type, timestamp, data):
    """Store other exchange metrics in the exchange_metrics table"""
    try:
        if isinstance(data, dict):
            query = """
                INSERT INTO exchange_metrics 
                (timestamp, exchange, coin, metric_type, value, additional_data)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (timestamp, exchange, coin, metric_type) 
                DO UPDATE SET 
                    value = EXCLUDED.value,
                    additional_data = EXCLUDED.additional_data
            """
            await conn.execute(
                query,
                timestamp,
                exchange,
                coin,
                metric_type,
                float(data.get("value", 0)),
                json.dumps(data)
            )
    except Exception as e:
        logger.error(f"Error storing exchange metrics: {e}")
        raise

def calculate_depth(bids, asks, depth_percent, mid_price):
    """Calculate order book depth at given percentage from mid price"""
    depth = 0
    lower_bound = mid_price * (1 - depth_percent)
    upper_bound = mid_price * (1 + depth_percent)
    
    for bid in bids:
        if float(bid[0]) >= lower_bound:
            depth += float(bid[1])
            
    for ask in asks:
        if float(ask[0]) <= upper_bound:
            depth += float(ask[1])
            
    return depth

async def collect_data(conn, coins=None, exchanges=None, timeframes=None):
    """Collect data from the Hyblock API and store it in the database"""
    if coins is None:
        coins = DEFAULT_COINS
    
    if exchanges is None:
        exchanges = DEFAULT_EXCHANGES
    
    if timeframes is None:
        timeframes = DEFAULT_TIMEFRAMES
    
    logger.info(f"Collecting data for coins: {coins}, exchanges: {exchanges}, timeframes: {timeframes}")
    
    # Initialize API client
    api = await HyblockAPI().initialize()
    
    try:
        total_results = 0
        total_stored = 0
        
        # Collect data for each coin
        for coin in coins:
            logger.info(f"Collecting data for {coin}...")
            
            try:
                # Fetch data from all endpoints for this coin
                results = await api.fetch_all_for_coin(coin, exchanges, timeframes)
                
                if results:
                    logger.info(f"Fetched {len(results)} results for {coin}")
                    total_results += len(results)
                    
                    # Log the first result for debugging
                    if len(results) > 0:
                        first_result = results[0]
                        logger.info(f"First result: endpoint={first_result.get('endpoint')}, params={first_result.get('params')}")
                        logger.info(f"Data structure: {type(first_result.get('data'))}, keys={first_result.get('data').keys() if isinstance(first_result.get('data'), dict) else 'not a dict'}")
                    
                    # Store the results in the database
                    stored_count = await store_data(conn, results)
                    total_stored += stored_count
                    
                    logger.info(f"Stored {stored_count} results for {coin}")
                else:
                    logger.warning(f"No results fetched for {coin}")
            except Exception as e:
                logger.error(f"Error collecting data for {coin}: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                # Continue with the next coin
                continue
        
        logger.info(f"Data collection completed. Fetched {total_results} results, stored {total_stored} results.")
        return True
    
    except Exception as e:
        logger.error(f"Error collecting data: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False
    
    finally:
        await api.close()

async def run_data_collection():
    """Run continuous data collection"""
    logger.info("Starting Hyblock data collection")
    
    try:
        # Connect to database
        conn = connect_to_database()
        if not conn:
            logger.error("Failed to connect to database")
            return
        
        logger.info("Connected to database successfully")
        
        # Run continuous data collection
        while True:
            start_time = time.time()
            
            try:
                # Collect data
                success = await collect_data(conn)
                
                if success:
                    logger.info("Data collection cycle completed successfully")
                else:
                    logger.warning("Data collection cycle failed")
                
                # Calculate time taken and sleep for the remainder of 5 minutes
                elapsed = time.time() - start_time
                sleep_time = max(0, 300.0 - elapsed)  # Collect data every 5 minutes
                
                logger.info(f"Data collection cycle completed in {elapsed:.2f}s, sleeping for {sleep_time:.2f}s")
                await asyncio.sleep(sleep_time)
            
            except Exception as e:
                logger.error(f"Error in data collection cycle: {e}")
                # Sleep for 30 seconds before retrying
                await asyncio.sleep(30)
    
    except asyncio.CancelledError:
        logger.info("Data collection cancelled")
    except Exception as e:
        logger.error(f"Error in data collection: {e}")
    finally:
        if conn:
            conn.close()
            logger.info("Database connection closed")

async def main():
    """Main function to run data collector"""
    try:
        await run_data_collection()
    except KeyboardInterrupt:
        logger.info("Data collection terminated by user")
    except Exception as e:
        logger.error(f"Unhandled exception in main: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Program terminated by user")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}") 