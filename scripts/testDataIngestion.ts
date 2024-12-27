import { DataIngestionService, MetricData } from '@/services/dataIngestion'
import { TOKEN_ADDRESSES } from '@/config/tokens'

async function testDataIngestion() {
  const service = new DataIngestionService()
  
  try {
    // Test single token
    const testSymbol = 'WIF'
    const testAddress = TOKEN_ADDRESSES[testSymbol]
    
    const dexData = await service.fetchDexScreenerData(testAddress)
    const hlData = await service.fetchHyperliquidData(testSymbol)
    
    const metric: MetricData = {
      symbol: testSymbol,
      timestamp: new Date().toISOString(),
      ...hlData,
      ...dexData,
      holder_count: null
    }
    
    await service.ingestMetrics([metric])
    console.log('Test successful')
    console.log('Sample metric:', JSON.stringify(metric, null, 2))
  } catch (error) {
    console.error('Test failed:', error)
    process.exit(1)
  }
}

testDataIngestion() 