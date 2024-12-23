-- Token metrics table
CREATE TABLE IF NOT EXISTS token_metrics (
    id BIGSERIAL PRIMARY KEY,
    token_address TEXT NOT NULL,
    symbol TEXT,
    name TEXT,
    price DECIMAL,
    volume_24h DECIMAL,
    market_cap DECIMAL,
    total_supply DECIMAL,
    timestamp TIMESTAMP WITH TIME ZONE,
    source TEXT,
    UNIQUE(token_address, timestamp)
);

-- DEX pairs table
CREATE TABLE IF NOT EXISTS dexscreener_pairs (
    id BIGSERIAL PRIMARY KEY,
    pair_address TEXT NOT NULL,
    chain_id TEXT,
    dex_id TEXT,
    token_1_symbol TEXT,
    token_1_address TEXT,
    token_2_symbol TEXT,
    token_2_address TEXT,
    price_usd DECIMAL,
    liquidity_usd DECIMAL,
    volume_24h DECIMAL,
    price_change_24h DECIMAL,
    created_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(pair_address, chain_id, created_at)
); 