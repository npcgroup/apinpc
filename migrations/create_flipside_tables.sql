-- Create tables for Flipside data
CREATE TABLE IF NOT EXISTS nft_protocol_metrics (
    id BIGSERIAL PRIMARY KEY,
    protocol_name TEXT NOT NULL,
    chain TEXT NOT NULL,
    volume_24h DECIMAL,
    transactions_24h INTEGER,
    unique_users_24h INTEGER,
    avg_price DECIMAL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(protocol_name, chain, created_at)
);

CREATE TABLE IF NOT EXISTS chain_metrics (
    id BIGSERIAL PRIMARY KEY,
    chain TEXT NOT NULL,
    hour TIMESTAMP WITH TIME ZONE,
    tx_count INTEGER,
    active_users INTEGER,
    eth_volume DECIMAL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(chain, hour)
);

CREATE TABLE IF NOT EXISTS nft_collection_metrics (
    id BIGSERIAL PRIMARY KEY,
    collection_name TEXT NOT NULL,
    total_sales INTEGER,
    unique_buyers INTEGER,
    unique_sellers INTEGER,
    total_volume DECIMAL,
    avg_price DECIMAL,
    period_start TIMESTAMP WITH TIME ZONE,
    period_end TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(collection_name, period_start)
); 