-- Drop the existing unique constraint if it exists
ALTER TABLE dex_metrics 
DROP CONSTRAINT IF EXISTS dex_metrics_name_key;

-- Add a new composite unique constraint on name and timestamp
ALTER TABLE dex_metrics
ADD CONSTRAINT dex_metrics_name_timestamp_key UNIQUE (name, timestamp);

-- Add an index for better query performance
CREATE INDEX IF NOT EXISTS idx_dex_metrics_name_timestamp 
ON dex_metrics(name, timestamp DESC); 