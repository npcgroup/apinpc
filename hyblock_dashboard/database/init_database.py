import asyncio
import asyncpg
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.database import get_logger

# Load environment variables
load_dotenv()

# Set up logger
logger = get_logger("init_database")

async def init_database():
    """Initialize the database with all required tables"""
    try:
        conn = await asyncpg.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", 5432),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "postgres"),
            database=os.getenv("DB_NAME", "hyblock_data")
        )
        
        # Enable TimescaleDB extension
        await conn.execute('CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;')
        
        # Create the main raw data table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS hyblock_data (
                timestamp TIMESTAMPTZ NOT NULL,
                endpoint TEXT NOT NULL,
                coin TEXT NOT NULL,
                exchange TEXT NOT NULL,
                timeframe TEXT,
                data JSONB NOT NULL,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (timestamp, endpoint, coin, exchange, timeframe)
            );
            
            -- Convert to hypertable
            SELECT create_hypertable('hyblock_data', 'timestamp', if_not_exists => TRUE, migrate_data => TRUE);
        """)
        
        # Create specialized tables
        await conn.execute("""
            -- Market data (OHLCV)
            CREATE TABLE IF NOT EXISTS market_data (
                timestamp TIMESTAMPTZ NOT NULL,
                coin TEXT NOT NULL,
                exchange TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                open NUMERIC,
                high NUMERIC,
                low NUMERIC,
                close NUMERIC,
                volume NUMERIC,
                volume_usd NUMERIC,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (timestamp, coin, exchange, timeframe)
            );
            SELECT create_hypertable('market_data', 'timestamp', if_not_exists => TRUE, migrate_data => TRUE);
            
            -- Orderbook data
            CREATE TABLE IF NOT EXISTS orderbook_data (
                timestamp TIMESTAMPTZ NOT NULL,
                coin TEXT NOT NULL,
                exchange TEXT NOT NULL,
                bid_price NUMERIC,
                bid_quantity NUMERIC,
                ask_price NUMERIC,
                ask_quantity NUMERIC,
                spread NUMERIC,
                mid_price NUMERIC,
                depth_1pct NUMERIC,
                depth_2pct NUMERIC,
                depth_5pct NUMERIC,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (timestamp, coin, exchange)
            );
            SELECT create_hypertable('orderbook_data', 'timestamp', if_not_exists => TRUE, migrate_data => TRUE);
            
            -- Funding rates
            CREATE TABLE IF NOT EXISTS funding_rates (
                timestamp TIMESTAMPTZ NOT NULL,
                coin TEXT NOT NULL,
                exchange TEXT NOT NULL,
                funding_rate NUMERIC,
                funding_interval INTEGER,
                next_funding_time TIMESTAMPTZ,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (timestamp, coin, exchange)
            );
            SELECT create_hypertable('funding_rates', 'timestamp', if_not_exists => TRUE, migrate_data => TRUE);
            
            -- Open interest
            CREATE TABLE IF NOT EXISTS open_interest (
                timestamp TIMESTAMPTZ NOT NULL,
                coin TEXT NOT NULL,
                exchange TEXT NOT NULL,
                open_interest NUMERIC,
                open_interest_usd NUMERIC,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (timestamp, coin, exchange)
            );
            SELECT create_hypertable('open_interest', 'timestamp', if_not_exists => TRUE, migrate_data => TRUE);
            
            -- Liquidations
            CREATE TABLE IF NOT EXISTS liquidations (
                timestamp TIMESTAMPTZ NOT NULL,
                coin TEXT NOT NULL,
                exchange TEXT NOT NULL,
                side TEXT,
                quantity NUMERIC,
                price NUMERIC,
                liquidation_value_usd NUMERIC,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (timestamp, coin, exchange, side)
            );
            SELECT create_hypertable('liquidations', 'timestamp', if_not_exists => TRUE, migrate_data => TRUE);
            
            -- Trades
            CREATE TABLE IF NOT EXISTS trades (
                timestamp TIMESTAMPTZ NOT NULL,
                coin TEXT NOT NULL,
                exchange TEXT NOT NULL,
                side TEXT,
                price NUMERIC,
                quantity NUMERIC,
                value_usd NUMERIC,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (timestamp, coin, exchange, price)
            );
            SELECT create_hypertable('trades', 'timestamp', if_not_exists => TRUE, migrate_data => TRUE);
            
            -- Exchange metrics
            CREATE TABLE IF NOT EXISTS exchange_metrics (
                timestamp TIMESTAMPTZ NOT NULL,
                exchange TEXT NOT NULL,
                coin TEXT NOT NULL,
                metric_type TEXT NOT NULL,
                value NUMERIC,
                additional_data JSONB,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (timestamp, exchange, coin, metric_type)
            );
            SELECT create_hypertable('exchange_metrics', 'timestamp', if_not_exists => TRUE, migrate_data => TRUE);
        """)
        
        logger.info("Database initialized successfully")
        await conn.close()
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(init_database()) 