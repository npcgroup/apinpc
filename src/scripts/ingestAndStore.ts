import { DataIngestionService } from '../../src/services/dataIngestion';
import type { PerpetualMetrics } from '../../src/services/dataIngestion';
import { TOKEN_ADDRESSES } from '../../src/config/tokens';
import * as dotenv from 'dotenv'
import { resolve } from 'path'

// Load environment variables from the project root
dotenv.config({ path: resolve(__dirname, '../../.env') })

const DEFAULT_METRIC_VALUES = {
  funding_rate: 0,
  open_interest: 0,
  volume_24h: 0,
  price_change_24h: 0,
  total_supply: 0,
  market_cap: 0,
  txns_24h: 0,
  holder_count: 0,
  daily_volume: 0,  
  long_positions: 0
};

async function processSymbol(
  service: DataIngestionService,
  symbol: string,
  address: string
): Promise<void> {
  try {
    const { birdeye, hyperliquid } = await service.fetchCombinedMarketData(symbol, address);

    const metric: PerpetualMetrics = {
      symbol,
      timestamp: new Date().toISOString(),
      mark_price: hyperliquid.mark_price ?? birdeye.price ?? 0,
      spot_price: birdeye.price ?? 0,
      liquidity: birdeye.liquidity ?? 0,
      spot_volume_24h: birdeye.volume24h ?? 0,
      ...DEFAULT_METRIC_VALUES,
      funding_rate: hyperliquid.funding_rate ?? 0,
      open_interest: hyperliquid.open_interest ?? 0,
      volume_24h: hyperliquid.volume_24h ?? 0,
      price_change_24h: birdeye.priceChange24h ?? 0,
      total_supply: birdeye.totalSupply ?? 0,
      market_cap: birdeye.marketCap ?? 0,
      holder_count: birdeye.holderCount ?? 0,
      daily_volume: hyperliquid.volume_24h ?? 0
    };

    await service.ingestMetrics([metric]);
    console.log(`✅ Successfully ingested data for ${symbol}`);
  } catch (error) {
    console.error(`❌ Error processing ${symbol}:`, error);
    throw error; // Re-throw to be handled by main
  }
}

async function main() {
  // Add environment variable check at the start
  if (!process.env.NEXT_PUBLIC_SUPABASE_URL || !process.env.NEXT_PUBLIC_SUPABASE_KEY) {
    console.error('❌ Missing required environment variables:');
    console.error('NEXT_PUBLIC_SUPABASE_URL:', process.env.NEXT_PUBLIC_SUPABASE_URL ? '✓ Set' : '✗ Missing');
    console.error('NEXT_PUBLIC_SUPABASE_KEY:', process.env.NEXT_PUBLIC_SUPABASE_KEY ? '✓ Set' : '✗ Missing');
    process.exit(1);
  }

  const service = new DataIngestionService();
  let failedSymbols: string[] = [];
  
  try {
    // Add more detailed connection testing
    console.log('Testing Supabase connection...');
    const isConnected = await service.testSupabaseConnection();
    if (!isConnected) {
      console.error('❌ Supabase connection test failed. Please check your credentials and connection settings.');
      throw new Error('Failed to connect to Supabase - connection test returned false');
    }
    console.log('✅ Successfully connected to Supabase');
    
    // Process all symbols concurrently with rate limiting
    const batchSize = 3; // Process 3 symbols at a time
    const symbols = Object.entries(TOKEN_ADDRESSES);
    
    for (let i = 0; i < symbols.length; i += batchSize) {
      const batch = symbols.slice(i, i + batchSize);
      const results = await Promise.allSettled(
        batch.map(([symbol, address]) => processSymbol(service, symbol, address))
      );
      
      // Track failed symbols
      results.forEach((result, index) => {
        if (result.status === 'rejected') {
          failedSymbols.push(batch[index][0]);
        }
      });
      
      // Add delay between batches to avoid rate limits
      if (i + batchSize < symbols.length) {
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
    }
    
    if (failedSymbols.length > 0) {
      console.warn('Failed to process symbols:', failedSymbols);
    }
  } catch (error) {
    console.error('Fatal error:', error);
    if (error instanceof Error) {
      console.error('Error details:', error.message);
      console.error('Stack trace:', error.stack);
    }
    process.exit(1);
  }
}

if (require.main === module) {
  main().catch(error => {
    console.error('Unhandled error:', error);
    process.exit(1);
  });
}