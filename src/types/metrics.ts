export interface TokenMetric {
  address: string;
  symbol: string;
  name: string;
  price: number;
  volume24h: number;
  marketCap: number;
  totalSupply: number | null;
  timestamp: string;
}

export interface DexPair {
  pair_address: string;
  chain_id: string;
  dex_id: string;
  token_1_symbol: string;
  token_1_address: string;
  token_2_symbol: string;
  token_2_address: string;
  price_usd: number;
  liquidity_usd: number;
  volume_24h: number;
  price_change_24h: number;
  created_at: string;
}

export interface MetricsData {
  tokens: TokenMetric[];
  pairs: DexPair[];
}

// Keep existing interfaces but rename TokenMetrics to TokenMetricsOld
export interface TokenMetricsOld {
  volume24h: number;
  holders: number;
  totalSupply: number;
}

export interface DexMetrics {
  volume24h: number;
  tvl: number;
  trades24h: number;
  uniqueTraders24h: number;
}

export interface LendingMetrics {
  tvl: number;
  totalBorrowed: number;
  totalSupplied: number;
  borrowApy: number;
  supplyApy: number;
  utilizationRate: number;
}

export interface DerivativesMetrics {
  volume24h: number;
  openInterest: number;
  trades24h: number;
  uniqueTraders24h: number;
}

export interface ChainMetrics {
  tvl: number;
  transactions24h: number;
  fees24h: number;
  activeAddresses24h: number;
} 
