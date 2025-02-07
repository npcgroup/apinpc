def setup_supabase_tables():
    """Create required Supabase tables if they don't exist"""
    try:
        # ... existing connection code ...

        # Create funding_rates table
        create_funding_rates = """
        create table if not exists public.funding_rates (
            id bigint primary key generated always as identity,
            symbol text not null,
            exchange text not null,
            funding_rate numeric not null,
            predicted_rate numeric,
            mark_price numeric,
            next_funding_time timestamptz,
            payment_interval integer,
            annualized_rate numeric,
            time_to_funding numeric default 8.0,
            opportunity_score numeric default 0.0,
            timestamp timestamptz default now(),
            created_at timestamptz default now()
        );
        """
        
        # Create funding_arbitrage_opportunities table
        create_arbitrage_opps = """
        create table if not exists public.funding_arbitrage_opportunities (
            id bigint primary key generated always as identity,
            coin text not null,
            exchange text not null,
            funding_rate numeric not null,
            predicted_rate numeric,
            mark_price numeric,
            volume_24h numeric,
            priority_score numeric,
            market_size numeric,
            time_to_funding numeric default 8.0,
            opportunity_score numeric default 0.0,
            timestamp timestamptz default now(),
            created_at timestamptz default now()
        );
        """
        
        # Execute the table creation
        supabase.rest.sql().execute(create_funding_rates)
        supabase.rest.sql().execute(create_arbitrage_opps)
        
        return True
        
    except Exception as e:
        logger.error(f"Error setting up Supabase tables: {e}")
        return False 