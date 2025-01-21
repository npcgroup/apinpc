create table if not exists public.gate_market_data (
    id bigint generated always as identity primary key,
    symbol text not null,
    base text not null,
    quote text not null,
    -- Open Interest data
    open_interest numeric not null,
    open_interest_usd numeric not null,
    -- Price data
    mark_price numeric not null,
    volume_24h numeric,
    volume_base_24h numeric,
    -- Price changes
    price_change_24h numeric,
    -- Funding data
    funding_rate numeric,
    next_funding_time timestamp with time zone,
    -- Timestamps
    timestamp bigint not null,
    datetime timestamp with time zone not null,
    created_at timestamp with time zone default now(),
    
    -- Composite unique constraint to prevent exact duplicates
    constraint gate_market_data_unique unique (symbol, timestamp)
);

-- Add indexes for better query performance
create index if not exists gate_market_data_symbol_idx on public.gate_market_data(symbol);
create index if not exists gate_market_data_timestamp_idx on public.gate_market_data(timestamp);
create index if not exists gate_market_data_datetime_idx on public.gate_market_data(datetime);
create index if not exists gate_market_data_volume_idx on public.gate_market_data(volume_24h);
create index if not exists gate_market_data_oi_usd_idx on public.gate_market_data(open_interest_usd); 