export interface Database {
  public: {
    Tables: {
      perpetual_metrics: {
        Row: {
          id: number
          symbol: string
          timestamp: string
          funding_rate: number
          perp_volume_24h: number
          open_interest: number
          mark_price: number
          spot_price: number
          spot_volume_24h: number
          liquidity: number
          market_cap: number
          total_supply: number
          price_change_24h: number
          txns_24h: number
          created_at: string
          updated_at: string
        }
        Insert: Omit<Database['public']['Tables']['perpetual_metrics']['Row'], 'id' | 'created_at' | 'updated_at'>
        Update: Partial<Database['public']['Tables']['perpetual_metrics']['Insert']>
      }
    }
  }
} 