-- Add totalSupply to token_metrics
ALTER TABLE token_metrics 
ADD COLUMN IF NOT EXISTS totalSupply NUMERIC;

-- Add column description
COMMENT ON COLUMN token_metrics.totalSupply IS 'Total supply of the token'; 