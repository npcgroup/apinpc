import { Layout } from 'plotly.js';

export interface FundingRate {
  symbol: string;
  exchange: string;
  funding_rate: number;
  predicted_rate: number;
  rate_diff: number;
  time_to_funding: number;
  direction: 'long' | 'short' | 'neutral';
  annualized_rate: number;
  opportunity_score: number;
  mark_price: number;
  next_funding_time?: Date;
  spread?: number;
}

export interface FundingStats {
  timestamp: string;
  total_markets: number;
  binance_markets: number;
  hl_markets: number;
  hourly_rate: number;
  eight_hour_rate: number;
  daily_rate: number;
}

interface PlotlyChart {
  data: any[];
  layout: Partial<Layout>;
}

export interface VisualizationData {
  opportunity_scatter: PlotlyChart;
  arb_scatter: PlotlyChart;
  exchange_comparison: PlotlyChart;
  funding_heatmap: PlotlyChart;
  top_opportunities: FundingRate[];
} 