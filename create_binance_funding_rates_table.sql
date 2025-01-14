create table if not exists public.binance_funding_rates (
    id bigint generated always as identity primary key,
    symbol text not null,
    funding_rate numeric not null,
    funding_rate_pct numeric not null,
    timestamp bigint not null,
    datetime timestamp with time zone not null,
    created_at timestamp with time zone default now(),
    
    -- Add a unique constraint to prevent duplicate entries for the same symbol and timestamp
    unique(symbol, timestamp)
);

-- Add indexes for better query performance
create index if not exists binance_funding_rates_symbol_idx on public.binance_funding_rates(symbol);
create index if not exists binance_funding_rates_timestamp_idx on public.binance_funding_rates(timestamp); 