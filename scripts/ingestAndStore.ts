import { DataIngestionService, MetricData } from '@/services/dataIngestion'
import { TOKEN_ADDRESSES } from '@/config/tokens'

async function main() {
  try {
    const service = new DataIngestionService()
    
    // Test Supabase connection first
    const isConnected = await service.testConnection()
    if (!isConnected) {
      throw new Error('Failed to connect to Supabase')
    }
    
    for (const [symbol, address] of Object.entries(TOKEN_ADDRESSES)) {
      console.log(`Processing ${symbol}...`)
      
      try {
        const [birdeyeData, fundingRate] = await Promise.all([
          service.fetchBirdeyeData(address),
          service.fetchHyperLiquidFunding(symbol)
        ])

        const metric: MetricData = {
          symbol,
          timestamp: new Date().toISOString(),
          mark_price: birdeyeData.price,
          funding_rate: fundingRate,
          open_interest: 0,
          volume_24h: birdeyeData.volume24h,
          price_change_24h: birdeyeData.priceChange24h,
          total_supply: birdeyeData.totalSupply,
          market_cap: birdeyeData.marketCap,
          liquidity: birdeyeData.liquidity,
          spot_price: birdeyeData.price,
          spot_volume_24h: birdeyeData.volume24h,
          txns_24h: 0,
          holder_count: birdeyeData.holderCount
        }

        await service.ingestMetrics([metric])
        console.log(`✅ Successfully ingested data for ${symbol}`)
      } catch (error) {
        console.error(`❌ Error processing ${symbol}:`, error)
      }
    }
  } catch (error) {
    console.error('Fatal error:', error)
    process.exit(1)
  }
}

main()