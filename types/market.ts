export interface MarketUpdate {
  timestamp: string
  title: string
  summary: string
  metrics: {
    total_markets: number
    total_volume: number
    total_oi: number
    avg_funding: number
  }
  charts: {
    funding_distribution: string
    top_markets: string
    funding_volume: string
  }
  highlights: Array<{
    title: string
    content: string
  }>
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
  }
} 