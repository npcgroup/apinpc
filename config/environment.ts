export const environment = {
  supabaseUrl: process.env.SUPABASE_URL || '',
  supabaseKey: process.env.SUPABASE_KEY || '',
  redisHost: process.env.REDIS_HOST || 'localhost',
  redisPort: parseInt(process.env.REDIS_PORT || '6379'),
  redisPassword: process.env.REDIS_PASSWORD,
  apiKeys: {
    defillama: process.env.DEFILLAMA_API_KEY,
    dune: process.env.DUNE_API_KEY,
    bitquery: process.env.BITQUERY_API_KEY,
    footprint: process.env.FOOTPRINT_API_KEY,
    thegraph: process.env.THEGRAPH_API_KEY,
    hyperliquid: process.env.HYPERLIQUID_API_KEY
  }
}; 