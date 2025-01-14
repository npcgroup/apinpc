export interface MarketUpdate {
  timestamp: string
  metrics: {
    total_markets: number
    total_volume: number
    total_oi: number
    avg_funding: number
    volume_distribution: Array<{
      timestamp: string
      volume: number
    }>
  }
  opportunities: Array<{
    token: string
    current_funding_rate: number
    predicted_funding_rate: number
    notional_open_interest: number
    volume_24h: number
    mark_price: number
  }>
  risk_metrics: {
    volume_concentration: number
    illiquid_markets: number
    largest_drawdown: number
    volatility_index: number
    market_depth: Array<{
      token: string
      depth: number
      utilization: number
    }>
  }
  market_data: {
    highest_funding: {
      token: string
      rate: number
      volume: number
    }
    most_active: {
      token: string
      volume: number
      rate: number
    }
    largest_oi: {
      token: string
      oi: number
      rate: number
    }
    volume_distribution: Array<{
      timestamp: string
      volume: number
    }>
  }
} 