import { DataIngestionService } from '../services/dataIngestion'
import { supabase } from '../lib/supabaseClient'
import { MetricData as BaseMetricData } from '@/utils/metrics'

interface MetricData extends BaseMetricData {
  timestamp: Date;
  name: string;
  value: number;
  symbol?: string;
  address?: string;
  price?: number;
  volume24h?: number;
  marketCap?: number;
}

interface Protocol {
  name: string;
  tvl: number;
  chains: string[];
  volume24h?: number;
  fees24h?: number;
  users24h?: number;
}

interface DuneMetrics {
  chain: string;
  transactions24h?: number;
  fees24h?: number;
  activeAddresses24h?: number;
  volume24h?: number;
  timestamp?: Date;
  [key: string]: any;
}

// Add interface for raw DexScreener data
interface DexScreenerMetric {
  name: string;
  symbol: string;
  price: number;
  volume24h: number;
  marketCap: number;
  address: string;
  timestamp?: Date;
}

class DataStorageService {
  private ingestionService: DataIngestionService

  constructor() {
    this.ingestionService = new DataIngestionService()
  }

  async storeProtocolMetrics(data: MetricData[]) {
    const { error } = await supabase
      .from('protocol_metrics')
      .insert(data)

    if (error) {
      console.error('Error storing protocol metrics:', error)
      throw error
    }
  }

  async storeTokenMetrics(data: MetricData[]) {
    const { error } = await supabase
      .from('token_metrics')
      .insert(data)

    if (error) {
      console.error('Error storing token metrics:', error)
      throw error
    }
  }

  async storeChainMetrics(data: MetricData[]) {
    const { error } = await supabase
      .from('chain_metrics')
      .insert(data)

    if (error) {
      console.error('Error storing chain metrics:', error)
      throw error
    }
  }

  async ingestAndStore() {
    try {
      console.log('Starting data ingestion and storage...')
      const errors: Error[] = []

      // Fetch protocols
      let protocols: Protocol[] = []
      try {
        protocols = await this.ingestionService.fetchTopProtocols()
      } catch (error) {
        console.error('Error fetching protocols:', error)
        errors.push(error as Error)
      }

      // Fetch chain metrics
      let chainMetrics: DuneMetrics[] = []
      try {
        const results = await Promise.all([
          this.ingestionService.fetchChainMetrics('ethereum'),
          this.ingestionService.fetchChainMetrics('polygon'),
          this.ingestionService.fetchChainMetrics('arbitrum')
        ])
        
        // Filter out any undefined results and ensure chain property exists
        chainMetrics = results.filter((metric): metric is DuneMetrics => {
          return metric !== undefined && typeof metric.chain === 'string'
        })
      } catch (error) {
        console.error('Error fetching chain metrics:', error)
        errors.push(error as Error)
      }

      // For token metrics, we'll use the DEXScreener client directly
      let tokenMetrics: MetricData[] = []
      try {
        const rawMetrics = await this.ingestionService.fetchDEXScreenerData()
        tokenMetrics = rawMetrics.map(metric => ({
          name: metric.name || metric.symbol,
          value: metric.price,
          symbol: metric.symbol,
          address: metric.address,
          timestamp: new Date()
        }))
      } catch (error) {
        console.error('Error fetching DEXScreener data:', error)
        errors.push(error as Error)
      }

      // Store data if available
      if (protocols.length > 0) {
        const protocolMetrics = protocols.map(protocol => ({
          name: protocol.name,
          value: protocol.tvl,
          tvl: protocol.tvl,
          volume24h: protocol.volume24h || 0,
          fees24h: protocol.fees24h || 0,
          users24h: protocol.users24h || 0,
          chains: protocol.chains,
          timestamp: new Date()
        }))
        await this.storeProtocolMetrics(protocolMetrics)
      }

      if (chainMetrics.length > 0) {
        const formattedChainMetrics = chainMetrics.map(metrics => ({
          name: metrics.chain,
          value: metrics.tvl || 0,
          ...metrics,
          timestamp: new Date()
        }))
        await this.storeChainMetrics(formattedChainMetrics)
      }

      if (tokenMetrics.length > 0) {
        await this.storeTokenMetrics(tokenMetrics)
      }

      if (errors.length > 0) {
        console.warn(`Completed with ${errors.length} errors`)
      } else {
        console.log('Data ingestion and storage completed successfully')
      }
    } catch (error) {
      console.error('Fatal error during data ingestion and storage:', error)
      throw error
    }
  }
}

// Create a function to run the ingestion and storage
async function runIngestAndStore() {
  const storageService = new DataStorageService()
  await storageService.ingestAndStore()
}

// Export for importing in other files
export { runIngestAndStore, DataStorageService }

// Run if called directly
if (require.main === module) {
  runIngestAndStore()
    .then(() => process.exit(0))
    .catch((error) => {
      console.error('Fatal error:', error)
      process.exit(1)
    })
}