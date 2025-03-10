-- Create table for Hyperliquid historical funding rates
CREATE TABLE IF NOT EXISTS hyperliquid_historical_funding (
    id BIGSERIAL PRIMARY KEY,
    asset TEXT NOT NULL,
    funding_rate FLOAT NOT NULL,
    premium FLOAT,
    timestamp BIGINT NOT NULL,
    datetime TEXT NOT NULL,
    exchange TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(asset, timestamp, exchange)
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_hyperliquid_historical_funding_asset ON hyperliquid_historical_funding(asset);
CREATE INDEX IF NOT EXISTS idx_hyperliquid_historical_funding_timestamp ON hyperliquid_historical_funding(timestamp);
CREATE INDEX IF NOT EXISTS idx_hyperliquid_historical_funding_exchange ON hyperliquid_historical_funding(exchange);
CREATE INDEX IF NOT EXISTS idx_hyperliquid_historical_funding_datetime ON hyperliquid_historical_funding(datetime);

-- Add RLS policies for security
ALTER TABLE hyperliquid_historical_funding ENABLE ROW LEVEL SECURITY;

-- Create policy to allow anyone to read the data
CREATE POLICY "Allow public read access" 
ON hyperliquid_historical_funding
FOR SELECT 
USING (true);

-- Create policy to allow only authenticated users to insert data
CREATE POLICY "Allow authenticated insert" 
ON hyperliquid_historical_funding
FOR INSERT 
TO authenticated
USING (true);

-- Add comment to the table
COMMENT ON TABLE hyperliquid_historical_funding IS 'Historical funding rates from Hyperliquid exchange'; 