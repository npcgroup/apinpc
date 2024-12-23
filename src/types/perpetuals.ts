export interface PerpetualMetrics {
  symbol: string;
  timestamp: string;
  funding_rate: number;
  perp_volume_24h: number;
  open_interest: number;
  mark_price: number;
  spot_price: number;
  spot_volume_24h: number;
  liquidity: number;
  market_cap: number;
  total_supply: number;
  price_change_24h: number;
  txns_24h: number;
  holder_count?: number;
}

export const TRACKED_PERP_TOKENS = [
  'POPCAT',
  'WIF',
  'GOAT',
  'PNUT',
  'CHILLGUY',
  'MOODENG',
  'MEW',
  'BRETT'
] as const;

export type TrackedPerpToken = typeof TRACKED_PERP_TOKENS[number]; 