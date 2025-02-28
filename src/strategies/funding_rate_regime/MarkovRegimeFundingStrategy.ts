import { BaseStrategy, StrategyConfig, StrategyResult } from '../base_strategy';
import { SupabaseClient } from '@supabase/supabase-js';

interface MarkovRegimeConfig extends StrategyConfig {
  parameters: {
    lookbackPeriodDays: number;
    minSampleSize: number;
    regimeCount: number;
    confidenceThreshold: number;
    assets: string[];
  };
}

export class MarkovRegimeFundingStrategy extends BaseStrategy {
  private regimeStates: Map<string, number[]> = new Map();
  private transitionMatrix: Map<string, number[][]> = new Map();

  constructor(config: MarkovRegimeConfig, supabaseClient: SupabaseClient) {
    super(config, supabaseClient);
  }

  async initialize(): Promise<void> {
    const endDate = new Date();
    const startDate = new Date(endDate.getTime() - (this.parameters.lookbackPeriodDays * 24 * 60 * 60 * 1000));
    
    for (const asset of this.parameters.assets) {
      const historicalRates = await this.fetchHistoricalData('funding_rates', startDate, endDate);
      if (historicalRates.length < this.parameters.minSampleSize) {
        throw new Error(`Insufficient data for asset ${asset}`);
      }
      
      // Initialize regime states using rate changes
      const rateChanges = this.calculateRateChanges(historicalRates);
      const regimes = this.identifyRegimes(rateChanges);
      this.regimeStates.set(asset, regimes);
      
      // Calculate transition probabilities
      this.transitionMatrix.set(asset, this.calculateTransitionMatrix(regimes));
    }
  }

  async execute(): Promise<StrategyResult> {
    const currentTimestamp = Date.now();
    const signals: Record<string, any> = {};
    const metrics: Record<string, number> = {};

    for (const asset of this.parameters.assets) {
      const recentRates = await this.fetchHistoricalData(
        'funding_rates',
        new Date(currentTimestamp - (24 * 60 * 60 * 1000)), // Last 24 hours
        new Date(currentTimestamp)
      );

      const currentRegime = this.getCurrentRegime(recentRates);
      const nextRegimeProbabilities = this.predictNextRegime(asset, currentRegime);

      signals[asset] = {
        currentRegime,
        predictedRegimes: nextRegimeProbabilities,
        confidence: Math.max(...nextRegimeProbabilities)
      };

      metrics[`${asset}_regime_stability`] = this.calculateRegimeStability(asset);
      metrics[`${asset}_prediction_confidence`] = signals[asset].confidence;
    }

    const result: StrategyResult = {
      timestamp: currentTimestamp,
      signals,
      metrics
    };

    await this.logResult(result);
    return result;
  }

  async cleanup(): Promise<void> {
    // Clear cached data
    this.regimeStates.clear();
    this.transitionMatrix.clear();
  }

  private calculateRateChanges(rates: any[]): number[] {
    return rates
      .map((rate, i) => i === 0 ? 0 : rate.funding_rate - rates[i-1].funding_rate);
  }

  private identifyRegimes(rateChanges: number[]): number[] {
    // Simple regime identification using standard deviation thresholds
    const mean = rateChanges.reduce((a, b) => a + b, 0) / rateChanges.length;
    const stdDev = Math.sqrt(
      rateChanges.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / rateChanges.length
    );

    return rateChanges.map(change => {
      if (change > mean + stdDev) return 2; // High regime
      if (change < mean - stdDev) return 0; // Low regime
      return 1; // Medium regime
    });
  }

  private calculateTransitionMatrix(regimes: number[]): number[][] {
    const matrix = Array(this.parameters.regimeCount)
      .fill(0)
      .map(() => Array(this.parameters.regimeCount).fill(0));

    for (let i = 0; i < regimes.length - 1; i++) {
      const currentRegime = regimes[i];
      const nextRegime = regimes[i + 1];
      matrix[currentRegime][nextRegime]++;
    }

    // Normalize to get probabilities
    return matrix.map(row => {
      const sum = row.reduce((a, b) => a + b, 0);
      return row.map(count => sum === 0 ? 0 : count / sum);
    });
  }

  private getCurrentRegime(recentRates: any[]): number {
    const changes = this.calculateRateChanges(recentRates);
    const regimes = this.identifyRegimes(changes);
    return regimes[regimes.length - 1];
  }

  private predictNextRegime(asset: string, currentRegime: number): number[] {
    const transitionProbs = this.transitionMatrix.get(asset);
    if (!transitionProbs) {
      throw new Error(`No transition matrix found for asset ${asset}`);
    }
    return transitionProbs[currentRegime];
  }

  private calculateRegimeStability(asset: string): number {
    const matrix = this.transitionMatrix.get(asset);
    if (!matrix) return 0;

    // Calculate stability as average probability of staying in same regime
    return matrix.reduce((sum, row, i) => sum + row[i], 0) / matrix.length;
  }
} 