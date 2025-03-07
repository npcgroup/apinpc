-- Script to modify primary keys to include timestamp column for TimescaleDB
-- This modifies the tables to allow them to be converted to hypertables

-- Backup the existing tables (create backup of orderbook_data as an example)
CREATE TABLE orderbook_data_backup AS SELECT * FROM orderbook_data;

-- Now demonstrate dropping the existing primary key constraint and creating a compound one
-- We'll do this for orderbook_data as an example
ALTER TABLE orderbook_data DROP CONSTRAINT orderbook_data_pkey;

-- Add a new primary key constraint that includes the timestamp column
ALTER TABLE orderbook_data ADD PRIMARY KEY (id, timestamp);

-- Now let's convert this modified table to a hypertable
SELECT create_hypertable('orderbook_data', 'timestamp', 
  chunk_time_interval => INTERVAL '1 day',
  if_not_exists => TRUE,
  migrate_data => TRUE
);

-- We can run similar operations for other tables as needed 