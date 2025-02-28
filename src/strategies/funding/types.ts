export interface FundingRateData {
  symbol: string;
  exchange: string;
  funding_rate: number;
  predicted_rate: number;
  rate_diff: number;
  time_to_funding: number;
  direction: string;
  annualized_rate: number;
  opportunity_score: number;
  mark_price: number;
  created_at: string;
}

export interface StrategySignal {
  asset: string;
  signal: 'bullish' | 'bearish' | 'neutral';
  strength: number;
  fundingRate: number;
  timestamp: string;
}

export interface MarketTrend {
  asset: string;
  fundingTrend: 'up' | 'down' | 'sideways';
  priceTrend: 'up' | 'down' | 'sideways';
  divergence: boolean;
  confidence: number;
}

export interface FundingArbitrageOpportunity {
  asset: string;
  longExchange: string;
  shortExchange: string;
  fundingRateDiff: number;
  estimatedApy: number;
  confidence: number;
  timestamp: string;
} 