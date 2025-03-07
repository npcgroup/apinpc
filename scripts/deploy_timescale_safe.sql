-- Safe TimescaleDB Deployment Script
-- This script creates tables in a new schema and migrates data safely

-- 1. Create a new schema for TimescaleDB tables
CREATE SCHEMA IF NOT EXISTS timescale;

-- 2. Create TimescaleDB extension if not exists
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- 3. Create new tables in the timescale schema with proper column types
-- Funding Rate Data
CREATE TABLE IF NOT EXISTS timescale.funding_rate_data (
    id SERIAL PRIMARY KEY,
    coin TEXT NOT NULL,
    exchange TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    funding_rate NUMERIC,
    next_funding_time TIMESTAMPTZ,
    predicted_funding_rate NUMERIC,
    UNIQUE(coin, exchange, timestamp)
);

-- Hyblock Data
CREATE TABLE IF NOT EXISTS timescale.hyblock_data (
    id SERIAL PRIMARY KEY,
    endpoint TEXT,
    coin TEXT NOT NULL,
    exchange TEXT NOT NULL,
    timeframe TEXT,
    market_cap_category TEXT,
    timestamp TIMESTAMPTZ NOT NULL,
    data JSONB,
    UNIQUE(coin, exchange, timestamp)
);

-- Liquidity Data
CREATE TABLE IF NOT EXISTS timescale.liquidity_data (
    id SERIAL PRIMARY KEY,
    coin TEXT NOT NULL,
    exchange TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    liquidation_levels JSONB,
    average_leverage NUMERIC,
    average_leverage_delta NUMERIC,
    liquidity_score NUMERIC,
    cumulative_liq_level JSONB,
    liquidation_heatmap JSONB,
    anchored_llc JSONB,
    anchored_lls JSONB,
    anchored_cllcd JSONB,
    anchored_clls JSONB,
    UNIQUE(coin, exchange, timestamp)
);

-- Long Short Data
CREATE TABLE IF NOT EXISTS timescale.long_short_data (
    id SERIAL PRIMARY KEY,
    coin TEXT NOT NULL,
    exchange TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    long_positions NUMERIC,
    short_positions NUMERIC,
    net_long_short NUMERIC,
    net_long_short_delta NUMERIC,
    long_short_ratio NUMERIC,
    binance_global_accounts JSONB,
    binance_top_trader_accounts JSONB,
    binance_top_trader_positions JSONB,
    binance_true_retail_long_short JSONB,
    binance_whale_retail_delta JSONB,
    trader_sentiment_gap NUMERIC,
    whale_position_dominance NUMERIC,
    bybit_global_accounts JSONB,
    okx_global_accounts JSONB,
    okx_top_trader_accounts JSONB,
    okx_whale_retail_delta JSONB,
    anchored_cls JSONB,
    anchored_clsd JSONB,
    UNIQUE(coin, exchange, timestamp)
);

-- Open Interest Data
CREATE TABLE IF NOT EXISTS timescale.open_interest_data (
    id SERIAL PRIMARY KEY,
    coin TEXT NOT NULL,
    exchange TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    open_interest NUMERIC,
    open_interest_delta NUMERIC,
    open_interest_usd NUMERIC,
    anchored_oi_delta JSONB,
    open_interest_profile JSONB,
    UNIQUE(coin, exchange, timestamp)
);

-- Options Data
CREATE TABLE IF NOT EXISTS timescale.options_data (
    id SERIAL PRIMARY KEY,
    coin TEXT NOT NULL,
    exchange TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    bvol NUMERIC,
    dvol NUMERIC,
    term_structure JSONB,
    UNIQUE(coin, exchange, timestamp)
);

-- Orderbook Data
CREATE TABLE IF NOT EXISTS timescale.orderbook_data (
    id SERIAL PRIMARY KEY,
    coin TEXT NOT NULL,
    exchange TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    bid_price NUMERIC,
    ask_price NUMERIC,
    bid_size NUMERIC,
    ask_size NUMERIC,
    bid_ask_ratio NUMERIC,
    bid_ask_delta NUMERIC,
    spread NUMERIC,
    bids_increase_decrease JSONB,
    asks_increase_decrease JSONB,
    combined_book JSONB,
    UNIQUE(coin, exchange, timestamp)
);

-- Orderflow Data
CREATE TABLE IF NOT EXISTS timescale.orderflow_data (
    id SERIAL PRIMARY KEY,
    coin TEXT NOT NULL,
    exchange TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    buy_volume NUMERIC,
    sell_volume NUMERIC,
    volume_delta NUMERIC,
    market_order_count INTEGER,
    limit_order_count INTEGER,
    market_order_avg_size NUMERIC,
    limit_order_avg_size NUMERIC,
    anchored_cvd JSONB,
    pd_levels JSONB,
    pw_levels JSONB,
    pm_levels JSONB,
    slippage NUMERIC,
    transfer_of_contracts JSONB,
    participation_ratio NUMERIC,
    UNIQUE(coin, exchange, timeframe, timestamp)
);

-- Sentiment Data
CREATE TABLE IF NOT EXISTS timescale.sentiment_data (
    id SERIAL PRIMARY KEY,
    coin TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    fear_greed_value INTEGER,
    fear_greed_classification TEXT,
    margin_lending_ratio NUMERIC,
    user_bot_ratio NUMERIC,
    bitmex_leaderboard_notional_profit JSONB,
    bitmex_leaderboard_roe_profit JSONB,
    trollbox_sentiment JSONB,
    stablecoin_premium_p2p NUMERIC,
    wbtc_mint_burn JSONB,
    UNIQUE(coin, timestamp)
);

-- 4. Convert tables to hypertables
SELECT create_hypertable('timescale.funding_rate_data', 'timestamp', 
  chunk_time_interval => INTERVAL '1 day',
  if_not_exists => TRUE
);

SELECT create_hypertable('timescale.hyblock_data', 'timestamp', 
  chunk_time_interval => INTERVAL '1 day',
  if_not_exists => TRUE
);

SELECT create_hypertable('timescale.liquidity_data', 'timestamp', 
  chunk_time_interval => INTERVAL '1 day',
  if_not_exists => TRUE
);

SELECT create_hypertable('timescale.long_short_data', 'timestamp', 
  chunk_time_interval => INTERVAL '1 day',
  if_not_exists => TRUE
);

SELECT create_hypertable('timescale.open_interest_data', 'timestamp', 
  chunk_time_interval => INTERVAL '1 day',
  if_not_exists => TRUE
);

SELECT create_hypertable('timescale.options_data', 'timestamp', 
  chunk_time_interval => INTERVAL '1 day',
  if_not_exists => TRUE
);

SELECT create_hypertable('timescale.orderbook_data', 'timestamp', 
  chunk_time_interval => INTERVAL '1 day',
  if_not_exists => TRUE
);

SELECT create_hypertable('timescale.orderflow_data', 'timestamp', 
  chunk_time_interval => INTERVAL '1 day',
  if_not_exists => TRUE
);

SELECT create_hypertable('timescale.sentiment_data', 'timestamp', 
  chunk_time_interval => INTERVAL '1 day',
  if_not_exists => TRUE
);

-- 5. Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_ts_funding_rate_coin_exchange_time ON timescale.funding_rate_data (coin, exchange, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_ts_liquidity_coin_exchange_time ON timescale.liquidity_data (coin, exchange, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_ts_long_short_coin_exchange_time ON timescale.long_short_data (coin, exchange, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_ts_open_interest_coin_exchange_time ON timescale.open_interest_data (coin, exchange, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_ts_options_coin_exchange_time ON timescale.options_data (coin, exchange, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_ts_orderbook_coin_exchange_time ON timescale.orderbook_data (coin, exchange, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_ts_orderflow_coin_exchange_timeframe_time ON timescale.orderflow_data (coin, exchange, timeframe, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_ts_sentiment_coin_time ON timescale.sentiment_data (coin, timestamp DESC);

-- 6. Migrate data from public schema to timescale schema
-- Funding Rate Data
INSERT INTO timescale.funding_rate_data (id, coin, exchange, timestamp, funding_rate, next_funding_time, predicted_funding_rate)
SELECT id, coin, exchange, timestamp, funding_rate, next_funding_time, predicted_funding_rate
FROM public.funding_rate_data
ON CONFLICT (coin, exchange, timestamp) DO NOTHING;

-- Hyblock Data
INSERT INTO timescale.hyblock_data (id, endpoint, coin, exchange, timeframe, market_cap_category, timestamp, data)
SELECT id, endpoint, coin, exchange, timeframe, market_cap_category, timestamp, data
FROM public.hyblock_data
ON CONFLICT (coin, exchange, timestamp) DO NOTHING;

-- Liquidity Data
INSERT INTO timescale.liquidity_data (id, coin, exchange, timestamp, liquidation_levels, average_leverage, average_leverage_delta, 
                                     liquidity_score, cumulative_liq_level, liquidation_heatmap, anchored_llc, anchored_lls, 
                                     anchored_cllcd, anchored_clls)
SELECT id, coin, exchange, timestamp, liquidation_levels, average_leverage, average_leverage_delta, 
       liquidity_score, cumulative_liq_level, liquidation_heatmap, anchored_llc, anchored_lls, 
       anchored_cllcd, anchored_clls
FROM public.liquidity_data
ON CONFLICT (coin, exchange, timestamp) DO NOTHING;

-- Long Short Data
INSERT INTO timescale.long_short_data (id, coin, exchange, timestamp, long_positions, short_positions, net_long_short, 
                                      net_long_short_delta, long_short_ratio, binance_global_accounts, binance_top_trader_accounts, 
                                      binance_top_trader_positions, binance_true_retail_long_short, binance_whale_retail_delta, 
                                      trader_sentiment_gap, whale_position_dominance, bybit_global_accounts, okx_global_accounts, 
                                      okx_top_trader_accounts, okx_whale_retail_delta, anchored_cls, anchored_clsd)
SELECT id, coin, exchange, timestamp, long_positions, short_positions, net_long_short, 
       net_long_short_delta, long_short_ratio, binance_global_accounts, binance_top_trader_accounts, 
       binance_top_trader_positions, binance_true_retail_long_short, binance_whale_retail_delta, 
       trader_sentiment_gap, whale_position_dominance, bybit_global_accounts, okx_global_accounts, 
       okx_top_trader_accounts, okx_whale_retail_delta, anchored_cls, anchored_clsd
FROM public.long_short_data
ON CONFLICT (coin, exchange, timestamp) DO NOTHING;

-- Open Interest Data
INSERT INTO timescale.open_interest_data (id, coin, exchange, timestamp, open_interest, open_interest_delta, 
                                         open_interest_usd, anchored_oi_delta, open_interest_profile)
SELECT id, coin, exchange, timestamp, open_interest, open_interest_delta, 
       open_interest_usd, anchored_oi_delta, open_interest_profile
FROM public.open_interest_data
ON CONFLICT (coin, exchange, timestamp) DO NOTHING;

-- Options Data
INSERT INTO timescale.options_data (id, coin, exchange, timestamp, bvol, dvol, term_structure)
SELECT id, coin, exchange, timestamp, bvol, dvol, term_structure
FROM public.options_data
ON CONFLICT (coin, exchange, timestamp) DO NOTHING;

-- Orderbook Data
INSERT INTO timescale.orderbook_data (id, coin, exchange, timestamp, bid_price, ask_price, bid_size, ask_size, 
                                     bid_ask_ratio, bid_ask_delta, spread, bids_increase_decrease, 
                                     asks_increase_decrease, combined_book)
SELECT id, coin, exchange, timestamp, bid_price, ask_price, bid_size, ask_size, 
       bid_ask_ratio, bid_ask_delta, spread, bids_increase_decrease, 
       asks_increase_decrease, combined_book
FROM public.orderbook_data
ON CONFLICT (coin, exchange, timestamp) DO NOTHING;

-- Orderflow Data
INSERT INTO timescale.orderflow_data (id, coin, exchange, timeframe, timestamp, buy_volume, sell_volume, volume_delta, 
                                     market_order_count, limit_order_count, market_order_avg_size, limit_order_avg_size, 
                                     anchored_cvd, pd_levels, pw_levels, pm_levels, slippage, transfer_of_contracts, 
                                     participation_ratio)
SELECT id, coin, exchange, timeframe, timestamp, buy_volume, sell_volume, volume_delta, 
       market_order_count, limit_order_count, market_order_avg_size, limit_order_avg_size, 
       anchored_cvd, pd_levels, pw_levels, pm_levels, slippage, transfer_of_contracts, 
       participation_ratio
FROM public.orderflow_data
ON CONFLICT (coin, exchange, timeframe, timestamp) DO NOTHING;

-- Sentiment Data
INSERT INTO timescale.sentiment_data (id, coin, timestamp, fear_greed_value, fear_greed_classification, margin_lending_ratio, 
                                     user_bot_ratio, bitmex_leaderboard_notional_profit, bitmex_leaderboard_roe_profit, 
                                     trollbox_sentiment, stablecoin_premium_p2p, wbtc_mint_burn)
SELECT id, coin, timestamp, fear_greed_value, fear_greed_classification, margin_lending_ratio, 
       user_bot_ratio, bitmex_leaderboard_notional_profit, bitmex_leaderboard_roe_profit, 
       trollbox_sentiment, stablecoin_premium_p2p, wbtc_mint_burn
FROM public.sentiment_data
ON CONFLICT (coin, timestamp) DO NOTHING;

-- 7. Set up compression policies
ALTER TABLE timescale.funding_rate_data SET (
  timescaledb.compress,
  timescaledb.compress_segmentby = 'coin,exchange'
);

ALTER TABLE timescale.liquidity_data SET (
  timescaledb.compress,
  timescaledb.compress_segmentby = 'coin,exchange'
);

ALTER TABLE timescale.long_short_data SET (
  timescaledb.compress,
  timescaledb.compress_segmentby = 'coin,exchange'
);

ALTER TABLE timescale.open_interest_data SET (
  timescaledb.compress,
  timescaledb.compress_segmentby = 'coin,exchange'
);

ALTER TABLE timescale.options_data SET (
  timescaledb.compress,
  timescaledb.compress_segmentby = 'coin,exchange'
);

ALTER TABLE timescale.orderbook_data SET (
  timescaledb.compress,
  timescaledb.compress_segmentby = 'coin,exchange'
);

ALTER TABLE timescale.orderflow_data SET (
  timescaledb.compress,
  timescaledb.compress_segmentby = 'coin,exchange,timeframe'
);

ALTER TABLE timescale.sentiment_data SET (
  timescaledb.compress,
  timescaledb.compress_segmentby = 'coin'
);

-- 8. Add compression policies (compress chunks older than 7 days)
SELECT add_compression_policy('timescale.funding_rate_data', INTERVAL '7 days');
SELECT add_compression_policy('timescale.liquidity_data', INTERVAL '7 days');
SELECT add_compression_policy('timescale.long_short_data', INTERVAL '7 days');
SELECT add_compression_policy('timescale.open_interest_data', INTERVAL '7 days');
SELECT add_compression_policy('timescale.options_data', INTERVAL '7 days');
SELECT add_compression_policy('timescale.orderbook_data', INTERVAL '7 days');
SELECT add_compression_policy('timescale.orderflow_data', INTERVAL '7 days');
SELECT add_compression_policy('timescale.sentiment_data', INTERVAL '7 days');

-- 9. Set up continuous aggregates in the timescale schema
-- Hourly aggregates for orderbook data
CREATE MATERIALIZED VIEW timescale.orderbook_hourly
WITH (timescaledb.continuous) AS
SELECT
  time_bucket('1 hour', timestamp) AS bucket,
  coin,
  exchange,
  AVG((bid_price + ask_price)/2) AS avg_price,
  AVG(bid_ask_ratio) AS avg_bid_ask_ratio,
  AVG(spread) AS avg_spread
FROM timescale.orderbook_data
GROUP BY bucket, coin, exchange
WITH NO DATA;

-- Hourly aggregates for funding rate data 
CREATE MATERIALIZED VIEW timescale.funding_rate_hourly
WITH (timescaledb.continuous) AS
SELECT
  time_bucket('1 hour', timestamp) AS bucket,
  coin,
  exchange,
  AVG(funding_rate) AS avg_funding_rate
FROM timescale.funding_rate_data
GROUP BY bucket, coin, exchange
WITH NO DATA;

-- Hourly aggregates for long-short data
CREATE MATERIALIZED VIEW timescale.long_short_hourly
WITH (timescaledb.continuous) AS
SELECT
  time_bucket('1 hour', timestamp) AS bucket,
  coin,
  exchange,
  AVG(long_short_ratio) AS avg_ls_ratio,
  AVG(long_positions) AS avg_long_positions,
  AVG(short_positions) AS avg_short_positions
FROM timescale.long_short_data
GROUP BY bucket, coin, exchange
WITH NO DATA;

-- Hourly aggregates for open interest data
CREATE MATERIALIZED VIEW timescale.open_interest_hourly
WITH (timescaledb.continuous) AS
SELECT
  time_bucket('1 hour', timestamp) AS bucket,
  coin,
  exchange,
  AVG(open_interest_usd) AS avg_oi_usd,
  AVG(open_interest_delta) AS avg_oi_delta
FROM timescale.open_interest_data
GROUP BY bucket, coin, exchange
WITH NO DATA;

-- Hourly aggregates for liquidity data
CREATE MATERIALIZED VIEW timescale.liquidity_hourly
WITH (timescaledb.continuous) AS
SELECT
  time_bucket('1 hour', timestamp) AS bucket,
  coin,
  exchange,
  AVG(liquidity_score) AS avg_liquidity_score,
  AVG(average_leverage) AS avg_leverage
FROM timescale.liquidity_data
GROUP BY bucket, coin, exchange
WITH NO DATA;

-- 10. Initial refresh of continuous aggregates
CALL refresh_continuous_aggregate('timescale.orderbook_hourly', NULL, NULL);
CALL refresh_continuous_aggregate('timescale.funding_rate_hourly', NULL, NULL);
CALL refresh_continuous_aggregate('timescale.long_short_hourly', NULL, NULL);
CALL refresh_continuous_aggregate('timescale.open_interest_hourly', NULL, NULL);
CALL refresh_continuous_aggregate('timescale.liquidity_hourly', NULL, NULL);

-- 11. Set retention policies for continuous aggregates (keep 24 months)
SELECT add_retention_policy('timescale.orderbook_hourly', INTERVAL '24 months');
SELECT add_retention_policy('timescale.funding_rate_hourly', INTERVAL '24 months');
SELECT add_retention_policy('timescale.long_short_hourly', INTERVAL '24 months');
SELECT add_retention_policy('timescale.open_interest_hourly', INTERVAL '24 months');
SELECT add_retention_policy('timescale.liquidity_hourly', INTERVAL '24 months'); 