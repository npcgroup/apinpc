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
logger = get_logger("enhanced_schema")

async def create_enhanced_schema():
    """Create enhanced database schema with specialized tables for all categories"""
    try:
        conn = await asyncpg.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", 5432),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "postgres"),
            database=os.getenv("DB_NAME", "hyblock_data")
        )
        
        # Create specialized tables for each category
        await conn.execute("""
            -- Orderbook category tables
            CREATE TABLE IF NOT EXISTS orderbook_depth (
                timestamp TIMESTAMPTZ NOT NULL,
                coin TEXT NOT NULL,
                exchange TEXT NOT NULL,
                bid_depth NUMERIC,
                ask_depth NUMERIC,
                total_depth NUMERIC,
                bid_ask_ratio NUMERIC,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (timestamp, coin, exchange)
            );
            SELECT create_hypertable('orderbook_depth', 'timestamp', if_not_exists => TRUE, migrate_data => TRUE);
            
            CREATE TABLE IF NOT EXISTS orderbook_imbalance (
                timestamp TIMESTAMPTZ NOT NULL,
                coin TEXT NOT NULL,
                exchange TEXT NOT NULL,
                imbalance_ratio NUMERIC,
                imbalance_direction TEXT,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (timestamp, coin, exchange)
            );
            SELECT create_hypertable('orderbook_imbalance', 'timestamp', if_not_exists => TRUE, migrate_data => TRUE);
            
            CREATE TABLE IF NOT EXISTS asks_increase_decrease (
                timestamp TIMESTAMPTZ NOT NULL,
                coin TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                exchange TEXT,
                asks_increase_decrease NUMERIC,
                market_types TEXT,
                additional_data JSONB,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (timestamp, coin, timeframe)
            );
            SELECT create_hypertable('asks_increase_decrease', 'timestamp', if_not_exists => TRUE, migrate_data => TRUE);
            
            CREATE TABLE IF NOT EXISTS bids_increase_decrease (
                timestamp TIMESTAMPTZ NOT NULL,
                coin TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                exchange TEXT,
                bids_increase_decrease NUMERIC,
                market_types TEXT,
                additional_data JSONB,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (timestamp, coin, timeframe)
            );
            SELECT create_hypertable('bids_increase_decrease', 'timestamp', if_not_exists => TRUE, migrate_data => TRUE);
            
            -- Options category tables
            CREATE TABLE IF NOT EXISTS options_data (
                timestamp TIMESTAMPTZ NOT NULL,
                coin TEXT NOT NULL,
                exchange TEXT NOT NULL,
                expiry_date TIMESTAMPTZ,
                strike_price NUMERIC,
                option_type TEXT,
                implied_volatility NUMERIC,
                open_interest NUMERIC,
                volume NUMERIC,
                delta NUMERIC,
                gamma NUMERIC,
                theta NUMERIC,
                vega NUMERIC,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (timestamp, coin, exchange, expiry_date, strike_price, option_type)
            );
            SELECT create_hypertable('options_data', 'timestamp', if_not_exists => TRUE, migrate_data => TRUE);
            
            -- Orderflow category tables
            CREATE TABLE IF NOT EXISTS cvd_data (
                timestamp TIMESTAMPTZ NOT NULL,
                coin TEXT NOT NULL,
                exchange TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                cvd_value NUMERIC,
                delta_value NUMERIC,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (timestamp, coin, exchange, timeframe)
            );
            SELECT create_hypertable('cvd_data', 'timestamp', if_not_exists => TRUE, migrate_data => TRUE);
            
            CREATE TABLE IF NOT EXISTS trades_by_side (
                timestamp TIMESTAMPTZ NOT NULL,
                coin TEXT NOT NULL,
                exchange TEXT NOT NULL,
                buy_volume NUMERIC,
                sell_volume NUMERIC,
                buy_count INTEGER,
                sell_count INTEGER,
                buy_sell_ratio NUMERIC,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (timestamp, coin, exchange)
            );
            SELECT create_hypertable('trades_by_side', 'timestamp', if_not_exists => TRUE, migrate_data => TRUE);
            
            CREATE TABLE IF NOT EXISTS large_trades (
                timestamp TIMESTAMPTZ NOT NULL,
                coin TEXT NOT NULL,
                exchange TEXT NOT NULL,
                side TEXT,
                price NUMERIC,
                quantity NUMERIC,
                value_usd NUMERIC,
                is_large BOOLEAN,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (timestamp, coin, exchange, price)
            );
            SELECT create_hypertable('large_trades', 'timestamp', if_not_exists => TRUE, migrate_data => TRUE);
            
            -- Open Interest category tables
            CREATE TABLE IF NOT EXISTS open_interest_change (
                timestamp TIMESTAMPTZ NOT NULL,
                coin TEXT NOT NULL,
                exchange TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                open_interest NUMERIC,
                open_interest_usd NUMERIC,
                change_amount NUMERIC,
                change_percent NUMERIC,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (timestamp, coin, exchange, timeframe)
            );
            SELECT create_hypertable('open_interest_change', 'timestamp', if_not_exists => TRUE, migrate_data => TRUE);
            
            -- Liquidity category tables
            CREATE TABLE IF NOT EXISTS liquidity_data (
                timestamp TIMESTAMPTZ NOT NULL,
                coin TEXT NOT NULL,
                exchange TEXT NOT NULL,
                liquidity_score NUMERIC,
                bid_liquidity NUMERIC,
                ask_liquidity NUMERIC,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (timestamp, coin, exchange)
            );
            SELECT create_hypertable('liquidity_data', 'timestamp', if_not_exists => TRUE, migrate_data => TRUE);
            
            -- Funding Rate category tables
            CREATE TABLE IF NOT EXISTS funding_rate_data (
                timestamp TIMESTAMPTZ NOT NULL,
                coin TEXT NOT NULL,
                exchange TEXT NOT NULL,
                funding_rate NUMERIC,
                predicted_rate NUMERIC,
                next_funding_time TIMESTAMPTZ,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (timestamp, coin, exchange)
            );
            SELECT create_hypertable('funding_rate_data', 'timestamp', if_not_exists => TRUE, migrate_data => TRUE);
            
            -- Longs and Shorts category tables
            CREATE TABLE IF NOT EXISTS long_short_ratio (
                timestamp TIMESTAMPTZ NOT NULL,
                coin TEXT NOT NULL,
                exchange TEXT NOT NULL,
                long_short_ratio NUMERIC,
                long_account_ratio NUMERIC,
                short_account_ratio NUMERIC,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (timestamp, coin, exchange)
            );
            SELECT create_hypertable('long_short_ratio', 'timestamp', if_not_exists => TRUE, migrate_data => TRUE);
            
            -- Sentiment category tables
            CREATE TABLE IF NOT EXISTS sentiment_data (
                timestamp TIMESTAMPTZ NOT NULL,
                coin TEXT NOT NULL,
                source TEXT NOT NULL,
                sentiment_score NUMERIC,
                sentiment_label TEXT,
                volume NUMERIC,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (timestamp, coin, source)
            );
            SELECT create_hypertable('sentiment_data', 'timestamp', if_not_exists => TRUE, migrate_data => TRUE);
            
            -- Profile Tool category tables
            CREATE TABLE IF NOT EXISTS profile_data (
                timestamp TIMESTAMPTZ NOT NULL,
                coin TEXT NOT NULL,
                profile_type TEXT NOT NULL,
                value NUMERIC,
                additional_data JSONB,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (timestamp, coin, profile_type)
            );
            SELECT create_hypertable('profile_data', 'timestamp', if_not_exists => TRUE, migrate_data => TRUE);
            
            -- Catalog category tables
            CREATE TABLE IF NOT EXISTS catalog_data (
                timestamp TIMESTAMPTZ NOT NULL,
                exchange TEXT NOT NULL,
                coin_count INTEGER,
                data JSONB,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (timestamp, exchange)
            );
            SELECT create_hypertable('catalog_data', 'timestamp', if_not_exists => TRUE, migrate_data => TRUE);
        """)
        
        logger.info("Enhanced schema created successfully")
        await conn.close()
        
    except Exception as e:
        logger.error(f"Error creating enhanced schema: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(create_enhanced_schema())