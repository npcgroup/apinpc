-- Create enum types for different data sources and metric types
CREATE TYPE data_source_type AS ENUM ('dexscreener', 'defillama', 'hypurrscan', 'flipside');
CREATE TYPE metric_type AS ENUM ('token', 'protocol', 'chain', 'holder', 'nft');

-- Create base metrics table
CREATE TABLE IF NOT EXISTS metrics (
    id BIGSERIAL PRIMARY KEY,
    source data_source_type NOT NULL,
    type metric_type NOT NULL,
    name TEXT NOT NULL,
    symbol TEXT,
    chain TEXT,
    value DECIMAL,
    protocol_name TEXT,
    description TEXT,
    metadata JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create token metrics table
CREATE TABLE IF NOT EXISTS token_metrics (
    id BIGSERIAL PRIMARY KEY,
    source data_source_type NOT NULL,
    token_address TEXT,
    symbol TEXT NOT NULL,
    name TEXT,
    protocol_name TEXT,
    price DECIMAL,
    price_change_24h DECIMAL,
    volume_24h DECIMAL,
    market_cap DECIMAL,
    total_supply DECIMAL,
    holders_count INTEGER,
    transactions_24h INTEGER,
    metadata JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(source, symbol, timestamp)
);

-- Create protocol metrics table
CREATE TABLE IF NOT EXISTS protocol_metrics (
    id BIGSERIAL PRIMARY KEY,
    source data_source_type NOT NULL,
    protocol_name TEXT NOT NULL,
    protocol_type TEXT,
    chain TEXT NOT NULL,
    tvl DECIMAL,
    volume_24h DECIMAL,
    fees_24h DECIMAL,
    revenue_24h DECIMAL,
    unique_users_24h INTEGER,
    transactions_24h INTEGER,
    metadata JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(source, protocol_name, chain, timestamp)
);

-- Create holder metrics table
CREATE TABLE IF NOT EXISTS holder_metrics (
    id BIGSERIAL PRIMARY KEY,
    source data_source_type NOT NULL,
    token_symbol TEXT NOT NULL,
    protocol_name TEXT,
    holder_address TEXT NOT NULL,
    balance DECIMAL NOT NULL,
    rank INTEGER,
    percentage DECIMAL,
    value_usd DECIMAL,
    metadata JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(source, token_symbol, holder_address, timestamp)
);

-- Create chain metrics table
CREATE TABLE IF NOT EXISTS chain_metrics (
    id BIGSERIAL PRIMARY KEY,
    source data_source_type NOT NULL,
    chain TEXT NOT NULL,
    block_height BIGINT,
    tx_count INTEGER,
    active_addresses INTEGER,
    total_fees DECIMAL,
    avg_gas_price DECIMAL,
    tvl DECIMAL,
    metadata JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(source, chain, timestamp)
);

-- DexScreener Tables
CREATE TABLE IF NOT EXISTS dexscreener_pairs (
    id BIGSERIAL PRIMARY KEY,
    pair_address TEXT NOT NULL,
    chain_id TEXT NOT NULL,
    dex_id TEXT,
    token_1_symbol TEXT,
    token_1_address TEXT,
    token_2_symbol TEXT,
    token_2_address TEXT,
    price_usd DECIMAL,
    liquidity_usd DECIMAL,
    volume_24h DECIMAL,
    price_change_24h DECIMAL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(pair_address, chain_id, created_at)
);

-- DefiLlama Tables
CREATE TABLE IF NOT EXISTS defillama_protocols (
    id BIGSERIAL PRIMARY KEY,
    protocol_id TEXT NOT NULL,
    name TEXT NOT NULL,
    chain TEXT[],
    tvl DECIMAL,
    tvl_change_24h DECIMAL,
    volume_24h DECIMAL,
    fees_24h DECIMAL,
    mcap_tvl DECIMAL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(protocol_id, created_at)
);

CREATE TABLE IF NOT EXISTS defillama_chains (
    id BIGSERIAL PRIMARY KEY,
    chain_name TEXT NOT NULL,
    tvl DECIMAL,
    tvl_change_24h DECIMAL,
    protocols_count INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(chain_name, created_at)
);

-- Hypurrscan Tables
CREATE TABLE IF NOT EXISTS hypurrscan_holders (
    id BIGSERIAL PRIMARY KEY,
    token TEXT NOT NULL,
    holder_address TEXT NOT NULL,
    balance DECIMAL,
    rank INTEGER,
    timestamp TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(token, holder_address, timestamp)
);

CREATE TABLE IF NOT EXISTS hypurrscan_token_details (
    id BIGSERIAL PRIMARY KEY,
    token TEXT NOT NULL,
    total_supply DECIMAL,
    holders_count INTEGER,
    transfers_count INTEGER,
    last_transfer_timestamp TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(token, created_at)
);

CREATE TABLE IF NOT EXISTS hypurrscan_twap (
    id BIGSERIAL PRIMARY KEY,
    token TEXT NOT NULL,
    price DECIMAL,
    volume DECIMAL,
    timestamp TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(token, timestamp)
);

-- Flipside Tables
CREATE TABLE IF NOT EXISTS flipside_nft_metrics (
    id BIGSERIAL PRIMARY KEY,
    project_name TEXT NOT NULL,
    chain TEXT NOT NULL,
    sales_count INTEGER,
    unique_buyers INTEGER,
    volume_usd DECIMAL,
    avg_price_usd DECIMAL,
    timestamp TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(project_name, chain, timestamp)
);

CREATE TABLE IF NOT EXISTS flipside_chain_metrics (
    id BIGSERIAL PRIMARY KEY,
    chain TEXT NOT NULL,
    block_timestamp TIMESTAMP WITH TIME ZONE,
    tx_count INTEGER,
    active_users INTEGER,
    eth_volume DECIMAL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(chain, block_timestamp)
);

-- Drop existing indexes if they exist
DROP INDEX IF EXISTS idx_metrics_source_type;
DROP INDEX IF EXISTS idx_metrics_timestamp;
DROP INDEX IF EXISTS idx_token_metrics_symbol;
DROP INDEX IF EXISTS idx_token_metrics_timestamp;
DROP INDEX IF EXISTS idx_protocol_metrics_name;
DROP INDEX IF EXISTS idx_holder_metrics_token;
DROP INDEX IF EXISTS idx_chain_metrics_chain;
DROP INDEX IF EXISTS idx_dexscreener_pairs_tokens;
DROP INDEX IF EXISTS idx_defillama_protocols_name;
DROP INDEX IF EXISTS idx_hypurrscan_holders_token;
DROP INDEX IF EXISTS idx_flipside_nft_project;

-- Create indexes for better query performance
CREATE INDEX idx_metrics_source_type ON metrics(source, type);
CREATE INDEX idx_metrics_timestamp ON metrics(timestamp);
CREATE INDEX idx_metrics_protocol_name ON metrics(protocol_name);
CREATE INDEX idx_token_metrics_symbol ON token_metrics(symbol);
CREATE INDEX idx_token_metrics_timestamp ON token_metrics(timestamp);
CREATE INDEX idx_token_metrics_protocol ON token_metrics(protocol_name);
CREATE INDEX idx_protocol_metrics_name ON protocol_metrics(protocol_name);
CREATE INDEX idx_holder_metrics_token ON holder_metrics(token_symbol);
CREATE INDEX idx_chain_metrics_chain ON chain_metrics(chain);
CREATE INDEX idx_dexscreener_pairs_tokens ON dexscreener_pairs(token_1_address, token_2_address);
CREATE INDEX idx_defillama_protocols_name ON defillama_protocols(name);
CREATE INDEX idx_hypurrscan_holders_token ON hypurrscan_holders(token);
CREATE INDEX idx_flipside_nft_project ON flipside_nft_metrics(project_name);

-- Drop existing views if they exist
DROP VIEW IF EXISTS latest_token_metrics;
DROP VIEW IF EXISTS latest_protocol_metrics;
DROP VIEW IF EXISTS latest_chain_metrics;
DROP MATERIALIZED VIEW IF EXISTS daily_metrics;
DROP VIEW IF EXISTS latest_dexscreener_pairs;
DROP VIEW IF EXISTS latest_defillama_protocols;
DROP VIEW IF EXISTS latest_hypurrscan_holders;
DROP VIEW IF EXISTS latest_flipside_metrics;

-- Create view for latest token metrics
CREATE OR REPLACE VIEW latest_token_metrics AS
SELECT DISTINCT ON (source, symbol, protocol_name)
    *
FROM token_metrics
ORDER BY source, symbol, protocol_name, timestamp DESC;

-- Create view for latest protocol metrics
CREATE OR REPLACE VIEW latest_protocol_metrics AS
SELECT DISTINCT ON (source, protocol_name, chain)
    *
FROM protocol_metrics
ORDER BY source, protocol_name, chain, timestamp DESC;

-- Create view for latest chain metrics
CREATE OR REPLACE VIEW latest_chain_metrics AS
SELECT DISTINCT ON (source, chain)
    *
FROM chain_metrics
ORDER BY source, chain, timestamp DESC;

-- Create materialized view for daily aggregates
CREATE MATERIALIZED VIEW daily_metrics AS
SELECT
    source,
    DATE_TRUNC('day', timestamp) as date,
    COUNT(*) as total_records,
    COUNT(DISTINCT protocol_name) as unique_protocols,
    AVG(CASE WHEN type = 'token' THEN value END) as avg_token_value,
    AVG(CASE WHEN type = 'protocol' THEN value END) as avg_protocol_value,
    COUNT(DISTINCT CASE WHEN type = 'holder' THEN name END) as unique_holders
FROM metrics
GROUP BY source, DATE_TRUNC('day', timestamp)
WITH DATA;

-- Create function to refresh materialized view
CREATE OR REPLACE FUNCTION refresh_daily_metrics()
RETURNS trigger AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY daily_metrics;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Drop existing trigger if it exists
DROP TRIGGER IF EXISTS refresh_daily_metrics_trigger ON metrics;

-- Create trigger to refresh materialized view
CREATE TRIGGER refresh_daily_metrics_trigger
AFTER INSERT OR UPDATE OR DELETE ON metrics
FOR EACH STATEMENT
EXECUTE FUNCTION refresh_daily_metrics();

-- Create views for latest data
CREATE OR REPLACE VIEW latest_dexscreener_pairs AS
SELECT DISTINCT ON (pair_address, chain_id)
    *
FROM dexscreener_pairs
ORDER BY pair_address, chain_id, created_at DESC;

CREATE OR REPLACE VIEW latest_defillama_protocols AS
SELECT DISTINCT ON (protocol_id)
    *
FROM defillama_protocols
ORDER BY protocol_id, created_at DESC;

CREATE OR REPLACE VIEW latest_hypurrscan_holders AS
SELECT DISTINCT ON (token, holder_address)
    *
FROM hypurrscan_holders
ORDER BY token, holder_address, timestamp DESC;

CREATE OR REPLACE VIEW latest_flipside_metrics AS
SELECT DISTINCT ON (project_name, chain)
    *
FROM flipside_nft_metrics
ORDER BY project_name, chain, timestamp DESC;

-- Add comments for documentation
COMMENT ON TABLE metrics IS 'Base table for all metric types';
COMMENT ON TABLE token_metrics IS 'Detailed token-specific metrics from various sources';
COMMENT ON TABLE protocol_metrics IS 'Protocol-level metrics including TVL and volume';
COMMENT ON TABLE holder_metrics IS 'Token holder information and balances';
COMMENT ON TABLE chain_metrics IS 'Blockchain-specific metrics and statistics';
COMMENT ON COLUMN metrics.metadata IS 'JSON field for storing additional source-specific data';
COMMENT ON TABLE dexscreener_pairs IS 'DEX pair data from DexScreener';
COMMENT ON TABLE defillama_protocols IS 'Protocol TVL and metrics from DefiLlama';
COMMENT ON TABLE hypurrscan_holders IS 'Token holder data from Hypurrscan';
COMMENT ON TABLE flipside_nft_metrics IS 'NFT metrics from Flipside';