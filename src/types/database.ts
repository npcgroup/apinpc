export interface TokenMetrics {
  address: string;
  symbol: string;
  name: string;
  price: number;
  volume24h: number;
  marketCap: number;
  totalSupply?: number;
  timestamp: Date;
  holders?: number;
  // ... other fields
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