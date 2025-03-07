-- Script to convert all tables to TimescaleDB hypertables
-- This script modifies the primary keys and converts the tables

-- Create backup tables
CREATE TABLE IF NOT EXISTS funding_rate_data_backup AS SELECT * FROM funding_rate_data;
CREATE TABLE IF NOT EXISTS hyblock_data_backup AS SELECT * FROM hyblock_data;
CREATE TABLE IF NOT EXISTS liquidity_data_backup AS SELECT * FROM liquidity_data;
CREATE TABLE IF NOT EXISTS long_short_data_backup AS SELECT * FROM long_short_data;
CREATE TABLE IF NOT EXISTS open_interest_data_backup AS SELECT * FROM open_interest_data;
CREATE TABLE IF NOT EXISTS options_data_backup AS SELECT * FROM options_data;
CREATE TABLE IF NOT EXISTS orderflow_data_backup AS SELECT * FROM orderflow_data;
CREATE TABLE IF NOT EXISTS sentiment_data_backup AS SELECT * FROM sentiment_data;

-- Modify funding_rate_data
ALTER TABLE IF EXISTS funding_rate_data DROP CONSTRAINT IF EXISTS funding_rate_data_pkey;
ALTER TABLE IF EXISTS funding_rate_data ADD PRIMARY KEY (id, timestamp);
SELECT create_hypertable('funding_rate_data', 'timestamp', 
  chunk_time_interval => INTERVAL '1 day',
  if_not_exists => TRUE,
  migrate_data => TRUE
);

-- Modify hyblock_data 
ALTER TABLE IF EXISTS hyblock_data DROP CONSTRAINT IF EXISTS hyblock_data_pkey;
ALTER TABLE IF EXISTS hyblock_data ADD PRIMARY KEY (id, timestamp);
SELECT create_hypertable('hyblock_data', 'timestamp', 
  chunk_time_interval => INTERVAL '1 day',
  if_not_exists => TRUE,
  migrate_data => TRUE
);

-- Modify liquidity_data
ALTER TABLE IF EXISTS liquidity_data DROP CONSTRAINT IF EXISTS liquidity_data_pkey;
ALTER TABLE IF EXISTS liquidity_data ADD PRIMARY KEY (id, timestamp);
SELECT create_hypertable('liquidity_data', 'timestamp', 
  chunk_time_interval => INTERVAL '1 day',
  if_not_exists => TRUE,
  migrate_data => TRUE
);

-- Modify long_short_data
ALTER TABLE IF EXISTS long_short_data DROP CONSTRAINT IF EXISTS long_short_data_pkey;
ALTER TABLE IF EXISTS long_short_data ADD PRIMARY KEY (id, timestamp);
SELECT create_hypertable('long_short_data', 'timestamp', 
  chunk_time_interval => INTERVAL '1 day',
  if_not_exists => TRUE,
  migrate_data => TRUE
);

-- Modify open_interest_data
ALTER TABLE IF EXISTS open_interest_data DROP CONSTRAINT IF EXISTS open_interest_data_pkey;
ALTER TABLE IF EXISTS open_interest_data ADD PRIMARY KEY (id, timestamp);
SELECT create_hypertable('open_interest_data', 'timestamp', 
  chunk_time_interval => INTERVAL '1 day',
  if_not_exists => TRUE,
  migrate_data => TRUE
);

-- Modify options_data
ALTER TABLE IF EXISTS options_data DROP CONSTRAINT IF EXISTS options_data_pkey;
ALTER TABLE IF EXISTS options_data ADD PRIMARY KEY (id, timestamp);
SELECT create_hypertable('options_data', 'timestamp', 
  chunk_time_interval => INTERVAL '1 day',
  if_not_exists => TRUE,
  migrate_data => TRUE
);

-- Modify orderflow_data
ALTER TABLE IF EXISTS orderflow_data DROP CONSTRAINT IF EXISTS orderflow_data_pkey;
ALTER TABLE IF EXISTS orderflow_data ADD PRIMARY KEY (id, timestamp);
SELECT create_hypertable('orderflow_data', 'timestamp', 
  chunk_time_interval => INTERVAL '1 day',
  if_not_exists => TRUE,
  migrate_data => TRUE
);

-- Modify sentiment_data
ALTER TABLE IF EXISTS sentiment_data DROP CONSTRAINT IF EXISTS sentiment_data_pkey;
ALTER TABLE IF EXISTS sentiment_data ADD PRIMARY KEY (id, timestamp);
SELECT create_hypertable('sentiment_data', 'timestamp', 
  chunk_time_interval => INTERVAL '1 day',
  if_not_exists => TRUE,
  migrate_data => TRUE
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_funding_rate_coin_exchange_time ON funding_rate_data (coin, exchange, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_liquidity_coin_exchange_time ON liquidity_data (coin, exchange, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_long_short_coin_exchange_time ON long_short_data (coin, exchange, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_open_interest_coin_exchange_time ON open_interest_data (coin, exchange, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_options_coin_exchange_time ON options_data (coin, exchange, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_orderbook_coin_exchange_time ON orderbook_data (coin, exchange, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_orderflow_coin_exchange_timeframe_time ON orderflow_data (coin, exchange, timeframe, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_sentiment_coin_time ON sentiment_data (coin, timestamp DESC); 