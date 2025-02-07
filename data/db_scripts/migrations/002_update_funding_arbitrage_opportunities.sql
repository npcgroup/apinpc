-- Drop existing table constraints and indices
DROP INDEX IF EXISTS idx_funding_arb_spread;
DROP INDEX IF EXISTS idx_funding_arb_yield;
DROP INDEX IF EXISTS idx_funding_arb_timestamp;
DROP INDEX IF EXISTS idx_funding_arb_position;
DROP INDEX IF EXISTS idx_funding_arb_strategy;

-- Modify the existing table
ALTER TABLE funding_arbitrage_opportunities
ADD COLUMN IF NOT EXISTS market_size numeric,
ADD COLUMN IF NOT EXISTS volume_24h numeric,
ADD COLUMN IF NOT EXISTS funding_payment_time timestamp with time zone,
ADD COLUMN IF NOT EXISTS next_funding_time timestamp with time zone,
ADD COLUMN IF NOT EXISTS priority_score numeric;

-- Rename position column to position_type to avoid reserved keyword
ALTER TABLE funding_arbitrage_opportunities
RENAME COLUMN position TO position_type;

-- Update unique constraint
ALTER TABLE funding_arbitrage_opportunities 
DROP CONSTRAINT IF EXISTS funding_arbitrage_opportunities_coin_strategy_counterparty_key;

ALTER TABLE funding_arbitrage_opportunities
ADD CONSTRAINT funding_arbitrage_opportunities_unique 
UNIQUE (coin, strategy, counterparty, timestamp);

-- Create new indices for better query performance
CREATE INDEX idx_funding_arb_spread ON funding_arbitrage_opportunities(spread DESC);
CREATE INDEX idx_funding_arb_yield ON funding_arbitrage_opportunities(annualized_yield DESC);
CREATE INDEX idx_funding_arb_priority ON funding_arbitrage_opportunities(priority_score DESC);
CREATE INDEX idx_funding_arb_timestamp ON funding_arbitrage_opportunities(timestamp DESC);
CREATE INDEX idx_funding_arb_next_funding ON funding_arbitrage_opportunities(next_funding_time);

-- Create views for different arbitrage strategies
CREATE OR REPLACE VIEW v_top_long_hl_opportunities AS
SELECT 
    coin,
    strategy,
    hyperliquid_rate,
    counterparty,
    counterparty_rate,
    spread,
    annualized_yield,
    market_size,
    volume_24h,
    next_funding_time,
    priority_score,
    timestamp
FROM funding_arbitrage_opportunities
WHERE position_type = 'Long HL'
    AND timestamp > NOW() - INTERVAL '5 minutes'
ORDER BY priority_score DESC, spread DESC
LIMIT 10;

CREATE OR REPLACE VIEW v_top_short_hl_opportunities AS
SELECT 
    coin,
    strategy,
    hyperliquid_rate,
    counterparty,
    counterparty_rate,
    spread,
    annualized_yield,
    market_size,
    volume_24h,
    next_funding_time,
    priority_score,
    timestamp
FROM funding_arbitrage_opportunities
WHERE position_type = 'Short HL'
    AND timestamp > NOW() - INTERVAL '5 minutes'
ORDER BY priority_score DESC, spread DESC
LIMIT 10;

-- Create function to get best opportunities
CREATE OR REPLACE FUNCTION get_best_funding_opportunities(
    min_spread numeric DEFAULT 0.001,
    min_market_size numeric DEFAULT 1000000,
    min_volume numeric DEFAULT 100000
)
RETURNS TABLE (
    position_type text,
    coin text,
    strategy text,
    hyperliquid_rate numeric,
    counterparty text,
    counterparty_rate numeric,
    spread numeric,
    annualized_yield numeric,
    market_size numeric,
    volume_24h numeric,
    next_funding_time timestamp with time zone,
    priority_score numeric
) AS $$
BEGIN
    RETURN QUERY
    (
        SELECT 
            f.position_type,
            f.coin,
            f.strategy,
            f.hyperliquid_rate,
            f.counterparty,
            f.counterparty_rate,
            f.spread,
            f.annualized_yield,
            f.market_size,
            f.volume_24h,
            f.next_funding_time,
            f.priority_score
        FROM funding_arbitrage_opportunities f
        WHERE f.position_type = 'Long HL'
            AND f.timestamp > NOW() - INTERVAL '5 minutes'
            AND ABS(f.spread) >= min_spread
            AND f.market_size >= min_market_size
            AND f.volume_24h >= min_volume
        ORDER BY f.priority_score DESC, f.spread DESC
        LIMIT 5
    )
    UNION ALL
    (
        SELECT 
            f.position_type,
            f.coin,
            f.strategy,
            f.hyperliquid_rate,
            f.counterparty,
            f.counterparty_rate,
            f.spread,
            f.annualized_yield,
            f.market_size,
            f.volume_24h,
            f.next_funding_time,
            f.priority_score
        FROM funding_arbitrage_opportunities f
        WHERE f.position_type = 'Short HL'
            AND f.timestamp > NOW() - INTERVAL '5 minutes'
            AND ABS(f.spread) >= min_spread
            AND f.market_size >= min_market_size
            AND f.volume_24h >= min_volume
        ORDER BY f.priority_score DESC, f.spread DESC
        LIMIT 5
    );
END;
$$ LANGUAGE plpgsql;

-- Example usage:
-- SELECT * FROM get_best_funding_opportunities(0.002, 2000000, 200000); 