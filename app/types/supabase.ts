export interface Database {
  public: {
    Tables: {
      funding_rate_snapshots: {
        Row: {
          id: number
          token: string
          exchange: string
          timestamp: string
          current_funding_rate: number
          predicted_funding_rate: number
          mark_price: number
          open_interest: number
          notional_open_interest: number
          volume_24h: number
          avg_24h_funding_rate: number
          metadata: {
            funding_difference: number
          }
        }
        Insert: Omit<FundingRateSnapshot, 'id'>
        Update: Partial<FundingRateSnapshot>
      }
    }
  }
}

export interface FundingRateSnapshot {
  id: number
  token: string
  exchange: string
  timestamp: string
  current_funding_rate: number
  predicted_funding_rate: number
  mark_price: number
  open_interest: number
  notional_open_interest: number
  volume_24h: number
  avg_24h_funding_rate: number
  metadata: {
    funding_difference: number
  }
}

export interface MarketMetrics {
  token: string
  exchange: string
  latest_snapshot: FundingRateSnapshot
  historical_data: FundingRateSnapshot[]
} 