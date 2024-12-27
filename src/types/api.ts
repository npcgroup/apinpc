interface BirdeyeTokenInfo {
  price: string | number
  volume24h: string | number
  priceChange24h: string | number
  marketCap: string | number
  totalSupply: string | number
  holderCount: string | number
  liquidity: string | number
  [key: string]: unknown // Allow for additional properties
}

export interface BirdeyeApiResponse {
  success: boolean
  data: {
    [key: string]: unknown
    data: BirdeyeTokenInfo
  }
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

export interface RawData {
  timestamp: string
  hyperliquid: Record<string, any>
  dexscreener: Record<string, any>
  birdeye: Record<string, any>
  solscan: Record<string, any>
} 