-- Create main schema
CREATE SCHEMA IF NOT EXISTS blockchain_analytics;

-- Enum types for various classifications
CREATE TYPE blockchain_analytics.asset_type AS ENUM (
    'token', 'nft', 'perpetual', 'synthetic', 'option'
);

CREATE TYPE blockchain_analytics.chain_name AS ENUM (
    'ethereum', 'solana', 'arbitrum', 'optimism', 'base', 'polygon'
);

CREATE TYPE blockchain_analytics.data_provider AS ENUM (
    'defillama', 'dune', 'bitquery', 'footprint', 'thegraph', 'hyperliquid'
);

CREATE TYPE blockchain_analytics.environment AS ENUM ('test', 'production');

-- Core tables
CREATE TABLE blockchain_analytics.chains (
    id BIGSERIAL PRIMARY KEY,
    name blockchain_analytics.chain_name NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(name)
);

CREATE TABLE blockchain_analytics.protocols (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL,
    chain_id BIGINT REFERENCES blockchain_analytics.chains(id),
    tvl DECIMAL(24,8),
    description TEXT,
    website_url TEXT,
    github_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(name, chain_id)
);

-- Asset tracking
CREATE TABLE blockchain_analytics.assets (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    name VARCHAR(100),
    type blockchain_analytics.asset_type NOT NULL,
    chain_id BIGINT REFERENCES blockchain_analytics.chains(id),
    decimals INTEGER,
    contract_address TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(symbol, chain_id, type)
);

-- Data sources configuration
CREATE TABLE blockchain_analytics.data_sources (
    id BIGSERIAL PRIMARY KEY,
    provider blockchain_analytics.data_provider NOT NULL,
    version VARCHAR(20) NOT NULL,
    config JSONB,
    rate_limit INTEGER,
    priority INTEGER,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(provider, version)
);

-- Metrics tables
CREATE TABLE blockchain_analytics.token_metrics (
    id BIGSERIAL PRIMARY KEY,
    asset_id BIGINT REFERENCES blockchain_analytics.assets(id),
    environment blockchain_analytics.environment NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    price DECIMAL(24,8),
    volume_24h DECIMAL(24,8),
    market_cap DECIMAL(24,8),
    total_supply DECIMAL(24,8),
    holder_count INTEGER,
    source_id BIGINT REFERENCES blockchain_analytics.data_sources(id),
    raw_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(asset_id, timestamp, environment)
);

CREATE TABLE blockchain_analytics.perpetual_metrics (
    id BIGSERIAL PRIMARY KEY,
    asset_id BIGINT REFERENCES blockchain_analytics.assets(id),
    environment blockchain_analytics.environment NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    funding_rate DECIMAL(18,8),
    open_interest DECIMAL(24,8),
    volume_24h DECIMAL(24,8),
    long_positions DECIMAL(24,8),
    short_positions DECIMAL(24,8),
    liquidations_24h DECIMAL(24,8),
    source_id BIGINT REFERENCES blockchain_analytics.data_sources(id),
    raw_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(asset_id, timestamp, environment)
);

CREATE TABLE blockchain_analytics.nft_metrics (
    id BIGSERIAL PRIMARY KEY,
    asset_id BIGINT REFERENCES blockchain_analytics.assets(id),
    environment blockchain_analytics.environment NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    floor_price DECIMAL(24,8),
    volume_24h DECIMAL(24,8),
    sales_count INTEGER,
    holder_count INTEGER,
    listed_count INTEGER,
    source_id BIGINT REFERENCES blockchain_analytics.data_sources(id),
    raw_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(asset_id, timestamp, environment)
);

-- Protocol metrics
CREATE TABLE blockchain_analytics.protocol_metrics (
    id BIGSERIAL PRIMARY KEY,
    protocol_id BIGINT REFERENCES blockchain_analytics.protocols(id),
    environment blockchain_analytics.environment NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    tvl DECIMAL(24,8),
    volume_24h DECIMAL(24,8),
    unique_users_24h INTEGER,
    transaction_count_24h INTEGER,
    revenue_24h DECIMAL(24,8),
    source_id BIGINT REFERENCES blockchain_analytics.data_sources(id),
    raw_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(protocol_id, timestamp, environment)
);

-- Data quality tracking
CREATE TABLE blockchain_analytics.data_quality (
    id BIGSERIAL PRIMARY KEY,
    source_id BIGINT REFERENCES blockchain_analytics.data_sources(id),
    metric_type VARCHAR(50) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    completeness_score DECIMAL(5,2),
    accuracy_score DECIMAL(5,2),
    timeliness_score DECIMAL(5,2),
    consistency_score DECIMAL(5,2),
    validation_errors JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Audit logging
CREATE TABLE blockchain_analytics.audit_log (
    id BIGSERIAL PRIMARY KEY,
    table_name VARCHAR(50) NOT NULL,
    record_id BIGINT NOT NULL,
    action VARCHAR(20) NOT NULL,
    old_data JSONB,
    new_data JSONB,
    user_id VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Performance indexes
CREATE INDEX idx_token_metrics_asset_time ON blockchain_analytics.token_metrics(asset_id, timestamp);
CREATE INDEX idx_perpetual_metrics_asset_time ON blockchain_analytics.perpetual_metrics(asset_id, timestamp);
CREATE INDEX idx_nft_metrics_asset_time ON blockchain_analytics.nft_metrics(asset_id, timestamp);
CREATE INDEX idx_protocol_metrics_protocol_time ON blockchain_analytics.protocol_metrics(protocol_id, timestamp);
CREATE INDEX idx_data_quality_source_time ON blockchain_analytics.data_quality(source_id, timestamp);
CREATE INDEX idx_audit_log_table_record ON blockchain_analytics.audit_log(table_name, record_id);

-- Triggers for updated_at columns
CREATE OR REPLACE FUNCTION blockchain_analytics.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers to relevant tables
CREATE TRIGGER update_chains_updated_at
    BEFORE UPDATE ON blockchain_analytics.chains
    FOR EACH ROW
    EXECUTE FUNCTION blockchain_analytics.update_updated_at_column();

-- Add similar triggers for other tables with updated_at columns 