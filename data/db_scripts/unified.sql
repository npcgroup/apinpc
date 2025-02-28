-- Create unified analytics schema
CREATE SCHEMA IF NOT EXISTS unified_analytics;

-- Core enums for classification
CREATE TYPE unified_analytics.asset_type AS ENUM (
    'token', 'nft', 'perpetual', 'synthetic', 'option', 'lp_pair'
);

CREATE TYPE unified_analytics.chain_name AS ENUM (
    'ethereum', 'solana', 'arbitrum', 'optimism', 'base', 'polygon'
);

CREATE TYPE unified_analytics.protocol_type AS ENUM (
    'dex', 'lending', 'derivatives', 'yield', 'bridge', 'perps', 'options'
);

-- Base metrics table (all metric tables will inherit from this)
CREATE TABLE unified_analytics.metrics_base (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    environment VARCHAR(20) CHECK (environment IN ('test', 'production')),
    source_id BIGINT,
    confidence_score DECIMAL(5,2),
    raw_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Core asset tracking
CREATE TABLE unified_analytics.assets (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    name VARCHAR(100),
    type unified_analytics.asset_type NOT NULL,
    chain unified_analytics.chain_name NOT NULL,
    protocol_id BIGINT,
    decimals INTEGER,
    contract_address TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(symbol, chain, type, protocol_id)
);

-- Protocol tracking
CREATE TABLE unified_analytics.protocols (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    type unified_analytics.protocol_type NOT NULL,
    chains unified_analytics.chain_name[],
    tvl DECIMAL(24,8),
    description TEXT,
    website_url TEXT,
    github_url TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(name)
);

-- Specialized metric tables inheriting from base
CREATE TABLE unified_analytics.token_metrics (
    asset_id BIGINT REFERENCES unified_analytics.assets(id),
    price DECIMAL(24,8),
    volume_24h DECIMAL(24,8),
    market_cap DECIMAL(24,8),
    total_supply DECIMAL(24,8),
    holder_count INTEGER,
    price_change_24h DECIMAL(10,2)
) INHERITS (unified_analytics.metrics_base);

CREATE TABLE unified_analytics.perpetual_metrics (
    asset_id BIGINT REFERENCES unified_analytics.assets(id),
    funding_rate DECIMAL(18,8),
    predicted_rate DECIMAL(18,8),
    open_interest DECIMAL(24,8),
    volume_24h DECIMAL(24,8),
    long_positions DECIMAL(24,8),
    short_positions DECIMAL(24,8),
    liquidations_24h DECIMAL(24,8),
    mark_price DECIMAL(24,8),
    index_price DECIMAL(24,8)
) INHERITS (unified_analytics.metrics_base);

CREATE TABLE unified_analytics.lp_metrics (
    pool_address VARCHAR(44) NOT NULL,
    token_a_id BIGINT REFERENCES unified_analytics.assets(id),
    token_b_id BIGINT REFERENCES unified_analytics.assets(id),
    tvl_usd DECIMAL(24,8),
    volume_24h DECIMAL(24,8),
    fee_apr DECIMAL(10,4),
    il_24h DECIMAL(10,4),
    reserves_a DECIMAL(24,8),
    reserves_b DECIMAL(24,8)
) INHERITS (unified_analytics.metrics_base);

CREATE TABLE unified_analytics.protocol_metrics (
    protocol_id BIGINT REFERENCES unified_analytics.protocols(id),
    tvl DECIMAL(24,8),
    volume_24h DECIMAL(24,8),
    revenue_24h DECIMAL(24,8),
    unique_users_24h INTEGER,
    transactions_24h INTEGER,
    market_share DECIMAL(10,4),
    risk_score DECIMAL(5,2),
    health_score DECIMAL(5,2),
    performance_metrics JSONB
) INHERITS (unified_analytics.metrics_base);

-- Quality tracking
CREATE TABLE unified_analytics.data_quality (
    id BIGSERIAL PRIMARY KEY,
    metric_table VARCHAR(50) NOT NULL,
    metric_id BIGINT NOT NULL,
    completeness_score DECIMAL(5,2),
    accuracy_score DECIMAL(5,2),
    timeliness_score DECIMAL(5,2),
    consistency_score DECIMAL(5,2),
    validation_errors JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create optimized indexes
CREATE INDEX idx_token_metrics_asset_time ON unified_analytics.token_metrics(asset_id, timestamp DESC);
CREATE INDEX idx_perp_metrics_asset_time ON unified_analytics.perpetual_metrics(asset_id, timestamp DESC);
CREATE INDEX idx_lp_metrics_pool_time ON unified_analytics.lp_metrics(pool_address, timestamp DESC);
CREATE INDEX idx_protocol_metrics_time ON unified_analytics.protocol_metrics(protocol_id, timestamp DESC);
CREATE INDEX idx_quality_metric ON unified_analytics.data_quality(metric_table, metric_id);

-- Create materialized views for common queries
CREATE MATERIALIZED VIEW unified_analytics.latest_protocol_stats AS
SELECT 
    p.name,
    p.type,
    pm.tvl,
    pm.volume_24h,
    pm.unique_users_24h,
    pm.risk_score,
    pm.health_score
FROM unified_analytics.protocols p
JOIN unified_analytics.protocol_metrics pm ON p.id = pm.protocol_id
WHERE pm.timestamp = (
    SELECT MAX(timestamp)
    FROM unified_analytics.protocol_metrics
    WHERE environment = 'production'
)
WITH DATA;