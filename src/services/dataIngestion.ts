import { createClient } from '@supabase/supabase-js'
import type { Database } from '../types/supabase'
import { DexScreenerResponse, HyperLiquidResponse, RawData } from '../types/api'
import fs from 'fs/promises'
import path from 'path'

export interface MetricData {
  symbol: string
  timestamp: string
  funding_rate: number
  volume_24h: number
  open_interest: number
  mark_price: number
  spot_price: number
  spot_volume_24h: number
  liquidity: number
  market_cap: number | null
  total_supply: number | null
  price_change_24h: number
  txns_24h: number
  holder_count: number | null
}

export interface BirdeyeTokenData {
  price: number
  volume24h: number
  priceChange24h: number
  marketCap: number
  totalSupply: number
  holderCount: number
  liquidity: number
}

export class DataIngestionService {
  private supabase
  private rawData: RawData

  constructor() {
    this.supabase = createClient<Database>(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
    )
    this.rawData = {
      timestamp: new Date().toISOString(),
      hyperliquid: {},
      dexscreener: {},
      birdeye: {},
      solscan: {}
    }
  }

  async fetchBirdeyeData(address: string): Promise<BirdeyeTokenData> {
    const url = `https://public-api.birdeye.so/defi/token_overview?address=${address}`
    const response = await fetch(url, {
      headers: {
        'accept': 'application/json',
        'X-API-KEY': process.env.BIRDEYE_API_KEY!
      }
    })

    if (!response.ok) {
      throw new Error(`Birdeye API error: ${response.statusText}`)
    }

    const data = await response.json()
    if (!data.success) {
      throw new Error(`Birdeye API error: ${data.message || 'Unknown error'}`)
    }

    const tokenData = data.data
    return {
      price: tokenData.price || 0,
      volume24h: tokenData.volume24h || 0,
      priceChange24h: tokenData.priceChange24h || 0,
      marketCap: tokenData.marketCap || 0,
      totalSupply: tokenData.totalSupply || 0,
      holderCount: tokenData.holderCount || 0,
      liquidity: tokenData.liquidity || 0
    }
  }

  async fetchHyperLiquidFunding(symbol: string): Promise<number> {
    const response = await fetch('https://api.hyperliquid.xyz/info', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type: "fundingAll" })
    })

    if (!response.ok) {
      throw new Error(`HyperLiquid API error: ${response.statusText}`)
    }

    const data = await response.json()
    const assetFunding = data.find((item: any) => item.coin === symbol)
    return assetFunding ? parseFloat(assetFunding.funding) : 0
  }

  async ingestMetrics(metrics: MetricData[]): Promise<void> {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '')
    await this.saveRawData(timestamp)
    
    const { error } = await this.supabase
      .from('perpetual_metrics')
      .insert(metrics)

    if (error) throw error
  }

  private async saveRawData(timestamp: string): Promise<void> {
    const dataDir = path.join(process.cwd(), 'data')
    await fs.mkdir(dataDir, { recursive: true })
    
    const filePath = path.join(dataDir, `all_data_${timestamp}.json`)
    await fs.writeFile(filePath, JSON.stringify(this.rawData, null, 2))
  }
} 