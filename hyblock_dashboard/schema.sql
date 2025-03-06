-- Schema for Hyblock Data Collection
-- This file defines the tables for storing various crypto metrics

-- Main table for storing all hyblock data
CREATE TABLE IF NOT EXISTS hyblock_data (
    id SERIAL PRIMARY KEY,
    endpoint VARCHAR(100) NOT NULL,
    coin VARCHAR(50) NOT NULL,
    exchange VARCHAR(50),
    timeframe VARCHAR(20),
    market_cap_category VARCHAR(20),
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    data JSONB,
    UNIQUE(endpoint, coin, exchange, timeframe, timestamp)
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS hyblock_data_endpoint_coin_idx ON hyblock_data(endpoint, coin);
CREATE INDEX IF NOT EXISTS hyblock_data_timestamp_idx ON hyblock_data(timestamp);

-- Orderbook Metrics
CREATE TABLE IF NOT EXISTS orderbook_data (
    id SERIAL PRIMARY KEY,
    coin VARCHAR(50) NOT NULL,
    exchange VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
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

-- Options Metrics
CREATE TABLE IF NOT EXISTS options_data (
    id SERIAL PRIMARY KEY,
    coin VARCHAR(50) NOT NULL,
    exchange VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    bvol NUMERIC,
    dvol NUMERIC,
    term_structure JSONB,
    UNIQUE(coin, exchange, timestamp)
);

-- Orderflow Metrics
CREATE TABLE IF NOT EXISTS orderflow_data (
    id SERIAL PRIMARY KEY,
    coin VARCHAR(50) NOT NULL,
    exchange VARCHAR(50) NOT NULL,
    timeframe VARCHAR(20),
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
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

-- Open Interest Metrics
CREATE TABLE IF NOT EXISTS open_interest_data (
    id SERIAL PRIMARY KEY,
    coin VARCHAR(50) NOT NULL,
    exchange VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    open_interest NUMERIC,
    open_interest_delta NUMERIC,
    open_interest_usd NUMERIC,
    anchored_oi_delta JSONB,
    open_interest_profile JSONB,
    UNIQUE(coin, exchange, timestamp)
);

-- Liquidity Metrics
CREATE TABLE IF NOT EXISTS liquidity_data (
    id SERIAL PRIMARY KEY,
    coin VARCHAR(50) NOT NULL,
    exchange VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
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

-- Funding Rate Metrics
CREATE TABLE IF NOT EXISTS funding_rate_data (
    id SERIAL PRIMARY KEY,
    coin VARCHAR(50) NOT NULL,
    exchange VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    funding_rate NUMERIC,
    next_funding_time TIMESTAMP,
    predicted_funding_rate NUMERIC,
    UNIQUE(coin, exchange, timestamp)
);

-- Longs and Shorts Metrics
CREATE TABLE IF NOT EXISTS long_short_data (
    id SERIAL PRIMARY KEY,
    coin VARCHAR(50) NOT NULL,
    exchange VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
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

-- Sentiment Metrics
CREATE TABLE IF NOT EXISTS sentiment_data (
    id SERIAL PRIMARY KEY,
    coin VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    fear_greed_value INTEGER,
    fear_greed_classification VARCHAR(50),
    margin_lending_ratio NUMERIC,
    user_bot_ratio NUMERIC,
    bitmex_leaderboard_notional_profit JSONB,
    bitmex_leaderboard_roe_profit JSONB,
    trollbox_sentiment JSONB,
    stablecoin_premium_p2p NUMERIC,
    wbtc_mint_burn JSONB,
    UNIQUE(coin, timestamp)
);

-- Profile Tool Metrics
CREATE TABLE IF NOT EXISTS profile_data (
    id SERIAL PRIMARY KEY,
    coin VARCHAR(50) NOT NULL,
    exchange VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    open_interest_profile JSONB,
    volume_profile JSONB,
    UNIQUE(coin, exchange, timestamp)
);

-- Market Cap Categories
CREATE TABLE IF NOT EXISTS market_cap_categories (
    id SERIAL PRIMARY KEY,
    coin VARCHAR(50) NOT NULL,
    category VARCHAR(20) NOT NULL,
    market_cap NUMERIC,
    last_updated TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(coin)
);

-- API Usage Tracking
CREATE TABLE IF NOT EXISTS api_usage (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    endpoint VARCHAR(100) NOT NULL,
    remaining_hits INTEGER,
    reset_time TIMESTAMP
); 