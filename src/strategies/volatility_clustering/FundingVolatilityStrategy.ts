import { BaseStrategy, StrategyConfig, StrategyResult } from '../base_strategy';
import { SupabaseClient } from '@supabase/supabase-js';

interface VolatilityClusterConfig extends StrategyConfig {
  parameters: {
    assets: string[];
    lookbackDays: number;
    volatilityThreshold: number;
    clusterMinSize: number;
    stressEventThreshold: number;
  };
}

interface VolatilityCluster {
  startTime: number;
  endTime: number;
  averageVolatility: number;
  maxVolatility: number;
  clusterSize: number;
}

export class FundingVolatilityStrategy extends BaseStrategy {
  private volatilityClusters: Map<string, VolatilityCluster[]> = new Map();
  private rollingVolatility: Map<string, number[]> = new Map();

  constructor(config: VolatilityClusterConfig, supabaseClient: SupabaseClient) {
    super(config, supabaseClient);
  }

  async initialize(): Promise<void> {
    const endDate = new Date();
    const startDate = new Date(endDate.getTime() - (this.parameters.lookbackDays * 24 * 60 * 60 * 1000));

    for (const asset of this.parameters.assets) {
      const fundingRates = await this.fetchHistoricalData('funding_rates', startDate, endDate);
      
      // Calculate rolling volatility
      const volatilities = this.calculateRollingVolatility(fundingRates);
      this.rollingVolatility.set(asset, volatilities);

      // Identify volatility clusters
      const clusters = this.identifyVolatilityClusters(
        volatilities,
        fundingRates.map(r => new Date(r.timestamp).getTime())
      );
      this.volatilityClusters.set(asset, clusters);
    }
  }

  async execute(): Promise<StrategyResult> {
    const currentTimestamp = Date.now();
    const signals: Record<string, any> = {};
    const metrics: Record<string, number> = {};

    for (const asset of this.parameters.assets) {
      // Get recent funding rates
      const recentRates = await this.fetchHistoricalData(
        'funding_rates',
        new Date(currentTimestamp - (24 * 60 * 60 * 1000)), // Last 24 hours
        new Date(currentTimestamp)
      );

      const currentVolatility = this.calculateCurrentVolatility(recentRates);
      const clusters = this.volatilityClusters.get(asset) || [];
      const activeCluster = this.findActiveCluster(clusters, currentTimestamp);
      
      signals[asset] = {
        currentVolatility,
        isInVolatilityCluster: !!activeCluster,
        clusterMetrics: activeCluster ? {
          duration: activeCluster.endTime - activeCluster.startTime,
          intensity: activeCluster.averageVolatility,
          peak: activeCluster.maxVolatility
        } : null,
        stressLevel: this.calculateStressLevel(currentVolatility, activeCluster)
      };

      metrics[`${asset}_current_volatility`] = currentVolatility;
      metrics[`${asset}_stress_level`] = signals[asset].stressLevel;
      if (activeCluster) {
        metrics[`${asset}_cluster_intensity`] = activeCluster.averageVolatility;
        metrics[`${asset}_cluster_duration`] = activeCluster.endTime - activeCluster.startTime;
      }
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
    this.volatilityClusters.clear();
    this.rollingVolatility.clear();
  }

  private calculateRollingVolatility(rates: any[]): number[] {
    const window = 24; // 24-hour rolling window
    const volatilities: number[] = [];
    
    for (let i = window; i < rates.length; i++) {
      const windowRates = rates.slice(i - window, i).map(r => r.funding_rate);
      const mean = windowRates.reduce((a, b) => a + b, 0) / window;
      const variance = windowRates.reduce((sum, rate) => 
        sum + Math.pow(rate - mean, 2), 0
      ) / window;
      volatilities.push(Math.sqrt(variance));
    }
    
    return volatilities;
  }

  private calculateCurrentVolatility(rates: any[]): number {
    if (rates.length < 2) return 0;
    
    const returns = rates.slice(1).map((rate, i) => 
      rate.funding_rate - rates[i].funding_rate
    );
    
    const mean = returns.reduce((a, b) => a + b, 0) / returns.length;
    const variance = returns.reduce((sum, ret) => 
      sum + Math.pow(ret - mean, 2), 0
    ) / returns.length;
    
    return Math.sqrt(variance);
  }

  private identifyVolatilityClusters(
    volatilities: number[],
    timestamps: number[]
  ): VolatilityCluster[] {
    const clusters: VolatilityCluster[] = [];
    let currentCluster: VolatilityCluster | null = null;

    for (let i = 0; i < volatilities.length; i++) {
      if (volatilities[i] > this.parameters.volatilityThreshold) {
        if (!currentCluster) {
          currentCluster = {
            startTime: timestamps[i],
            endTime: timestamps[i],
            averageVolatility: volatilities[i],
            maxVolatility: volatilities[i],
            clusterSize: 1
          };
        } else {
          currentCluster.endTime = timestamps[i];
          currentCluster.averageVolatility = 
            (currentCluster.averageVolatility * currentCluster.clusterSize + volatilities[i]) /
            (currentCluster.clusterSize + 1);
          currentCluster.maxVolatility = Math.max(currentCluster.maxVolatility, volatilities[i]);
          currentCluster.clusterSize++;
        }
      } else if (currentCluster && currentCluster.clusterSize >= this.parameters.clusterMinSize) {
        clusters.push(currentCluster);
        currentCluster = null;
      } else {
        currentCluster = null;
      }
    }

    if (currentCluster && currentCluster.clusterSize >= this.parameters.clusterMinSize) {
      clusters.push(currentCluster);
    }

    return clusters;
  }

  private findActiveCluster(
    clusters: VolatilityCluster[],
    currentTimestamp: number
  ): VolatilityCluster | null {
    return clusters.find(cluster => 
      currentTimestamp >= cluster.startTime && 
      currentTimestamp <= cluster.endTime
    ) || null;
  }

  private calculateStressLevel(
    currentVolatility: number,
    activeCluster: VolatilityCluster | null
  ): number {
    if (!activeCluster) return currentVolatility / this.parameters.volatilityThreshold;

    const clusterIntensity = activeCluster.averageVolatility / this.parameters.volatilityThreshold;
    const clusterPersistence = Math.min(
      1,
      activeCluster.clusterSize / (this.parameters.clusterMinSize * 2)
    );

    return clusterIntensity * (1 + clusterPersistence);
  }
} 