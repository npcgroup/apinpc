-- Create funding rate snapshots table
CREATE TABLE funding_rate_snapshots (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    token VARCHAR(20) NOT NULL,
    current_funding_rate DECIMAL(20, 10) NOT NULL,
    predicted_funding_rate DECIMAL(20, 10),
    annualized_funding DECIMAL(20, 10),
    mark_price DECIMAL(30, 10),
    open_interest DECIMAL(30, 10),
    volume_24h DECIMAL(30, 10),
    avg_24h_funding_rate DECIMAL(20, 10),
    exchange VARCHAR(50) NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(timestamp, token, exchange)
);

-- Create funding opportunities table
CREATE TABLE funding_opportunities (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    token VARCHAR(20) NOT NULL,
    opportunity_type VARCHAR(50) NOT NULL,
    current_rate DECIMAL(20, 10) NOT NULL,
    predicted_rate DECIMAL(20, 10),
    annualized_rate DECIMAL(20, 10),
    rate_difference DECIMAL(20, 10),
    exchange VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create market stats table
CREATE TABLE market_stats (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    exchange VARCHAR(50) NOT NULL,
    total_markets INTEGER NOT NULL,
    positive_funding_markets INTEGER NOT NULL,
    negative_funding_markets INTEGER NOT NULL,
    highest_annual_funding DECIMAL(20, 10),
    lowest_annual_funding DECIMAL(20, 10),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(timestamp, exchange)
);

-- Create indexes for better query performance
CREATE INDEX idx_funding_snapshots_timestamp ON funding_rate_snapshots(timestamp);
CREATE INDEX idx_funding_snapshots_token ON funding_rate_snapshots(token);
CREATE INDEX idx_funding_opportunities_timestamp ON funding_opportunities(timestamp);
CREATE INDEX idx_funding_opportunities_type ON funding_opportunities(opportunity_type);
CREATE INDEX idx_market_stats_timestamp ON market_stats(timestamp);

-- Add comments for documentation
COMMENT ON TABLE funding_rate_snapshots IS 'Stores periodic snapshots of funding rates for all tokens';
COMMENT ON TABLE funding_opportunities IS 'Stores notable funding rate opportunities identified during analysis';
COMMENT ON TABLE market_stats IS 'Stores aggregate market statistics for each snapshot'; 