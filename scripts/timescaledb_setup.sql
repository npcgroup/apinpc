-- TimescaleDB Implementation Script
-- This script converts regular PostgreSQL tables to TimescaleDB hypertables
-- and sets up continuous aggregates, compression, and retention policies

-- 1. Convert tables to hypertables
SELECT create_hypertable('funding_rate_data', 'timestamp', 
  chunk_time_interval => INTERVAL '1 day',
  if_not_exists => TRUE
);

SELECT create_hypertable('hyblock_data', 'timestamp', 
  chunk_time_interval => INTERVAL '1 day',
  if_not_exists => TRUE
);

SELECT create_hypertable('liquidity_data', 'timestamp', 
  chunk_time_interval => INTERVAL '1 day',
  if_not_exists => TRUE
);

SELECT create_hypertable('long_short_data', 'timestamp', 
  chunk_time_interval => INTERVAL '1 day',
  if_not_exists => TRUE
);

SELECT create_hypertable('open_interest_data', 'timestamp', 
  chunk_time_interval => INTERVAL '1 day',
  if_not_exists => TRUE
);

SELECT create_hypertable('options_data', 'timestamp', 
  chunk_time_interval => INTERVAL '1 day',
  if_not_exists => TRUE
);

SELECT create_hypertable('orderbook_data', 'timestamp', 
  chunk_time_interval => INTERVAL '1 day',
  if_not_exists => TRUE
);

SELECT create_hypertable('orderflow_data', 'timestamp', 
  chunk_time_interval => INTERVAL '1 day',
  if_not_exists => TRUE
);

SELECT create_hypertable('sentiment_data', 'timestamp', 
  chunk_time_interval => INTERVAL '1 day',
  if_not_exists => TRUE
);

-- 2. Create indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_funding_rate_coin_exchange_time ON funding_rate_data (coin, exchange, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_liquidity_coin_exchange_time ON liquidity_data (coin, exchange, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_long_short_coin_exchange_time ON long_short_data (coin, exchange, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_open_interest_coin_exchange_time ON open_interest_data (coin, exchange, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_options_coin_exchange_time ON options_data (coin, exchange, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_orderbook_coin_exchange_time ON orderbook_data (coin, exchange, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_orderflow_coin_exchange_timeframe_time ON orderflow_data (coin, exchange, timeframe, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_sentiment_coin_time ON sentiment_data (coin, timestamp DESC);

-- 3. Setup continuous aggregates for common time windows

-- Hourly aggregates for orderbook data
CREATE MATERIALIZED VIEW IF NOT EXISTS orderbook_hourly
WITH (timescaledb.continuous) AS
SELECT
  time_bucket('1 hour', timestamp) AS bucket,
  coin,
  exchange,
  AVG((bid_price + ask_price)/2) AS avg_price,
  AVG(bid_ask_ratio) AS avg_bid_ask_ratio,
  AVG(spread) AS avg_spread
FROM orderbook_data
GROUP BY bucket, coin, exchange
WITH NO DATA;

-- Daily aggregates for combined market metrics
CREATE MATERIALIZED VIEW IF NOT EXISTS market_metrics_daily
WITH (timescaledb.continuous) AS
SELECT
  time_bucket('1 day', ob.timestamp) AS bucket,
  ob.coin,
  ob.exchange,
  AVG((ob.bid_price + ob.ask_price)/2) AS avg_price,
  AVG(ob.bid_ask_ratio) AS avg_bid_ask_ratio,
  AVG(fr.funding_rate) AS avg_funding_rate,
  AVG(ls.long_short_ratio) AS avg_long_short_ratio,
  AVG(oi.open_interest_usd) AS avg_open_interest_usd,
  AVG(l.liquidity_score) AS avg_liquidity_score
FROM orderbook_data ob
JOIN funding_rate_data fr ON ob.coin = fr.coin 
  AND ob.exchange = fr.exchange
  AND ob.timestamp::date = fr.timestamp::date
JOIN long_short_data ls ON ob.coin = ls.coin 
  AND ob.exchange = ls.exchange
  AND ob.timestamp::date = ls.timestamp::date
JOIN open_interest_data oi ON ob.coin = oi.coin 
  AND ob.exchange = oi.exchange
  AND ob.timestamp::date = oi.timestamp::date
JOIN liquidity_data l ON ob.coin = l.coin 
  AND ob.exchange = l.exchange
  AND ob.timestamp::date = l.timestamp::date
GROUP BY bucket, ob.coin, ob.exchange
WITH NO DATA;

-- Initial refresh of continuous aggregates
CALL refresh_continuous_aggregate('orderbook_hourly', NULL, NULL);
CALL refresh_continuous_aggregate('market_metrics_daily', NULL, NULL);

-- 4. Enable compression on hypertables
ALTER TABLE funding_rate_data SET (
  timescaledb.compress,
  timescaledb.compress_segmentby = 'coin,exchange'
);

ALTER TABLE liquidity_data SET (
  timescaledb.compress,
  timescaledb.compress_segmentby = 'coin,exchange'
);

ALTER TABLE long_short_data SET (
  timescaledb.compress,
  timescaledb.compress_segmentby = 'coin,exchange'
);

ALTER TABLE open_interest_data SET (
  timescaledb.compress,
  timescaledb.compress_segmentby = 'coin,exchange'
);

ALTER TABLE options_data SET (
  timescaledb.compress,
  timescaledb.compress_segmentby = 'coin,exchange'
);

ALTER TABLE orderbook_data SET (
  timescaledb.compress,
  timescaledb.compress_segmentby = 'coin,exchange'
);

ALTER TABLE orderflow_data SET (
  timescaledb.compress,
  timescaledb.compress_segmentby = 'coin,exchange,timeframe'
);

ALTER TABLE sentiment_data SET (
  timescaledb.compress,
  timescaledb.compress_segmentby = 'coin'
);

-- 5. Add compression policies
SELECT add_compression_policy('funding_rate_data', INTERVAL '7 days');
SELECT add_compression_policy('liquidity_data', INTERVAL '7 days');
SELECT add_compression_policy('long_short_data', INTERVAL '7 days');
SELECT add_compression_policy('open_interest_data', INTERVAL '7 days');
SELECT add_compression_policy('options_data', INTERVAL '7 days');
SELECT add_compression_policy('orderbook_data', INTERVAL '7 days');
SELECT add_compression_policy('orderflow_data', INTERVAL '7 days');
SELECT add_compression_policy('sentiment_data', INTERVAL '7 days');

-- 6. Set up retention policies
SELECT add_retention_policy('funding_rate_data', INTERVAL '12 months');
SELECT add_retention_policy('liquidity_data', INTERVAL '12 months');
SELECT add_retention_policy('long_short_data', INTERVAL '12 months');
SELECT add_retention_policy('open_interest_data', INTERVAL '12 months');
SELECT add_retention_policy('options_data', INTERVAL '12 months');
SELECT add_retention_policy('orderbook_data', INTERVAL '12 months');
SELECT add_retention_policy('orderflow_data', INTERVAL '12 months');
SELECT add_retention_policy('sentiment_data', INTERVAL '12 months');

-- Set longer retention policies for continuous aggregates
SELECT add_retention_policy('orderbook_hourly', INTERVAL '24 months');
SELECT add_retention_policy('market_metrics_daily', INTERVAL '36 months'); 