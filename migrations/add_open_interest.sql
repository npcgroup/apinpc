-- Add notional open interest column to funding_rate_snapshots
ALTER TABLE funding_rate_snapshots 
ADD COLUMN notional_open_interest DECIMAL(30, 10),
ADD COLUMN open_interest_rank INTEGER;

-- Create index for open interest querying
CREATE INDEX idx_funding_snapshots_notional_oi ON funding_rate_snapshots(notional_open_interest);

-- Create view for open interest analysis
CREATE VIEW v_market_open_interest AS
SELECT 
    token,
    timestamp,
    open_interest,
    notional_open_interest,
    open_interest_rank,
    mark_price,
    current_funding_rate,
    exchange
FROM funding_rate_snapshots
WHERE timestamp >= NOW() - INTERVAL '24 hours'
ORDER BY notional_open_interest DESC; 