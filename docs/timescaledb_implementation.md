# TimescaleDB Implementation for Crypto Market Data

This document outlines the implementation plan for converting our existing PostgreSQL tables to TimescaleDB hypertables for optimized timeseries data processing.

## Overview

TimescaleDB extends PostgreSQL with specialized time-series capabilities while maintaining full SQL compatibility. The implementation will:

1. Improve query performance for time-based analytics
2. Enable efficient data retention policies
3. Support automated data aggregation through continuous aggregates
4. Optimize storage through data compression

## Implementation Steps

### 1. Install TimescaleDB Extension

```sql
CREATE EXTENSION IF NOT EXISTS timescaledb;
```

### 2. Convert Existing Tables to Hypertables

For each of our timeseries tables, we'll convert them to hypertables using the `create_hypertable` function:

```sql
-- For funding_rate_data
SELECT create_hypertable('funding_rate_data', 'timestamp', 
  chunk_time_interval => INTERVAL '1 day',
  if_not_exists => TRUE
);

-- For hyblock_data
SELECT create_hypertable('hyblock_data', 'timestamp', 
  chunk_time_interval => INTERVAL '1 day',
  if_not_exists => TRUE
);

-- For liquidity_data
SELECT create_hypertable('liquidity_data', 'timestamp', 
  chunk_time_interval => INTERVAL '1 day',
  if_not_exists => TRUE
);

-- For long_short_data
SELECT create_hypertable('long_short_data', 'timestamp', 
  chunk_time_interval => INTERVAL '1 day',
  if_not_exists => TRUE
);

-- For open_interest_data
SELECT create_hypertable('open_interest_data', 'timestamp', 
  chunk_time_interval => INTERVAL '1 day',
  if_not_exists => TRUE
);

-- For options_data
SELECT create_hypertable('options_data', 'timestamp', 
  chunk_time_interval => INTERVAL '1 day',
  if_not_exists => TRUE
);

-- For orderbook_data
SELECT create_hypertable('orderbook_data', 'timestamp', 
  chunk_time_interval => INTERVAL '1 day',
  if_not_exists => TRUE
);

-- For orderflow_data
SELECT create_hypertable('orderflow_data', 'timestamp', 
  chunk_time_interval => INTERVAL '1 day',
  if_not_exists => TRUE
);

-- For sentiment_data
SELECT create_hypertable('sentiment_data', 'timestamp', 
  chunk_time_interval => INTERVAL '1 day',
  if_not_exists => TRUE
);
```

### 3. Create Indexes for Common Query Patterns

```sql
-- Add indexes for common query dimensions
CREATE INDEX ON funding_rate_data (coin, exchange, timestamp DESC);
CREATE INDEX ON liquidity_data (coin, exchange, timestamp DESC);
CREATE INDEX ON long_short_data (coin, exchange, timestamp DESC);
CREATE INDEX ON open_interest_data (coin, exchange, timestamp DESC);
CREATE INDEX ON options_data (coin, exchange, timestamp DESC);
CREATE INDEX ON orderbook_data (coin, exchange, timestamp DESC);
CREATE INDEX ON orderflow_data (coin, exchange, timeframe, timestamp DESC);
CREATE INDEX ON sentiment_data (coin, timestamp DESC);
```

### 4. Setup Continuous Aggregates for Common Time Windows

```sql
-- Hourly aggregates for orderbook data
CREATE MATERIALIZED VIEW orderbook_hourly
WITH (timescaledb.continuous) AS
SELECT
  time_bucket('1 hour', timestamp) AS bucket,
  coin,
  exchange,
  AVG((bid_price + ask_price)/2) AS avg_price,
  AVG(bid_ask_ratio) AS avg_bid_ask_ratio,
  AVG(spread) AS avg_spread
FROM orderbook_data
GROUP BY bucket, coin, exchange;

-- Daily aggregates for combined market metrics
CREATE MATERIALIZED VIEW market_metrics_daily
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
GROUP BY bucket, ob.coin, ob.exchange;
```

### 5. Set Up Retention Policies

```sql
-- Set retention policy to keep only the most recent 12 months of raw data
SELECT add_retention_policy('funding_rate_data', INTERVAL '12 months');
SELECT add_retention_policy('liquidity_data', INTERVAL '12 months');
SELECT add_retention_policy('long_short_data', INTERVAL '12 months');
SELECT add_retention_policy('open_interest_data', INTERVAL '12 months');
SELECT add_retention_policy('options_data', INTERVAL '12 months');
SELECT add_retention_policy('orderbook_data', INTERVAL '12 months');
SELECT add_retention_policy('orderflow_data', INTERVAL '12 months');
SELECT add_retention_policy('sentiment_data', INTERVAL '12 months');

-- Keep continuous aggregates for longer periods
SELECT add_retention_policy('orderbook_hourly', INTERVAL '24 months');
SELECT add_retention_policy('market_metrics_daily', INTERVAL '36 months');
```

### 6. Enable Compression

```sql
-- Enable compression for all hypertables with a default compression policy
ALTER TABLE funding_rate_data SET (
  timescaledb.compress,
  timescaledb.compress_segmentby = 'coin,exchange'
);
SELECT add_compression_policy('funding_rate_data', INTERVAL '7 days');

-- Repeat for all other hypertables with appropriate segmentby columns
```

## Expected Performance Benefits

- 10-100x faster queries for time-based analytics
- Reduced storage requirements through compression (typically 94-97% for timeseries data)
- More efficient data management with automated retention policies
- Better scalability for growing datasets

## Monitoring and Maintenance

After implementation, monitor the following:
- Chunk size and distribution
- Compression ratios
- Query performance
- Continuous aggregate refresh performance

Adjust chunk_time_interval and other parameters as needed based on monitoring results. 