import { FundingRate, FundingStats, VisualizationData } from '../types/funding';
import { createClient } from '@supabase/supabase-js';
import { DataTransformService } from './dataTransformService';

export class FundingService {
  private supabase;
  
  constructor() {
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
    const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

    if (!supabaseUrl || !supabaseKey) {
      throw new Error(
        'Missing environment variables: NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY must be defined'
      );
    }

    this.supabase = createClient(supabaseUrl, supabaseKey);
  }

  async getPredictedRates(): Promise<{
    rates: FundingRate[];
    directional: any[];
    crossExchange: any[];
    detailed: any[];
  }> {
    try {
      const { data, error } = await this.supabase
        .from('funding_market_snapshots')
        .select('*')
        .order('opportunity_score', { ascending: false });

      if (error) throw error;
      
      // If no data, return empty arrays
      if (!data || data.length === 0) {
        return {
          rates: [],
          directional: [],
          crossExchange: [],
          detailed: []
        };
      }

      const rates = data.map(rate => ({
        symbol: rate.symbol,
        exchange: rate.exchange,
        funding_rate: rate.funding_rate,
        predicted_rate: rate.predicted_rate,
        rate_diff: rate.rate_diff,
        time_to_funding: rate.time_to_funding,
        direction: rate.direction,
        annualized_rate: rate.annualized_rate,
        opportunity_score: rate.opportunity_score,
        mark_price: rate.mark_price,
        suggested_position: rate.suggested_position,
        created_at: new Date(rate.created_at)
      }));

      return {
        rates,
        directional: DataTransformService.processDirectionalOpportunities(rates),
        crossExchange: DataTransformService.processCrossExchangeOpportunities(rates),
        detailed: DataTransformService.processDetailedView(rates)
      };
    } catch (error) {
      console.error('Error fetching funding rates:', error);
      throw error;
    }
  }

  async getLatestStats(): Promise<FundingStats> {
    try {
      const { data, error } = await this.supabase
        .from('funding_statistics')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(1);

      if (error) throw error;

      // If no data, return default stats
      if (!data || data.length === 0) {
        return {
          total_markets: 0,
          binance_markets: 0,
          hl_markets: 0,
          hourly_rate: 0,
          eight_hour_rate: 0,
          daily_rate: 0
        };
      }

      return data[0];
    } catch (error) {
      console.error('Error fetching latest stats:', error);
      // Return default stats on error
      return {
        total_markets: 0,
        binance_markets: 0,
        hl_markets: 0,
        hourly_rate: 0,
        eight_hour_rate: 0,
        daily_rate: 0
      };
    }
  }

  async pushToSupabase(
    rates: FundingRate[],
    stats: FundingStats,
    visualizations: VisualizationData
  ) {
    try {
      if (rates.length > 0) {
        const { error: ratesError } = await this.supabase
          .from('funding_market_snapshots')
          .upsert(
            rates.map(rate => ({
              symbol: rate.symbol,
              exchange: rate.exchange,
              funding_rate: rate.funding_rate,
              predicted_rate: rate.predicted_rate,
              rate_diff: rate.rate_diff || Math.abs(rate.predicted_rate - rate.funding_rate),
              time_to_funding: rate.time_to_funding || 8,
              direction: rate.funding_rate < 0 ? 'Long' : 'Short',
              annualized_rate: rate.annualized_rate,
              opportunity_score: rate.opportunity_score,
              mark_price: rate.mark_price,
              suggested_position: rate.funding_rate < 0 ? 'Long' : 'Short',
              created_at: new Date().toISOString()
            }))
          );

        if (ratesError) throw ratesError;
      }

      const { error: statsError } = await this.supabase
        .from('funding_statistics')
        .upsert({
          total_markets: stats.total_markets,
          binance_markets: stats.binance_markets,
          hl_markets: stats.hl_markets,
          hourly_rate: stats.hourly_rate,
          eight_hour_rate: stats.eight_hour_rate,
          daily_rate: stats.daily_rate,
          created_at: new Date().toISOString()
        });

      if (statsError) throw statsError;

      return true;
    } catch (error) {
      console.error('Error pushing to Supabase:', error);
      throw error;
    }
  }

  async getFundingStats(): Promise<FundingStats> {
    try {
      const { data: rates, error } = await this.supabase
        .from('predicted_funding_rates')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(1000);

      if (error) throw error;

      // Calculate statistics
      const stats = {
        timestamp: new Date().toISOString(),
        total_markets: rates.length,
        binance_markets: rates.filter(r => r.exchange === 'BINANCE').length,
        hl_markets: rates.filter(r => r.exchange === 'HYPERLIQUID').length,
        hourly_rate: this.calculateAverageRate(rates, 1),
        eight_hour_rate: this.calculateAverageRate(rates, 8),
        daily_rate: this.calculateAverageRate(rates, 24)
      };

      return stats;
    } catch (error) {
      console.error('Error fetching funding stats:', error);
      throw error;
    }
  }

  async getHistoricalStats(): Promise<FundingStats[]> {
    try {
      const { data: rates, error } = await this.supabase
        .from('predicted_funding_rates')
        .select('*')
        .order('created_at', { ascending: false });

      if (error) throw error;

      // Group rates by hour and calculate stats for each hour
      const hourlyStats = this.groupByHour(rates).map(hourlyRates => ({
        timestamp: new Date(hourlyRates[0].created_at).toISOString(),
        total_markets: hourlyRates.length,
        binance_markets: hourlyRates.filter(r => r.exchange === 'BINANCE').length,
        hl_markets: hourlyRates.filter(r => r.exchange === 'HYPERLIQUID').length,
        hourly_rate: this.calculateAverageRate(hourlyRates, 1),
        eight_hour_rate: this.calculateAverageRate(hourlyRates, 8),
        daily_rate: this.calculateAverageRate(hourlyRates, 24)
      }));

      return hourlyStats;
    } catch (error) {
      console.error('Error fetching historical stats:', error);
      throw error;
    }
  }

  private calculateAverageRate(rates: FundingRate[], hours: number): number {
    const endTime = new Date();
    const startTime = new Date(endTime.getTime() - hours * 3600000);
    const filteredRates = rates.filter(r => r.created_at >= startTime && r.created_at <= endTime);
    const totalRate = filteredRates.reduce((total, rate) => total + rate.funding_rate, 0);
    return totalRate / filteredRates.length;
  }

  private groupByHour(rates: FundingRate[]): FundingRate[][] {
    const groups: FundingRate[][] = [];
    const endTime = new Date();
    const startTime = new Date(endTime.getTime() - 3600000);

    let currentGroup: FundingRate[] = [];
    for (const rate of rates) {
      if (rate.created_at >= startTime && rate.created_at <= endTime) {
        currentGroup.push(rate);
      } else {
        if (currentGroup.length > 0) {
          groups.push(currentGroup);
          currentGroup = [];
        }
        currentGroup.push(rate);
        startTime = new Date(rate.created_at.getTime() - 3600000);
        endTime = new Date(rate.created_at.getTime() + 3600000);
      }
    }

    if (currentGroup.length > 0) {
      groups.push(currentGroup);
    }

    return groups;
  }
} 