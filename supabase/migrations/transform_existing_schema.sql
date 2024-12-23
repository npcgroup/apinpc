-- Start a transaction
BEGIN;

-- 1. Create new tables while preserving existing data
-- Create chains table and populate with existing chain data
CREATE TABLE chains_new (
    id SERIAL PRIMARY KEY,
    slug TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO chains_new (slug, name)
SELECT DISTINCT 
    LOWER(REGEXP_REPLACE(chain, '[^a-zA-Z0-9]', '-', 'g')) as slug,
    chain as name
FROM chain_metrics;

-- Create protocols table and populate with existing protocol data
CREATE TABLE protocols_new (
    id SERIAL PRIMARY KEY,
    slug TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('dex', 'lending', 'derivatives', 'yield', 'bridge')),
    website_url TEXT,
    description TEXT,
    logo_url TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Insert protocols from various sources
INSERT INTO protocols_new (slug, name, type)
SELECT DISTINCT 
    LOWER(REGEXP_REPLACE(name, '[^a-zA-Z0-9]', '-', 'g')) as slug,
    name,
    CASE 
        WHEN EXISTS (SELECT 1 FROM dex_metrics d WHERE d.name = p.name) THEN 'dex'
        WHEN EXISTS (SELECT 1 FROM lending_metrics l WHERE l.name = p.name) THEN 'lending'
        ELSE 'yield'
    END as type
FROM protocol_metrics p;

-- Create tokens table and populate with existing token data
CREATE TABLE tokens_new (
    id SERIAL PRIMARY KEY,
    address TEXT NOT NULL,
    chain_id INTEGER REFERENCES chains_new(id),
    symbol TEXT NOT NULL,
    name TEXT NOT NULL,
    decimals INTEGER NOT NULL DEFAULT 18,
    logo_url TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (address, chain_id)
);

-- Insert tokens from token_metrics
INSERT INTO tokens_new (address, symbol, name, chain_id)
SELECT DISTINCT 
    t.address,
    t.symbol,
    t.name,
    c.id as chain_id
FROM token_metrics t
CROSS JOIN (SELECT id FROM chains_new WHERE slug = 'ethereum' LIMIT 1) c;

-- Create the base metrics table
CREATE TABLE metrics_base (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    source TEXT NOT NULL,
    confidence_score NUMERIC CHECK (confidence_score >= 0 AND confidence_score <= 1),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create new metrics tables inheriting from base
CREATE TABLE protocol_metrics_new (
    protocol_id INTEGER REFERENCES protocols_new(id),
    tvl NUMERIC,
    volume_24h NUMERIC,
    fees_24h NUMERIC,
    revenue_24h NUMERIC,
    users_24h INTEGER,
    transactions_24h INTEGER
) INHERITS (metrics_base);

-- Migrate protocol metrics data
INSERT INTO protocol_metrics_new (
    protocol_id, tvl, volume_24h, fees_24h, users_24h, 
    timestamp, source, confidence_score
)
SELECT 
    p.id as protocol_id,
    pm.tvl,
    pm.volume_24h,
    pm.fees_24h,
    pm.users_24h,
    pm.timestamp,
    'historical_migration' as source,
    1 as confidence_score
FROM protocol_metrics pm
JOIN protocols_new p ON p.name = pm.name;

-- Similar migrations for other metrics tables...

-- After successful migration, rename tables
ALTER TABLE protocol_metrics RENAME TO protocol_metrics_old;
ALTER TABLE protocol_metrics_new RENAME TO protocol_metrics;

ALTER TABLE tokens RENAME TO tokens_old;
ALTER TABLE tokens_new RENAME TO tokens;

-- Create necessary indexes on new tables
CREATE INDEX idx_protocol_metrics_timestamp ON protocol_metrics(timestamp DESC);
CREATE INDEX idx_protocol_metrics_protocol_id ON protocol_metrics(protocol_id);

-- Create updated views
CREATE OR REPLACE VIEW latest_protocol_metrics AS
SELECT DISTINCT ON (protocol_id)
    pm.*,
    p.name as protocol_name,
    p.type as protocol_type
FROM protocol_metrics pm
JOIN protocols_new p ON p.id = pm.protocol_id
ORDER BY protocol_id, timestamp DESC;

COMMIT;

-- Backup tables can be dropped later after verifying migration
-- DROP TABLE protocol_metrics_old;
-- DROP TABLE tokens_old; 