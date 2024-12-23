-- Create schema for perpetuals data
CREATE SCHEMA IF NOT EXISTS perpetuals;

-- Create enum types for data sources and environments
CREATE TYPE perpetuals.data_source_type AS ENUM ('hyperliquid', 'dexscreener', 'helius', 'combined');
CREATE TYPE perpetuals.environment_type AS ENUM ('test', 'production');

-- Create tokens table to store base token information
CREATE TABLE perpetuals.tokens (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    name VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(symbol)
);

-- Create data_sources table to track different data providers
CREATE TABLE perpetuals.data_sources (
    id BIGSERIAL PRIMARY KEY,
    name perpetuals.data_source_type NOT NULL,
    version VARCHAR(20) NOT NULL,
    config JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(name, version)
);

-- Create metrics_versions table to track schema versions
CREATE TABLE perpetuals.metrics_versions (
    id BIGSERIAL PRIMARY KEY,
    version VARCHAR(20) NOT NULL,
    schema_hash VARCHAR(64) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(version)
);

-- Create perpetual_metrics table with versioning and environment tracking
CREATE TABLE perpetuals.perpetual_metrics (
    id BIGSERIAL PRIMARY KEY,
    token_id BIGINT REFERENCES perpetuals.tokens(id),
    version_id BIGINT REFERENCES perpetuals.metrics_versions(id),
    environment perpetuals.environment_type NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    
    -- Market data
    funding_rate DECIMAL(18,8),
    perp_volume_24h DECIMAL(24,8),
    open_interest DECIMAL(24,8),
    mark_price DECIMAL(24,8),
    spot_price DECIMAL(24,8),
    spot_volume_24h DECIMAL(24,8),
    liquidity DECIMAL(24,8),
    
    -- Token metrics
    market_cap DECIMAL(24,8),
    total_supply DECIMAL(24,8),
    holder_count INTEGER,
    price_change_24h DECIMAL(10,2),
    txns_24h INTEGER,
    
    -- Metadata
    source_id BIGINT REFERENCES perpetuals.data_sources(id),
    raw_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(token_id, timestamp, environment, version_id)
);

-- Create metrics_quality table for data quality tracking
CREATE TABLE perpetuals.metrics_quality (
    id BIGSERIAL PRIMARY KEY,
    metric_id BIGINT REFERENCES perpetuals.perpetual_metrics(id),
    completeness_score DECIMAL(5,2),
    accuracy_score DECIMAL(5,2),
    timeliness_score DECIMAL(5,2),
    consistency_score DECIMAL(5,2),
    validation_errors JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create audit_log table for tracking changes
CREATE TABLE perpetuals.audit_log (
    id BIGSERIAL PRIMARY KEY,
    table_name VARCHAR(50) NOT NULL,
    record_id BIGINT NOT NULL,
    action VARCHAR(20) NOT NULL,
    old_data JSONB,
    new_data JSONB,
    user_id VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add indexes for performance
CREATE INDEX idx_perpetual_metrics_token_timestamp ON perpetuals.perpetual_metrics(token_id, timestamp);
CREATE INDEX idx_perpetual_metrics_environment ON perpetuals.perpetual_metrics(environment);
CREATE INDEX idx_metrics_quality_metric_id ON perpetuals.metrics_quality(metric_id);
CREATE INDEX idx_audit_log_table_record ON perpetuals.audit_log(table_name, record_id);

-- Add triggers for updated_at
CREATE OR REPLACE FUNCTION perpetuals.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_tokens_updated_at
    BEFORE UPDATE ON perpetuals.tokens
    FOR EACH ROW
    EXECUTE FUNCTION perpetuals.update_updated_at_column();

CREATE TRIGGER update_perpetual_metrics_updated_at
    BEFORE UPDATE ON perpetuals.perpetual_metrics
    FOR EACH ROW
    EXECUTE FUNCTION perpetuals.update_updated_at_column(); 