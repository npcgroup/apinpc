-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Chains table (base table for blockchain networks)
CREATE TABLE chains (
    id SERIAL PRIMARY KEY,
    slug TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Protocols table (base table for all protocols)
CREATE TABLE protocols (
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

-- Protocol chains (many-to-many relationship)
CREATE TABLE protocol_chains (
    protocol_id INTEGER REFERENCES protocols(id),
    chain_id INTEGER REFERENCES chains(id),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (protocol_id, chain_id)
);

-- Tokens table (base table for all tokens)
CREATE TABLE tokens (
    id SERIAL PRIMARY KEY,
    address TEXT NOT NULL,
    chain_id INTEGER REFERENCES chains(id),
    symbol TEXT NOT NULL,
    name TEXT NOT NULL,
    decimals INTEGER NOT NULL DEFAULT 18,
    logo_url TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (address, chain_id)
);

-- Protocol tokens (many-to-many relationship)
CREATE TABLE protocol_tokens (
    protocol_id INTEGER REFERENCES protocols(id),
    token_id INTEGER REFERENCES tokens(id),
    is_native BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (protocol_id, token_id)
);

-- Base metrics table (abstract table for common fields)
CREATE TABLE metrics_base (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    source TEXT NOT NULL,
    confidence_score NUMERIC CHECK (confidence_score >= 0 AND confidence_score <= 1),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Protocol metrics table (inherits common fields from metrics_base)
CREATE TABLE protocol_metrics (
    protocol_id INTEGER REFERENCES protocols(id),
    tvl NUMERIC,
    volume_24h NUMERIC,
    fees_24h NUMERIC,
    revenue_24h NUMERIC,
    users_24h INTEGER,
    transactions_24h INTEGER
) INHERITS (metrics_base);

-- Token metrics table (inherits common fields from metrics_base)
CREATE TABLE token_metrics (
    token_id INTEGER REFERENCES tokens(id),
    price_usd NUMERIC,
    volume_24h NUMERIC,
    market_cap_usd NUMERIC,
    total_supply NUMERIC,
    circulating_supply NUMERIC
) INHERITS (metrics_base);

-- Chain metrics table (inherits common fields from metrics_base)
CREATE TABLE chain_metrics (
    chain_id INTEGER REFERENCES chains(id),
    tvl NUMERIC,
    transactions_24h INTEGER,
    fees_24h NUMERIC,
    active_addresses_24h INTEGER
) INHERITS (metrics_base);

-- DEX-specific metrics (inherits from protocol_metrics)
CREATE TABLE dex_metrics (
    trades_24h INTEGER,
    unique_traders_24h INTEGER,
    liquidity_usd NUMERIC,
    price_impact_basis_points NUMERIC
) INHERITS (protocol_metrics);

-- Lending-specific metrics (inherits from protocol_metrics)
CREATE TABLE lending_metrics (
    total_borrowed NUMERIC,
    total_supplied NUMERIC,
    borrow_apy NUMERIC,
    supply_apy NUMERIC,
    utilization_rate NUMERIC
) INHERITS (protocol_metrics);

-- Create indexes for better query performance
CREATE INDEX idx_protocol_metrics_timestamp ON protocol_metrics(timestamp DESC);
CREATE INDEX idx_token_metrics_timestamp ON token_metrics(timestamp DESC);
CREATE INDEX idx_chain_metrics_timestamp ON chain_metrics(timestamp DESC);
CREATE INDEX idx_dex_metrics_timestamp ON dex_metrics(timestamp DESC);
CREATE INDEX idx_lending_metrics_timestamp ON lending_metrics(timestamp DESC);

-- Create indexes for foreign keys
CREATE INDEX idx_protocol_chains_protocol_id ON protocol_chains(protocol_id);
CREATE INDEX idx_protocol_chains_chain_id ON protocol_chains(chain_id);
CREATE INDEX idx_protocol_tokens_protocol_id ON protocol_tokens(protocol_id);
CREATE INDEX idx_protocol_tokens_token_id ON protocol_tokens(token_id);

-- Create composite indexes for common queries
CREATE INDEX idx_token_metrics_token_price ON token_metrics(token_id, timestamp DESC, price_usd);
CREATE INDEX idx_protocol_metrics_tvl ON protocol_metrics(protocol_id, timestamp DESC, tvl);

-- Views for latest metrics
CREATE OR REPLACE VIEW latest_protocol_metrics AS
SELECT DISTINCT ON (protocol_id)
    pm.*,
    p.name as protocol_name,
    p.type as protocol_type
FROM protocol_metrics pm
JOIN protocols p ON p.id = pm.protocol_id
ORDER BY protocol_id, timestamp DESC;

CREATE OR REPLACE VIEW latest_token_metrics AS
SELECT DISTINCT ON (token_id)
    tm.*,
    t.symbol,
    t.name as token_name,
    c.name as chain_name
FROM token_metrics tm
JOIN tokens t ON t.id = tm.token_id
JOIN chains c ON c.id = t.chain_id
ORDER BY token_id, timestamp DESC;

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_protocols_updated_at
    BEFORE UPDATE ON protocols
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tokens_updated_at
    BEFORE UPDATE ON tokens
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column(); 