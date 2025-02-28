import { BaseStrategy, StrategyConfig, StrategyResult } from '../base_strategy';
import { SupabaseClient } from '@supabase/supabase-js';

interface MarginHealthConfig extends StrategyConfig {
  parameters: {
    assets: string[];
    lookbackPeriodHours: number;
    marginThresholds: {
      critical: number;
      warning: number;
      healthy: number;
    };
    volatilityWindowSize: number;
    forecastHorizonMinutes: number;
    confidenceLevel: number;
  };
}

interface PositionHealth {
  asset: string;
  positionId: string;
  currentMarginRatio: number;
  projectedMarginRatio: number;
  volatilityExposure: number;
  healthScore: number;
  riskLevel: string;
  timeToMarginCall: number;
}

interface MarginProjection {
  timestamp: number;
  marginRatio: number;
  confidence: number;
}

export class MarginHealthStrategy extends BaseStrategy {
  private positionHealth: Map<string, PositionHealth[]> = new Map();
  private historicalMargins: Map<string, number[]> = new Map();
  private volatilityEstimates: Map<string, number> = new Map();

  constructor(config: MarginHealthConfig, supabaseClient: SupabaseClient) {
    super(config, supabaseClient);
  }

  async initialize(): Promise<void> {
    const endDate = new Date();
    const startDate = new Date(
      endDate.getTime() - (this.parameters.lookbackPeriodHours * 60 * 60 * 1000)
    );

    for (const asset of this.parameters.assets) {
      // Fetch historical margin data
      const marginData = await this.fetchHistoricalData(
        `margin_data_${asset}`,
        startDate,
        endDate
      );

      // Calculate historical margins and volatility
      const margins = marginData.map(d => d.marginRatio);
      this.historicalMargins.set(asset, margins);
      
      const volatility = this.calculateVolatility(
        margins,
        this.parameters.volatilityWindowSize
      );
      this.volatilityEstimates.set(asset, volatility);
    }
  }

  async execute(): Promise<StrategyResult> {
    const currentTimestamp = Date.now();
    const signals: Record<string, any> = {};
    const metrics: Record<string, number> = {};

    for (const asset of this.parameters.assets) {
      // Analyze current positions
      const positions = await this.fetchHistoricalData(
        `positions_${asset}`,
        new Date(currentTimestamp - (5 * 60 * 1000)), // Last 5 minutes
        new Date(currentTimestamp)
      );

      const healthMetrics = await this.analyzePositionHealth(
        asset,
        positions,
        currentTimestamp
      );
      this.positionHealth.set(asset, healthMetrics);

      const aggregateHealth = this.calculateAggregateHealth(healthMetrics);
      const riskProfiles = this.categorizeRiskProfiles(healthMetrics);
      
      signals[asset] = {
        overallHealthScore: aggregateHealth.score,
        riskDistribution: riskProfiles,
        criticalPositions: healthMetrics
          .filter(h => h.riskLevel === 'critical')
          .map(h => ({
            positionId: h.positionId,
            marginRatio: h.currentMarginRatio,
            timeToMarginCall: h.timeToMarginCall
          })),
        projections: this.generateMarginProjections(
          asset,
          healthMetrics,
          currentTimestamp
        )
      };

      metrics[`${asset}_health_score`] = aggregateHealth.score;
      metrics[`${asset}_critical_positions`] = riskProfiles.critical;
      metrics[`${asset}_warning_positions`] = riskProfiles.warning;
      metrics[`${asset}_healthy_positions`] = riskProfiles.healthy;
      metrics[`${asset}_avg_margin_ratio`] = aggregateHealth.averageMargin;
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
    this.positionHealth.clear();
    this.historicalMargins.clear();
    this.volatilityEstimates.clear();
  }

  private async analyzePositionHealth(
    asset: string,
    positions: any[],
    timestamp: number
  ): Promise<PositionHealth[]> {
    const volatility = this.volatilityEstimates.get(asset) || 0;
    const healthMetrics: PositionHealth[] = [];

    for (const position of positions) {
      const currentRatio = position.margin / position.notionalValue;
      const volExposure = this.calculateVolatilityExposure(position, volatility);
      const projected = this.projectMarginRatio(currentRatio, volExposure);
      
      const healthScore = this.calculateHealthScore(
        currentRatio,
        projected,
        volExposure
      );

      healthMetrics.push({
        asset,
        positionId: position.id,
        currentMarginRatio: currentRatio,
        projectedMarginRatio: projected,
        volatilityExposure: volExposure,
        healthScore,
        riskLevel: this.determineRiskLevel(healthScore),
        timeToMarginCall: this.estimateTimeToMarginCall(
          currentRatio,
          volExposure,
          this.parameters.marginThresholds.critical
        )
      });
    }

    return healthMetrics;
  }

  private calculateVolatility(data: number[], windowSize: number): number {
    if (data.length < windowSize) return 0;

    const returns = data.slice(1).map((value, i) => 
      Math.log(value / data[i])
    );

    const mean = returns.reduce((a, b) => a + b, 0) / returns.length;
    const variance = returns.reduce(
      (sum, ret) => sum + Math.pow(ret - mean, 2),
      0
    ) / returns.length;

    return Math.sqrt(variance);
  }

  private calculateVolatilityExposure(
    position: any,
    assetVolatility: number
  ): number {
    const leverage = position.notionalValue / position.margin;
    return leverage * assetVolatility;
  }

  private projectMarginRatio(
    currentRatio: number,
    volatilityExposure: number
  ): number {
    // Simple projection using volatility exposure
    const impactFactor = 2; // Two standard deviations
    return currentRatio * (1 - impactFactor * volatilityExposure);
  }

  private calculateHealthScore(
    currentRatio: number,
    projectedRatio: number,
    volatilityExposure: number
  ): number {
    const thresholds = this.parameters.marginThresholds;
    
    // Base score from current margin ratio
    let score = currentRatio / thresholds.healthy;
    
    // Penalize for projected deterioration
    if (projectedRatio < currentRatio) {
      score *= projectedRatio / currentRatio;
    }

    // Penalize for high volatility exposure
    score *= 1 / (1 + volatilityExposure);

    return Math.min(1, Math.max(0, score));
  }

  private determineRiskLevel(healthScore: number): string {
    const thresholds = this.parameters.marginThresholds;
    
    if (healthScore < thresholds.critical) return 'critical';
    if (healthScore < thresholds.warning) return 'warning';
    if (healthScore >= thresholds.healthy) return 'healthy';
    return 'moderate';
  }

  private estimateTimeToMarginCall(
    currentRatio: number,
    volatilityExposure: number,
    criticalLevel: number
  ): number {
    if (currentRatio <= criticalLevel) return 0;
    if (volatilityExposure === 0) return Infinity;

    // Estimate time using volatility exposure
    const buffer = currentRatio - criticalLevel;
    return buffer / (volatilityExposure * currentRatio);
  }

  private calculateAggregateHealth(positions: PositionHealth[]): {
    score: number;
    averageMargin: number;
  } {
    if (positions.length === 0) {
      return { score: 1, averageMargin: 0 };
    }

    const totalNotional = positions.reduce((sum, pos) => sum + 1, 0);
    const weightedScore = positions.reduce(
      (sum, pos) => sum + pos.healthScore / totalNotional,
      0
    );

    const avgMargin = positions.reduce(
      (sum, pos) => sum + pos.currentMarginRatio,
      0
    ) / positions.length;

    return {
      score: weightedScore,
      averageMargin: avgMargin
    };
  }

  private categorizeRiskProfiles(positions: PositionHealth[]): {
    critical: number;
    warning: number;
    healthy: number;
  } {
    return positions.reduce(
      (counts, pos) => {
        counts[pos.riskLevel as keyof typeof counts]++;
        return counts;
      },
      { critical: 0, warning: 0, healthy: 0 }
    );
  }

  private generateMarginProjections(
    asset: string,
    positions: PositionHealth[],
    currentTimestamp: number
  ): MarginProjection[] {
    const projections: MarginProjection[] = [];
    const volatility = this.volatilityEstimates.get(asset) || 0;
    const horizonMinutes = this.parameters.forecastHorizonMinutes;
    
    // Generate projections at 5-minute intervals
    for (let minute = 5; minute <= horizonMinutes; minute += 5) {
      const timestamp = currentTimestamp + minute * 60 * 1000;
      
      // Calculate aggregate projected margin ratio
      const projectedRatios = positions.map(pos => {
        const timeScaledVol = volatility * Math.sqrt(minute / 60);
        return this.projectMarginRatio(
          pos.currentMarginRatio,
          pos.volatilityExposure * timeScaledVol
        );
      });

      const avgProjectedRatio = projectedRatios.reduce(
        (sum, ratio) => sum + ratio, 0
      ) / projectedRatios.length;

      // Calculate confidence based on volatility and time horizon
      const timeScaledVol = volatility * Math.sqrt(minute / 60);
      const confidence = Math.exp(-timeScaledVol) * this.parameters.confidenceLevel;

      projections.push({
        timestamp,
        marginRatio: avgProjectedRatio,
        confidence
      });
    }

    return projections;
  }
} 