#!/bin/bash
# Safe Deployment Script for TimescaleDB Analytics Platform
# This script creates tables in a new schema and migrates data safely

echo "===== TimescaleDB Analytics Platform Safe Deployment ====="
echo "This script will set up TimescaleDB in a separate schema and migrate data safely"

# Step 1: Ensure TimescaleDB extension is installed
echo "Step 1: Ensuring TimescaleDB extension is installed..."
psql -h localhost -d hyblock_data -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"

# Step 2: Run the safe deployment script
echo "Step 2: Creating new schema and tables with proper data types..."
psql -h localhost -d hyblock_data -f scripts/deploy_timescale_safe.sql

# Step 3: Generate updated MCP configuration for the new schema
echo "Step 3: Updating MCP configuration for the new schema..."
cat > scripts/generate_mcp_timescale_config.js << 'EOF'
// Script to generate MCP configuration for timescale schema
const fs = require('fs');
const path = require('path');

const mcpConfig = {
  "mcpServers": {
    "postgres": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-postgres",
        "postgresql://localhost:5432/hyblock_data"
      ]
    },
    "timeseries": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-postgres",
        "postgresql://localhost:5432/hyblock_data"
      ],
      "queryCategories": [
        {
          "name": "Market Pulse",
          "description": "High-level market metrics across time periods",
          "queries": [
            {
              "name": "Unified Market Pulse",
              "description": "Combined view of key metrics for market analysis",
              "sql": "WITH time_series AS (SELECT generate_series(date_trunc('hour', NOW() - interval '{{timeframe}}'), date_trunc('hour', NOW()), interval '1 hour') AS ts), oi_data AS (SELECT date_trunc('hour', timestamp) as hour, coin, SUM(open_interest_usd) as total_oi_usd FROM timescale.open_interest_data WHERE timestamp >= NOW() - interval '{{timeframe}}' AND coin = '{{coin}}' GROUP BY hour, coin), ls_data AS (SELECT date_trunc('hour', timestamp) as hour, coin, AVG(long_short_ratio) as avg_ls_ratio FROM timescale.long_short_data WHERE timestamp >= NOW() - interval '{{timeframe}}' AND coin = '{{coin}}' GROUP BY hour, coin), funding_data AS (SELECT date_trunc('hour', timestamp) as hour, coin, AVG(funding_rate) as avg_funding_rate FROM timescale.funding_rate_data WHERE timestamp >= NOW() - interval '{{timeframe}}' AND coin = '{{coin}}' GROUP BY hour, coin), liquidity_agg AS (SELECT date_trunc('hour', timestamp) as hour, coin, AVG(liquidity_score) as avg_liquidity_score FROM timescale.liquidity_data WHERE timestamp >= NOW() - interval '{{timeframe}}' AND coin = '{{coin}}' GROUP BY hour, coin) SELECT ts.ts as timestamp, '{{coin}}' as coin, oi.total_oi_usd, ls.avg_ls_ratio, f.avg_funding_rate, l.avg_liquidity_score FROM time_series ts LEFT JOIN oi_data oi ON ts.ts = oi.hour AND oi.coin = '{{coin}}' LEFT JOIN ls_data ls ON ts.ts = ls.hour AND ls.coin = '{{coin}}' LEFT JOIN funding_data f ON ts.ts = f.hour AND f.coin = '{{coin}}' LEFT JOIN liquidity_agg l ON ts.ts = l.hour AND l.coin = '{{coin}}' ORDER BY ts.ts",
              "parameters": [
                {
                  "name": "timeframe",
                  "type": "string",
                  "description": "Time period to analyze",
                  "default": "7 days"
                },
                {
                  "name": "coin",
                  "type": "string",
                  "description": "Cryptocurrency to analyze",
                  "default": "BTC"
                }
              ]
            }
          ]
        },
        {
          "name": "Multi-Timeframe Analysis",
          "description": "Compare metrics across various time periods",
          "queries": [
            {
              "name": "Continuous Aggregate Analytics",
              "description": "Using TimescaleDB continuous aggregates for efficient analysis",
              "sql": "WITH daily AS (SELECT bucket::date as day, coin, exchange, avg_price, avg_bid_ask_ratio, avg_spread FROM timescale.orderbook_hourly WHERE bucket >= NOW() - interval '{{timeframe}}' AND coin = '{{coin}}' AND exchange = '{{exchange}}'), hourly_funding AS (SELECT bucket::date as day, coin, exchange, avg_funding_rate FROM timescale.funding_rate_hourly WHERE bucket >= NOW() - interval '{{timeframe}}' AND coin = '{{coin}}' AND exchange = '{{exchange}}'), hourly_ls AS (SELECT bucket::date as day, coin, exchange, avg_ls_ratio, avg_long_positions, avg_short_positions FROM timescale.long_short_hourly WHERE bucket >= NOW() - interval '{{timeframe}}' AND coin = '{{coin}}' AND exchange = '{{exchange}}'), hourly_oi AS (SELECT bucket::date as day, coin, exchange, avg_oi_usd, avg_oi_delta FROM timescale.open_interest_hourly WHERE bucket >= NOW() - interval '{{timeframe}}' AND coin = '{{coin}}' AND exchange = '{{exchange}}'), hourly_liq AS (SELECT bucket::date as day, coin, exchange, avg_liquidity_score, avg_leverage FROM timescale.liquidity_hourly WHERE bucket >= NOW() - interval '{{timeframe}}' AND coin = '{{coin}}' AND exchange = '{{exchange}}') SELECT d.day, d.coin, d.exchange, d.avg_price, d.avg_bid_ask_ratio, d.avg_spread, f.avg_funding_rate, l.avg_ls_ratio, l.avg_long_positions, l.avg_short_positions, o.avg_oi_usd, o.avg_oi_delta, lq.avg_liquidity_score, lq.avg_leverage FROM daily d LEFT JOIN hourly_funding f ON d.day = f.day AND d.coin = f.coin AND d.exchange = f.exchange LEFT JOIN hourly_ls l ON d.day = l.day AND d.coin = l.coin AND d.exchange = l.exchange LEFT JOIN hourly_oi o ON d.day = o.day AND d.coin = o.coin AND d.exchange = o.exchange LEFT JOIN hourly_liq lq ON d.day = lq.day AND d.coin = lq.coin AND d.exchange = lq.exchange ORDER BY d.day DESC",
              "parameters": [
                {
                  "name": "timeframe",
                  "type": "string",
                  "description": "Time period to analyze",
                  "default": "30 days"
                },
                {
                  "name": "coin",
                  "type": "string",
                  "description": "Cryptocurrency to analyze",
                  "default": "BTC"
                },
                {
                  "name": "exchange",
                  "type": "string",
                  "description": "Exchange to analyze",
                  "default": "binance"
                }
              ]
            }
          ]
        },
        {
          "name": "Liquidity Analysis",
          "description": "Multi-dimensional liquidity analysis",
          "queries": [
            {
              "name": "Liquidity Heatmap",
              "description": "Comprehensive view of liquidity across dimensions",
              "sql": "WITH time_periods AS (SELECT generate_series(date_trunc('day', NOW() - interval '{{timeframe}}'), date_trunc('day', NOW()), interval '1 day') AS day), liquidity_metrics AS (SELECT date_trunc('day', l.timestamp) as day, l.coin, l.exchange, AVG(l.liquidity_score) as avg_liquidity_score, AVG(l.average_leverage) as avg_leverage, jsonb_array_elements(l.liquidation_levels)->>'price' as liq_price, (jsonb_array_elements(l.liquidation_levels)->>'longs')::numeric as longs_at_price, (jsonb_array_elements(l.liquidation_levels)->>'shorts')::numeric as shorts_at_price FROM timescale.liquidity_data l WHERE l.timestamp >= NOW() - interval '{{timeframe}}' AND l.coin = '{{coin}}' GROUP BY day, l.coin, l.exchange, liq_price, longs_at_price, shorts_at_price), price_data AS (SELECT date_trunc('day', timestamp) as day, coin, AVG((bid_price + ask_price)/2) as avg_price, MAX((bid_price + ask_price)/2) as high_price, MIN((bid_price + ask_price)/2) as low_price FROM timescale.orderbook_data WHERE timestamp >= NOW() - interval '{{timeframe}}' AND coin = '{{coin}}' GROUP BY day, coin), liq_zones AS (SELECT lm.day, lm.coin, lm.exchange, p.avg_price, p.high_price, p.low_price, SUM(lm.longs_at_price) as total_long_liqs, SUM(lm.shorts_at_price) as total_short_liqs, MAX(CASE WHEN lm.longs_at_price > 1000000 THEN lm.liq_price::numeric ELSE NULL END) as major_long_liq_price, MIN(CASE WHEN lm.shorts_at_price > 1000000 THEN lm.liq_price::numeric ELSE NULL END) as major_short_liq_price, AVG(lm.avg_liquidity_score) as liquidity_score, AVG(lm.avg_leverage) as avg_leverage FROM liquidity_metrics lm JOIN price_data p ON lm.day = p.day AND lm.coin = p.coin GROUP BY lm.day, lm.coin, lm.exchange, p.avg_price, p.high_price, p.low_price) SELECT tp.day as timestamp, COALESCE(lz.coin, '{{coin}}') as coin, lz.exchange, lz.avg_price, lz.liquidity_score, lz.avg_leverage, lz.high_price, lz.low_price, lz.total_long_liqs, lz.total_short_liqs, lz.major_long_liq_price, lz.major_short_liq_price, CASE WHEN lz.avg_price > lz.major_long_liq_price THEN 'Above Major Long Liquidations' WHEN lz.avg_price < lz.major_short_liq_price THEN 'Below Major Short Liquidations' WHEN lz.major_long_liq_price - lz.avg_price < 0.05 * lz.avg_price THEN 'Near Major Long Liquidations' WHEN lz.avg_price - lz.major_short_liq_price < 0.05 * lz.avg_price THEN 'Near Major Short Liquidations' ELSE 'Neutral Zone' END as liquidity_zone_status, CASE WHEN lz.avg_leverage > 10 THEN 'Very High Leverage' WHEN lz.avg_leverage > 5 THEN 'High Leverage' WHEN lz.avg_leverage > 2 THEN 'Moderate Leverage' ELSE 'Low Leverage' END as leverage_status FROM time_periods tp LEFT JOIN liq_zones lz ON tp.day = lz.day ORDER BY tp.day DESC",
              "parameters": [
                {
                  "name": "timeframe",
                  "type": "string",
                  "description": "Time period to analyze",
                  "default": "30 days"
                },
                {
                  "name": "coin",
                  "type": "string",
                  "description": "Cryptocurrency to analyze",
                  "default": "BTC"
                }
              ]
            }
          ]
        },
        {
          "name": "TimescaleDB Features",
          "description": "Queries showcasing TimescaleDB specific features",
          "queries": [
            {
              "name": "Hypertable Chunk Analysis",
              "description": "Information about TimescaleDB hypertable chunks",
              "sql": "SELECT hypertable_schema, hypertable_name, chunk_name, range_start, range_end, is_compressed FROM timescaledb_information.chunks WHERE hypertable_schema = 'timescale' AND hypertable_name = '{{table}}' ORDER BY range_start DESC LIMIT 20",
              "parameters": [
                {
                  "name": "table",
                  "type": "string",
                  "description": "Table name",
                  "default": "orderbook_data"
                }
              ]
            },
            {
              "name": "Compression Stats",
              "description": "Compression statistics for hypertables",
              "sql": "SELECT format('%s.%s', hypertable_schema, hypertable_name) as table_name, pg_size_pretty(total_bytes) as total_size, pg_size_pretty(compressed_total_bytes) as compressed_size, round(compressed_total_bytes::numeric / nullif(total_bytes, 0) * 100, 2) as compression_ratio FROM timescaledb_information.compressed_hypertable_stats WHERE hypertable_schema = 'timescale' ORDER BY compression_ratio",
              "parameters": []
            }
          ]
        }
      ]
    }
  }
};

// Write the configuration to file
const outputDir = path.resolve(__dirname, '../.cursor');
const outputPath = path.join(outputDir, 'mcp.json');

try {
  // Create directory if it doesn't exist
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }
  
  // Write the file
  fs.writeFileSync(outputPath, JSON.stringify(mcpConfig, null, 2));
  console.log(`MCP configuration written to ${outputPath}`);
} catch (error) {
  console.error('Error writing MCP configuration:', error);
}
EOF

# Run the MCP configuration generator
echo "Step 4: Generating MCP configuration..."
node scripts/generate_mcp_timescale_config.js

# Step 5: Create a view for backward compatibility (optional)
echo "Step 5: Creating views for backward compatibility..."
psql -h localhost -d hyblock_data -c "
-- Create views in public schema that point to timescale schema tables
CREATE OR REPLACE VIEW public.orderbook_hourly_view AS SELECT * FROM timescale.orderbook_hourly;
CREATE OR REPLACE VIEW public.funding_rate_hourly_view AS SELECT * FROM timescale.funding_rate_hourly;
CREATE OR REPLACE VIEW public.long_short_hourly_view AS SELECT * FROM timescale.long_short_hourly;
CREATE OR REPLACE VIEW public.open_interest_hourly_view AS SELECT * FROM timescale.open_interest_hourly;
CREATE OR REPLACE VIEW public.liquidity_hourly_view AS SELECT * FROM timescale.liquidity_hourly;
"

echo "===== Safe Deployment Complete ====="
echo "TimescaleDB Analytics Platform is now ready to use in the 'timescale' schema!"
echo "You can access the advanced analytics through the MCP interface."
echo ""
echo "Benefits of this deployment:"
echo "1. Original data remains untouched in the public schema"
echo "2. Proper data types (TEXT instead of VARCHAR, TIMESTAMPTZ instead of TIMESTAMP)"
echo "3. Clean separation of concerns with schema-based organization"
echo "4. Backward compatibility through views" 