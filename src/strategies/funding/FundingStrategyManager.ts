import { createClient, SupabaseClient } from '@supabase/supabase-js';
import { FundingRateData, StrategySignal, MarketTrend } from './types';

export class FundingStrategyManager {
  private supabase: SupabaseClient;
  private assets: string[];
  private exchanges: string[];

  constructor(supabaseUrl: string, supabaseKey: string) {
    this.supabase = createClient(supabaseUrl, supabaseKey);
    this.assets = ['BTC', 'ETH', 'SOL', 'ARB', 'OP'];
    this.exchanges = ['binance', 'hyperliquid', 'bybit'];
  }

  async getFundingData(lookbackHours: number = 24): Promise<FundingRateData[]> {
    const { data, error } = await this.supabase
      .from('funding_market_snapshots')
      .select('*')
      .gte('created_at', new Date(Date.now() - lookbackHours * 60 * 60 * 1000).toISOString())
      .order('created_at', { ascending: false });

    if (error) throw error;
    return data;
  }

  async analyzeSentiment(): Promise<Map<string, StrategySignal>> {
    const fundingData = await this.getFundingData();
    const sentiment = new Map<string, StrategySignal>();

    for (const asset of this.assets) {
      const assetData = fundingData.filter(d => d.symbol.startsWith(asset));
      const avgFundingRate = this.calculateAverageFundingRate(assetData);
      const volatility = this.calculateFundingVolatility(assetData);
      
      sentiment.set(asset, {
        asset,
        signal: this.determineSentimentSignal(avgFundingRate, volatility),
        strength: Math.abs(avgFundingRate) / volatility,
        fundingRate: avgFundingRate,
        timestamp: new Date().toISOString()
      });
    }

    return sentiment;
  }

  async analyzeTrendDivergence(): Promise<Map<string, MarketTrend>> {
    const fundingData = await this.getFundingData(48); // 48 hours for trend analysis
    const trends = new Map<string, MarketTrend>();

    for (const asset of this.assets) {
      const assetData = fundingData.filter(d => d.symbol.startsWith(asset));
      const priceData = await this.getPriceData(asset);
      
      const fundingTrend = this.calculateFundingTrend(assetData);
      const priceTrend = this.calculatePriceTrend(priceData);
      
      trends.set(asset, {
        asset,
        fundingTrend,
        priceTrend,
        divergence: this.calculateDivergence(fundingTrend, priceTrend),
        confidence: this.calculateTrendConfidence(assetData, priceData)
      });
    }

    return trends;
  }

  private calculateAverageFundingRate(data: FundingRateData[]): number {
    return data.reduce((acc, curr) => acc + curr.funding_rate, 0) / data.length;
  }

  private calculateFundingVolatility(data: FundingRateData[]): number {
    const mean = this.calculateAverageFundingRate(data);
    const squaredDiffs = data.map(d => Math.pow(d.funding_rate - mean, 2));
    return Math.sqrt(squaredDiffs.reduce((acc, curr) => acc + curr, 0) / data.length);
  }

  private determineSentimentSignal(fundingRate: number, volatility: number): 'bullish' | 'bearish' | 'neutral' {
    const normalizedRate = fundingRate / volatility;
    if (normalizedRate > 1) return 'bullish';
    if (normalizedRate < -1) return 'bearish';
    return 'neutral';
  }

  // Additional helper methods...
} 