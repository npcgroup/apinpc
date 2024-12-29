import { DataIngestionService } from '../src/services/dataIngestion';
import { MetricData } from '../src/types/api';
import { TOKEN_ADDRESSES } from '../src/config/tokens';

async function main() {
  try {
    const service = new DataIngestionService();
    
    // Test connection first
    const isConnected = await service.testSupabaseConnection();
    if (!isConnected) {
      throw new Error('Failed to connect to Supabase');
    }
    
    for (const [symbol, address] of Object.entries(TOKEN_ADDRESSES)) {
      console.log(`Processing ${symbol}...`);
      
      try {
        const { birdeye, hyperliquid } = await service.fetchCombinedMarketData(symbol, address);

        const metric: MetricData = {
          symbol,
          timestamp: new Date().toISOString(),
          mark_price: hyperliquid.mark_price || birdeye.price,
          funding_rate: hyperliquid.funding_rate,
          open_interest: hyperliquid.open_interest,
          volume_24h: hyperliquid.volume_24h,
          price_change_24h: birdeye.priceChange24h,
          total_supply: birdeye.totalSupply,
          market_cap: birdeye.marketCap,
          liquidity: birdeye.liquidity,
          spot_price: birdeye.price,
          spot_volume_24h: birdeye.volume24h,
          txns_24h: 0,
          holder_count: birdeye.holderCount
        };

        await service.ingestMetrics([metric]);
        console.log(`✅ Successfully ingested data for ${symbol}`);
      } catch (error) {
        console.error(`❌ Error processing ${symbol}:`, error);
      }
    }
  } catch (error) {
    console.error('Fatal error:', error);
    process.exit(1);
  }
}

main();