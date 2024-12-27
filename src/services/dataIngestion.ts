import { createClient } from '@supabase/supabase-js'
import type { Database } from '@/types/supabase'
import { BirdeyeTokenData, RawData } from '@/types/api'
import fs from 'fs/promises'
import path from 'path'
import { env } from '@/config/env'
import type { Exchange } from 'ccxt'
import * as ccxt from 'ccxt'
import birdeyedotso from '@api/birdeyedotso'
import axios from 'axios'

// HyperLiquid API Types
interface HyperliquidAssetCtx {
  dayNtlVlm: string
  funding: string
  impactPxs: [string, string]
  markPx: string
  midPx: string
  openInterest: string
  oraclePx: string
  premium: string
  prevDayPx: string
}

interface HyperliquidMetaAndAssetCtxResponse {
  meta: {
    universe: Array<{
      name: string
      szDecimals: number
      maxLeverage: number
      onlyIsolated: boolean
    }>
  }
  assetCtxs: Record<string, HyperliquidAssetCtx>
}

async function fetchHyperliquidDirectAPI(symbol: string) {
  try {
    // Fetch asset contexts and metadata
    const assetResponse = await axios.post<HyperliquidMetaAndAssetCtxResponse>('https://api.hyperliquid.xyz/info', {
      type: 'metaAndAssetCtxs'
    }, {
      headers: {
        'Content-Type': 'application/json'
      }
    })

    // Validate response structure
    if (!assetResponse.data?.assetCtxs) {
      throw new Error('Invalid API response structure')
    }
    
    const assetInfo = assetResponse.data.assetCtxs[symbol]
    if (!assetInfo) {
      throw new Error(`Asset ${symbol} not found in HyperLiquid API response`)
    }

    // Parse numeric values with validation
    const parseValue = (value: string | undefined, fallback = '0'): number => {
      if (!value) return 0
      const parsed = parseFloat(value)
      return isNaN(parsed) ? 0 : parsed
    }

    // Calculate 24h volume from notional volume and mark price
    const markPrice = parseValue(assetInfo.markPx)
    const notionalVolume = parseValue(assetInfo.dayNtlVlm)
    const baseVolume = markPrice ? notionalVolume / markPrice : 0

    const result = {
      funding_rate: parseValue(assetInfo.funding),
      mark_price: markPrice,
      open_interest: parseValue(assetInfo.openInterest),
      volume_24h: baseVolume,
      oracle_price: parseValue(assetInfo.oraclePx),
      premium: parseValue(assetInfo.premium),
      price_24h_ago: parseValue(assetInfo.prevDayPx),
      impact_prices: assetInfo.impactPxs.map(p => parseValue(p)),
      mid_price: parseValue(assetInfo.midPx)
    }

    // Log successful API response with validation
    console.log('HyperLiquid API Response:', {
      symbol,
      markPrice: result.mark_price,
      fundingRate: result.funding_rate,
      volume24h: result.volume_24h,
      openInterest: result.open_interest,
      timestamp: new Date().toISOString()
    })

    return result
  } catch (error) {
    console.error('Error fetching from HyperLiquid API:', error)
    if (axios.isAxiosError(error)) {
      console.error('Response details:', {
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data,
        url: error.config?.url,
        method: error.config?.method,
        timestamp: new Date().toISOString()
      })
    }
    throw error
  }
}

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

export class DataIngestionService {
  private supabase
  private rawData: RawData
  private hyperliquid!: Exchange

  constructor() {
    this.supabase = createClient<Database>(
      env.SUPABASE_URL,
      env.SUPABASE_SERVICE_KEY
    )
    this.rawData = {
      timestamp: new Date().toISOString(),
      hyperliquid: {},
      dexscreener: {},
      birdeye: {},
      solscan: {}
    }
    
    this.initializeExchange()
    // Initialize Birdeye API
    birdeyedotso.auth(env.BIRDEYE_API_KEY)
  }

  private initializeExchange() {
    try {
      this.hyperliquid = new ccxt.hyperliquid({
        enableRateLimit: true,
        timeout: 30000,
        options: {
          defaultType: 'swap',
          adjustForTimeDifference: true,
          createMarketBuyOrderRequiresPrice: false
        }
      })
    } catch (error) {
      console.error('Failed to initialize HyperLiquid CCXT:', error)
      throw new Error('Failed to initialize exchange')
    }
  }

  async fetchHyperliquidData(symbol: string) {
    try {
      if (!this.hyperliquid) {
        throw new Error('HyperLiquid CCXT not initialized')
      }

      try {
        // Try CCXT first
        await this.hyperliquid.loadMarkets()
        console.log('Available markets:', Object.keys(this.hyperliquid.markets))

        const ccxtSymbol = symbol
        console.log('Fetching HyperLiquid data for symbol:', ccxtSymbol)

        const [fundingRates, ticker] = await Promise.all([
          this.hyperliquid.fetchFundingRates([ccxtSymbol]),
          this.hyperliquid.fetchTicker(ccxtSymbol)
        ])

        const fundingRate = fundingRates[ccxtSymbol]?.fundingRate || 0

        const result = {
          funding_rate: fundingRate,
          mark_price: ticker.last || ticker.close || 0,
          open_interest: parseFloat(ticker.info?.openInterest || '0'),
          volume_24h: ticker.baseVolume || 0
        }

        this.rawData.hyperliquid[symbol] = {
          name: symbol,
          ...result,
          funding: result.funding_rate.toString(),
          markPrice: result.mark_price.toString(),
          openInterest: result.open_interest.toString(),
          volume24h: result.volume_24h.toString()
        }

        return result

      } catch (ccxtError) {
        console.log('CCXT failed, falling back to direct API:', ccxtError)
        
        // Fallback to direct API
        const directData = await fetchHyperliquidDirectAPI(symbol)
        
        this.rawData.hyperliquid[symbol] = {
          name: symbol,
          funding: directData.funding_rate.toString(),
          markPrice: directData.mark_price.toString(),
          openInterest: directData.open_interest.toString(),
          volume24h: directData.volume_24h.toString(),
          oraclePrice: directData.oracle_price.toString(),
          premium: directData.premium.toString(),
          price24hAgo: directData.price_24h_ago.toString()
        }

        return {
          funding_rate: directData.funding_rate,
          mark_price: directData.mark_price,
          open_interest: directData.open_interest,
          volume_24h: directData.volume_24h
        }
      }
    } catch (error) {
      console.error('Both CCXT and direct API failed:', error)
      return {
        funding_rate: 0,
        mark_price: 0,
        open_interest: 0,
        volume_24h: 0
      }
    }
  }

  async fetchBirdeyeData(address: string): Promise<BirdeyeTokenData> {
    try {
      console.log('Fetching Birdeye data for address:', address)
      
      const response = await birdeyedotso.getDefiToken_overview({
        address,
        'x-chain': 'solana'
      })

      // Detailed response logging
      console.log('Raw Birdeye Response:', response)
      console.log('Response type:', typeof response)
      console.log('Response structure:', JSON.stringify(response, null, 2))

      // Type-safe data extraction
      if (!response || typeof response !== 'object') {
        throw new Error('Invalid response from Birdeye API')
      }

      const tokenData = response.data?.data
      console.log('Token data:', tokenData)

      if (!tokenData || typeof tokenData !== 'object') {
        throw new Error('Invalid token data structure')
      }

      const result: BirdeyeTokenData = {
        price: this.parseNumber(tokenData.price),
        volume24h: this.parseNumber(tokenData.volume24h),
        priceChange24h: this.parseNumber(tokenData.priceChange24h),
        marketCap: this.parseNumber(tokenData.marketCap),
        totalSupply: this.parseNumber(tokenData.totalSupply),
        holderCount: this.parseNumber(tokenData.holderCount),
        liquidity: this.parseNumber(tokenData.liquidity)
      }

      this.rawData.birdeye[address] = result
      return result
    } catch (error) {
      console.error('Error fetching Birdeye data:', error)
      return {
        price: 0,
        volume24h: 0,
        priceChange24h: 0,
        marketCap: 0,
        totalSupply: 0,
        holderCount: 0,
        liquidity: 0
      }
    }
  }

  private parseNumber(value: unknown): number {
    if (typeof value === 'number') return value
    if (typeof value === 'string') return parseFloat(value) || 0
    return 0
  }

  async fetchDexScreenerData(address: string) {
    try {
      const response = await fetch(`https://api.dexscreener.com/latest/dex/tokens/${address}`)
      if (!response.ok) {
        throw new Error(`DexScreener API error: ${response.statusText}`)
      }
      
      const responseData = await response.json()
      const pair = responseData.pairs?.[0]
      
      const result = {
        price: parseFloat(pair?.priceUsd || '0'),
        volume24h: parseFloat(pair?.volume?.h24 || '0'),
        liquidity: parseFloat(pair?.liquidity?.usd || '0'),
        priceChange24h: parseFloat(pair?.priceChange?.h24 || '0')
      }

      this.rawData.dexscreener[address] = result
      return result
    } catch (error) {
      console.error('Error fetching DexScreener data:', error)
      return {
        price: 0,
        volume24h: 0,
        liquidity: 0,
        priceChange24h: 0
      }
    }
  }

  async ingestMetrics(metrics: MetricData[]): Promise<void> {
    const timestamp = new Date().toISOString()
    await this.saveRawData(timestamp)
    
    const formattedMetrics = metrics.map(metric => ({
      ...metric,
      daily_volume: metric.volume_24h,
      created_at: timestamp,
      updated_at: timestamp
    }))
    
    console.log('Attempting to insert metrics:', JSON.stringify(formattedMetrics, null, 2))
    
    const { error } = await this.supabase
      .from('perpetual_metrics')
      .insert(formattedMetrics)

    if (error) {
      console.error('Supabase error:', error)
      throw error
    }

    console.log(`Successfully inserted ${metrics.length} metrics`)
  }

  private async saveRawData(timestamp: string): Promise<void> {
    const dataDir = path.join(process.cwd(), 'data')
    await fs.mkdir(dataDir, { recursive: true })
    
    const filePath = path.join(dataDir, `raw_data_${timestamp.replace(/[:.]/g, '')}.json`)
    await fs.writeFile(filePath, JSON.stringify(this.rawData, null, 2))
  }

  async testConnection(): Promise<boolean> {
    try {
      const { error } = await this.supabase
        .from('perpetual_metrics')
        .select('id')
        .limit(1)
        .single()

      if (error) {
        console.error('Supabase connection test failed:', error)
        return false
      }

      console.log('Supabase connection test successful')
      return true
    } catch (error) {
      console.error('Supabase connection test error:', error)
      return false
    }
  }
} 