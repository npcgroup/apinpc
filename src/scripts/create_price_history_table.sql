-- Create crypto_price_history table
CREATE TABLE IF NOT EXISTS crypto_price_history (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    exchange VARCHAR(20) NOT NULL,
    datetime TIMESTAMP WITH TIME ZONE NOT NULL,
    price NUMERIC(20, 8) NOT NULL,
    volume NUMERIC(30, 8),
    high NUMERIC(20, 8),
    low NUMERIC(20, 8),
    open NUMERIC(20, 8),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Add unique constraint to prevent duplicate entries
ALTER TABLE crypto_price_history 
ADD CONSTRAINT unique_price_entry UNIQUE (symbol, exchange, datetime);

-- Create indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_price_history_symbol ON crypto_price_history (symbol);
CREATE INDEX IF NOT EXISTS idx_price_history_exchange ON crypto_price_history (exchange);
CREATE INDEX IF NOT EXISTS idx_price_history_datetime ON crypto_price_history (datetime);
CREATE INDEX IF NOT EXISTS idx_price_history_symbol_exchange ON crypto_price_history (symbol, exchange);

-- Add row level security
ALTER TABLE crypto_price_history ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Allow public read access" 
ON crypto_price_history FOR SELECT 
USING (true);

CREATE POLICY "Allow authenticated insert" 
ON crypto_price_history FOR INSERT 
TO authenticated 
WITH CHECK (true);

-- Add table comment
COMMENT ON TABLE crypto_price_history IS 'Historical price data for cryptocurrencies';

-- Create a view for easier querying
CREATE OR REPLACE VIEW crypto_price_view AS
SELECT 
    symbol,
    exchange,
    datetime,
    price,
    volume,
    high,
    low,
    open
FROM crypto_price_history
ORDER BY datetime DESC; 