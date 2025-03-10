import { createClient } from '@supabase/supabase-js';
import * as dotenv from 'dotenv';

// Load environment variables
dotenv.config();

async function setupMarketMetricsTable() {
    console.log('Setting up market_metrics table in Supabase...');
    
    // Initialize Supabase client
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://llanxjeohlxpnndhqbdp.supabase.co';
    const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_KEY || process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

    if (!supabaseKey) {
        throw new Error('Missing Supabase API key');
    }

    const supabase = createClient(supabaseUrl, supabaseKey);
    
    try {
        // Check if the table already exists
        const { data: existingTables, error: tableError } = await supabase
            .from('information_schema.tables')
            .select('table_name')
            .eq('table_schema', 'public')
            .eq('table_name', 'market_metrics');
            
        if (tableError) {
            throw new Error(`Error checking for existing table: ${tableError.message}`);
        }
        
        if (existingTables && existingTables.length > 0) {
            console.log('market_metrics table already exists');
            return;
        }
        
        // Create the market_metrics table using SQL
        const { error: createError } = await supabase.rpc('exec_sql', {
            sql_query: `
                CREATE TABLE public.market_metrics (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    timestamp TIMESTAMPTZ NOT NULL,
                    asset TEXT NOT NULL,
                    exchange TEXT NOT NULL,
                    price NUMERIC NOT NULL,
                    volume_24h NUMERIC NOT NULL,
                    open_interest NUMERIC,
                    funding_rate NUMERIC,
                    mark_price NUMERIC,
                    index_price NUMERIC,
                    bid_price NUMERIC,
                    ask_price NUMERIC,
                    mid_price NUMERIC,
                    spread NUMERIC,
                    liquidity NUMERIC,
                    volatility_24h NUMERIC,
                    price_change_24h NUMERIC,
                    created_at TIMESTAMPTZ NOT NULL,
                    UNIQUE(timestamp, asset, exchange)
                );
                
                -- Create indexes for common queries
                CREATE INDEX idx_market_metrics_asset ON public.market_metrics(asset);
                CREATE INDEX idx_market_metrics_exchange ON public.market_metrics(exchange);
                CREATE INDEX idx_market_metrics_timestamp ON public.market_metrics(timestamp);
                CREATE INDEX idx_market_metrics_asset_exchange ON public.market_metrics(asset, exchange);
                
                -- Enable RLS
                ALTER TABLE public.market_metrics ENABLE ROW LEVEL SECURITY;
                
                -- Create policies
                CREATE POLICY "Allow anonymous read access" 
                ON public.market_metrics FOR SELECT 
                USING (true);
                
                -- Create a function to clean up old data (keep last 30 days)
                CREATE OR REPLACE FUNCTION cleanup_old_market_metrics()
                RETURNS void AS $$
                BEGIN
                    DELETE FROM public.market_metrics
                    WHERE timestamp < NOW() - INTERVAL '30 days';
                END;
                $$ LANGUAGE plpgsql;
                
                -- Create a cron job to run cleanup daily
                SELECT cron.schedule(
                    'cleanup-market-metrics',
                    '0 0 * * *',  -- Run at midnight every day
                    $$SELECT cleanup_old_market_metrics()$$
                );
            `
        });
        
        if (createError) {
            throw new Error(`Error creating market_metrics table: ${createError.message}`);
        }
        
        console.log('Successfully created market_metrics table');
        
    } catch (error) {
        console.error('Setup failed:', error instanceof Error ? error.message : String(error));
        throw error;
    }
}

// Run the setup if this script is executed directly
if (require.main === module) {
    setupMarketMetricsTable()
        .then(() => {
            console.log('Setup completed successfully');
            process.exit(0);
        })
        .catch(error => {
            console.error('Setup failed:', error);
            process.exit(1);
        });
}

export { setupMarketMetricsTable }; 