export interface DexScreenerPair {
  chainId: string
  dexId: string
  url: string
  pairAddress: string
  baseToken: {
    address: string
    name: string
    symbol: string
  }
  priceUsd: string
  priceChange24h: string
  volume24h: string
  liquidity: {
    usd: string
  }
  txns: {
    h24: number
  }
}

export interface DexScreenerResponse {
  pairs: DexScreenerPair[]
}

export interface HyperLiquidAsset {
  name: string
  funding: string
  volume24h: string
  openInterest: string
  markPrice: string
}

export interface HyperLiquidResponse {
  assetCtxs: HyperLiquidAsset[]
}

export interface RawData {
  timestamp: string
  hyperliquid: {
    [symbol: string]: HyperLiquidAsset
  }
  dexscreener: {
    [symbol: string]: DexScreenerPair
  }
  solscan: {
    [symbol: string]: {
      holder_count: number
    }
  }
} 