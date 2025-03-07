-- Setup TimescaleDB simplified continuous aggregates
-- This script creates materialized views for individual tables

-- Create continuous aggregates for individual tables

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

-- Hourly aggregates for funding rate data 
CREATE MATERIALIZED VIEW IF NOT EXISTS funding_rate_hourly
WITH (timescaledb.continuous) AS
SELECT
  time_bucket('1 hour', timestamp) AS bucket,
  coin,
  exchange,
  AVG(funding_rate) AS avg_funding_rate
FROM funding_rate_data
GROUP BY bucket, coin, exchange
WITH NO DATA;

-- Hourly aggregates for long-short data
CREATE MATERIALIZED VIEW IF NOT EXISTS long_short_hourly
WITH (timescaledb.continuous) AS
SELECT
  time_bucket('1 hour', timestamp) AS bucket,
  coin,
  exchange,
  AVG(long_short_ratio) AS avg_ls_ratio,
  AVG(long_positions) AS avg_long_positions,
  AVG(short_positions) AS avg_short_positions
FROM long_short_data
GROUP BY bucket, coin, exchange
WITH NO DATA;

-- Hourly aggregates for open interest data
CREATE MATERIALIZED VIEW IF NOT EXISTS open_interest_hourly
WITH (timescaledb.continuous) AS
SELECT
  time_bucket('1 hour', timestamp) AS bucket,
  coin,
  exchange,
  AVG(open_interest_usd) AS avg_oi_usd,
  AVG(open_interest_delta) AS avg_oi_delta
FROM open_interest_data
GROUP BY bucket, coin, exchange
WITH NO DATA;

-- Hourly aggregates for liquidity data
CREATE MATERIALIZED VIEW IF NOT EXISTS liquidity_hourly
WITH (timescaledb.continuous) AS
SELECT
  time_bucket('1 hour', timestamp) AS bucket,
  coin,
  exchange,
  AVG(liquidity_score) AS avg_liquidity_score,
  AVG(average_leverage) AS avg_leverage
FROM liquidity_data
GROUP BY bucket, coin, exchange
WITH NO DATA;

-- Initial refresh of continuous aggregates
CALL refresh_continuous_aggregate('orderbook_hourly', NULL, NULL);
CALL refresh_continuous_aggregate('funding_rate_hourly', NULL, NULL);
CALL refresh_continuous_aggregate('long_short_hourly', NULL, NULL);
CALL refresh_continuous_aggregate('open_interest_hourly', NULL, NULL);
CALL refresh_continuous_aggregate('liquidity_hourly', NULL, NULL);

-- Set retention policies for continuous aggregates (keep 24 months)
SELECT add_retention_policy('orderbook_hourly', INTERVAL '24 months');
SELECT add_retention_policy('funding_rate_hourly', INTERVAL '24 months');
SELECT add_retention_policy('long_short_hourly', INTERVAL '24 months');
SELECT add_retention_policy('open_interest_hourly', INTERVAL '24 months');
SELECT add_retention_policy('liquidity_hourly', INTERVAL '24 months'); 