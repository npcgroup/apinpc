export interface Database {
  public: {
    Tables: {
      perpetual_metrics: {
        Row: {
          id: number
          symbol: string
          timestamp: string
          mark_price: number
          funding_rate: number
          open_interest: number
          volume_24h: number
          price_change_24h: number
          total_supply: number
          market_cap: number
          liquidity: number
          spot_price: number
          spot_volume_24h: number
          holders: number | null
        }
        Insert: Omit<Database['public']['Tables']['perpetual_metrics']['Row'], 'id'>
        Update: Partial<Database['public']['Tables']['perpetual_metrics']['Row']>
      }
    }
  }
} 