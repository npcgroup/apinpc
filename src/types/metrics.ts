import { Environment } from './providers';

export interface BaseMetrics {
  id: number;
  asset_id: number;
  environment: Environment;
  timestamp: string;
  source_id: number;
  raw_data?: Record<string, any>;
  created_at: Date;
}

export interface TokenMetrics extends BaseMetrics {
  price: number;
  volume_24h: number;
  market_cap: number;
  total_supply: number;
  holder_count?: number;
}

export interface NFTMetrics extends BaseMetrics {
  floor_price: number;
  volume_24h: number;
  sales_count: number;
  holder_count: number;
  listed_count: number;
}

export interface ProtocolMetrics {
  id: number;
  protocol_id: number;
  environment: Environment;
  timestamp: string;
  tvl: number;
  volume_24h: number;
  unique_users_24h: number;
  transaction_count_24h: number;
  revenue_24h: number;
  source_id: number;
  raw_data?: Record<string, any>;
  created_at: Date;
} 
