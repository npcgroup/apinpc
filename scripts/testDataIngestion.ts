import dotenv from 'dotenv'
import { resolve } from 'path'

// Load environment variables from all possible locations
dotenv.config({ path: resolve(__dirname, '../.env') })
dotenv.config({ path: resolve(__dirname, '../.env.local') })
dotenv.config({ path: resolve(__dirname, '../app/.env.local') })

import { DataIngestionService } from '../src/services/dataIngestion'
import { TOKEN_ADDRESSES } from '../src/config/tokens'

async function testDataIngestion() {
  const service = new DataIngestionService()
  
  try {
    // Test Supabase connection first
    const isConnected = await service.testConnection()
    if (!isConnected) {
      throw new Error('Failed to connect to Supabase')
    }

    // Test with POPCAT as our first token
    const testSymbol = 'POPCAT'
    const testAddress = TOKEN_ADDRESSES[testSymbol]
    
    console.log(`Testing with ${testSymbol} (${testAddress})...`)
    
    const [birdeyeData, dexData, hlData] = await Promise.all([
      service.fetchBirdeyeData(testAddress),
      service.fetchDexScreenerData(testAddress),
      service.fetchHyperliquidData(testSymbol)
    ])

    const metric = {
      symbol: testSymbol,
      timestamp: new Date().toISOString(),
      mark_price: hlData.mark_price || birdeyeData.price,
      funding_rate: hlData.funding_rate,
      open_interest: hlData.open_interest,
      volume_24h: hlData.volume_24h,
      price_change_24h: birdeyeData.priceChange24h,
      total_supply: birdeyeData.totalSupply,
      market_cap: birdeyeData.marketCap,
      liquidity: Math.max(birdeyeData.liquidity, dexData.liquidity),
      spot_price: birdeyeData.price,
      spot_volume_24h: Math.max(birdeyeData.volume24h, dexData.volume24h),
      txns_24h: 0,
      holder_count: birdeyeData.holderCount
    }
    
    await service.ingestMetrics([metric])
    console.log('✅ Test successful')
    console.log('Sample metric:', JSON.stringify(metric, null, 2))
  } catch (error) {
    console.error('❌ Test failed:', error)
    process.exit(1)
  }
}

testDataIngestion() 