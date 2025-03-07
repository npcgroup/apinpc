-- TimescaleDB Implementation Script (Fixed)
-- This script converts regular PostgreSQL tables to TimescaleDB hypertables
-- and sets up indexes for optimal performance

-- 1. Convert tables to hypertables with migrate_data option
SELECT create_hypertable('funding_rate_data', 'timestamp', 
  chunk_time_interval => INTERVAL '1 day',
  if_not_exists => TRUE,
  migrate_data => TRUE
);

SELECT create_hypertable('hyblock_data', 'timestamp', 
  chunk_time_interval => INTERVAL '1 day',
  if_not_exists => TRUE,
  migrate_data => TRUE
);

SELECT create_hypertable('liquidity_data', 'timestamp', 
  chunk_time_interval => INTERVAL '1 day',
  if_not_exists => TRUE,
  migrate_data => TRUE
);

SELECT create_hypertable('long_short_data', 'timestamp', 
  chunk_time_interval => INTERVAL '1 day',
  if_not_exists => TRUE,
  migrate_data => TRUE
);

SELECT create_hypertable('open_interest_data', 'timestamp', 
  chunk_time_interval => INTERVAL '1 day',
  if_not_exists => TRUE,
  migrate_data => TRUE
);

SELECT create_hypertable('options_data', 'timestamp', 
  chunk_time_interval => INTERVAL '1 day',
  if_not_exists => TRUE,
  migrate_data => TRUE
);

SELECT create_hypertable('orderbook_data', 'timestamp', 
  chunk_time_interval => INTERVAL '1 day',
  if_not_exists => TRUE,
  migrate_data => TRUE
);

SELECT create_hypertable('orderflow_data', 'timestamp', 
  chunk_time_interval => INTERVAL '1 day',
  if_not_exists => TRUE,
  migrate_data => TRUE
);

SELECT create_hypertable('sentiment_data', 'timestamp', 
  chunk_time_interval => INTERVAL '1 day',
  if_not_exists => TRUE,
  migrate_data => TRUE
);

-- 2. Create indexes for common query patterns
-- Note: These indexes will only be created if the hypertables were successfully created
CREATE INDEX IF NOT EXISTS idx_funding_rate_coin_exchange_time ON funding_rate_data (coin, exchange, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_liquidity_coin_exchange_time ON liquidity_data (coin, exchange, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_long_short_coin_exchange_time ON long_short_data (coin, exchange, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_open_interest_coin_exchange_time ON open_interest_data (coin, exchange, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_options_coin_exchange_time ON options_data (coin, exchange, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_orderbook_coin_exchange_time ON orderbook_data (coin, exchange, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_orderflow_coin_exchange_timeframe_time ON orderflow_data (coin, exchange, timeframe, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_sentiment_coin_time ON sentiment_data (coin, timestamp DESC); 