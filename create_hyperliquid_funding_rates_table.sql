create table if not exists public.hyperliquid_funding_rates (
    id bigint generated always as identity primary key,
    symbol text not null,
    funding_rate numeric not null,
    funding_rate_pct numeric not null,
    timestamp bigint not null,
    datetime timestamp with time zone not null,
    prediction_price numeric,
    next_funding_time timestamp with time zone,
    created_at timestamp with time zone default now(),
    
    -- Composite unique constraint to prevent exact duplicates
    constraint hyperliquid_funding_rates_unique unique (symbol, timestamp)
);

-- Add indexes for better query performance
create index if not exists hyperliquid_funding_rates_symbol_idx on public.hyperliquid_funding_rates(symbol);
create index if not exists hyperliquid_funding_rates_timestamp_idx on public.hyperliquid_funding_rates(timestamp);
create index if not exists hyperliquid_funding_rates_created_at_idx on public.hyperliquid_funding_rates(created_at);

-- Add index for time-based queries
create index if not exists hyperliquid_funding_rates_datetime_idx on public.hyperliquid_funding_rates(datetime); 