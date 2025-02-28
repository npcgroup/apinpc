import { BaseStrategy, StrategyConfig, StrategyResult } from '../base_strategy';
import { SupabaseClient } from '@supabase/supabase-js';

interface LiquidationCascadeConfig extends StrategyConfig {
  parameters: {
    assets: string[];
    lookbackPeriodHours: number;
    minCascadeSize: number;
    priceImpactThreshold: number;
    liquidationThreshold: number;
    riskWindowMinutes: number;
  };
}

interface LiquidationEvent {
  asset: string;
  timestamp: number;
  size: number;
  price: number;
  priceImpact: number;
  isTriggered: boolean;
}

interface CascadePattern {
  startTime: number;
  endTime: number;
  totalSize: number;
  maxPriceImpact: number;
  events: LiquidationEvent[];
  triggerPrice: number;
}

export class LiquidationCascadeStrategy extends BaseStrategy {
  private cascadePatterns: Map<string, CascadePattern[]> = new Map();
  private riskPositions: Map<string, any[]> = new Map();
  private priceHistory: Map<string, number[]> = new Map();

  constructor(config: LiquidationCascadeConfig, supabaseClient: SupabaseClient) {
    super(config, supabaseClient);
  }

  async initialize(): Promise<void> {
    const endDate = new Date();
    const startDate = new Date(
      endDate.getTime() - (this.parameters.lookbackPeriodHours * 60 * 60 * 1000)
    );

    for (const asset of this.parameters.assets) {
      // Fetch historical liquidations and price data
      const liquidations = await this.fetchHistoricalData(
        `liquidations_${asset}`,
        startDate,
        endDate
      );

      const prices = await this.fetchHistoricalData(
        `prices_${asset}`,
        startDate,
        endDate
      );

      // Identify historical cascade patterns
      const patterns = this.identifyCascadePatterns(liquidations, prices);
      this.cascadePatterns.set(asset, patterns);

      // Store price history for analysis
      this.priceHistory.set(
        asset,
        prices.map(p => p.price)
      );
    }
  }

  async execute(): Promise<StrategyResult> {
    const currentTimestamp = Date.now();
    const signals: Record<string, any> = {};
    const metrics: Record<string, number> = {};

    for (const asset of this.parameters.assets) {
      // Analyze current at-risk positions
      const riskPositions = await this.analyzeRiskPositions(asset, currentTimestamp);
      this.riskPositions.set(asset, riskPositions);

      // Detect potential cascade triggers
      const cascadeRisk = this.assessCascadeRisk(
        asset,
        riskPositions,
        currentTimestamp
      );

      signals[asset] = {
        atRiskPositions: riskPositions.map(pos => ({
          size: pos.size,
          liquidationPrice: pos.liquidationPrice,
          riskScore: pos.riskScore
        })),
        cascadeRisk: {
          probability: cascadeRisk.probability,
          potentialImpact: cascadeRisk.impact,
          triggerPrice: cascadeRisk.triggerPrice,
          timeWindow: cascadeRisk.timeWindow
        },
        warnings: this.generateWarnings(cascadeRisk)
      };

      metrics[`${asset}_at_risk_positions`] = riskPositions.length;
      metrics[`${asset}_cascade_probability`] = cascadeRisk.probability;
      metrics[`${asset}_potential_impact`] = cascadeRisk.impact;
      metrics[`${asset}_risk_concentration`] = this.calculateRiskConcentration(riskPositions);
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
    this.cascadePatterns.clear();
    this.riskPositions.clear();
    this.priceHistory.clear();
  }

  private identifyCascadePatterns(
    liquidations: any[],
    prices: any[]
  ): CascadePattern[] {
    const patterns: CascadePattern[] = [];
    let currentPattern: CascadePattern | null = null;
    const cascadeWindow = 15 * 60 * 1000; // 15 minutes

    for (let i = 0; i < liquidations.length; i++) {
      const event = this.createLiquidationEvent(liquidations[i], prices);

      if (event.priceImpact >= this.parameters.priceImpactThreshold) {
        if (!currentPattern) {
          currentPattern = {
            startTime: event.timestamp,
            endTime: event.timestamp,
            totalSize: event.size,
            maxPriceImpact: event.priceImpact,
            events: [event],
            triggerPrice: event.price
          };
        } else if (event.timestamp - currentPattern.endTime <= cascadeWindow) {
          currentPattern.endTime = event.timestamp;
          currentPattern.totalSize += event.size;
          currentPattern.maxPriceImpact = Math.max(
            currentPattern.maxPriceImpact,
            event.priceImpact
          );
          currentPattern.events.push(event);
        } else {
          if (this.isSignificantCascade(currentPattern)) {
            patterns.push(currentPattern);
          }
          currentPattern = null;
        }
      }
    }

    if (currentPattern && this.isSignificantCascade(currentPattern)) {
      patterns.push(currentPattern);
    }

    return patterns;
  }

  private createLiquidationEvent(
    liquidation: any,
    prices: any[]
  ): LiquidationEvent {
    const priceBeforeIndex = this.findClosestPriceIndex(
      prices,
      liquidation.timestamp,
      true
    );
    const priceAfterIndex = this.findClosestPriceIndex(
      prices,
      liquidation.timestamp,
      false
    );

    const priceImpact = priceAfterIndex >= 0 && priceBeforeIndex >= 0 ?
      Math.abs(
        prices[priceAfterIndex].price - prices[priceBeforeIndex].price
      ) / prices[priceBeforeIndex].price :
      0;

    return {
      asset: liquidation.asset,
      timestamp: new Date(liquidation.timestamp).getTime(),
      size: liquidation.size,
      price: liquidation.price,
      priceImpact,
      isTriggered: liquidation.isTriggered || false
    };
  }

  private findClosestPriceIndex(
    prices: any[],
    timestamp: string,
    before: boolean
  ): number {
    const targetTime = new Date(timestamp).getTime();
    let closest = -1;
    let minDiff = Infinity;

    for (let i = 0; i < prices.length; i++) {
      const priceTime = new Date(prices[i].timestamp).getTime();
      const diff = Math.abs(priceTime - targetTime);

      if (
        (before && priceTime <= targetTime || !before && priceTime >= targetTime) &&
        diff < minDiff
      ) {
        minDiff = diff;
        closest = i;
      }
    }

    return closest;
  }

  private isSignificantCascade(pattern: CascadePattern): boolean {
    return pattern.events.length >= this.parameters.minCascadeSize &&
           pattern.maxPriceImpact >= this.parameters.priceImpactThreshold;
  }

  private async analyzeRiskPositions(
    asset: string,
    currentTimestamp: number
  ): Promise<any[]> {
    const positions = await this.fetchHistoricalData(
      `positions_${asset}`,
      new Date(currentTimestamp - (5 * 60 * 1000)), // Last 5 minutes
      new Date(currentTimestamp)
    );

    return positions
      .filter(pos => this.isPositionAtRisk(pos))
      .map(pos => ({
        ...pos,
        riskScore: this.calculatePositionRiskScore(pos)
      }))
      .sort((a, b) => b.riskScore - a.riskScore);
  }

  private isPositionAtRisk(position: any): boolean {
    const marginRatio = position.margin / position.notionalValue;
    return marginRatio <= this.parameters.liquidationThreshold * 1.5;
  }

  private calculatePositionRiskScore(position: any): number {
    const marginRatio = position.margin / position.notionalValue;
    const buffer = marginRatio - this.parameters.liquidationThreshold;
    const sizeFactor = position.notionalValue / 1000000; // Normalize by $1M

    return Math.min(
      1,
      (1 / (1 + Math.max(0, buffer))) * Math.sqrt(sizeFactor)
    );
  }

  private assessCascadeRisk(
    asset: string,
    riskPositions: any[],
    currentTimestamp: number
  ): {
    probability: number;
    impact: number;
    triggerPrice: number;
    timeWindow: number;
  } {
    if (riskPositions.length === 0) {
      return {
        probability: 0,
        impact: 0,
        triggerPrice: 0,
        timeWindow: 0
      };
    }

    // Sort positions by liquidation price
    const sortedPositions = [...riskPositions].sort(
      (a, b) => b.liquidationPrice - a.liquidationPrice
    );

    // Find price levels with concentrated liquidations
    const clusters = this.findLiquidationClusters(sortedPositions);
    const historicalPatterns = this.cascadePatterns.get(asset) || [];

    // Calculate cascade probability and impact
    const probability = this.calculateCascadeProbability(
      clusters,
      historicalPatterns
    );

    const impact = this.estimateCascadeImpact(
      clusters,
      historicalPatterns
    );

    // Find the most likely trigger price
    const triggerCluster = clusters.reduce((a, b) =>
      a.totalSize > b.totalSize ? a : b
    );

    return {
      probability,
      impact,
      triggerPrice: triggerCluster.price,
      timeWindow: this.parameters.riskWindowMinutes * 60 * 1000
    };
  }

  private findLiquidationClusters(positions: any[]): any[] {
    const clusters: any[] = [];
    let currentCluster = null;
    const priceThreshold = 0.01; // 1% price difference threshold

    for (const position of positions) {
      if (!currentCluster) {
        currentCluster = {
          price: position.liquidationPrice,
          positions: [position],
          totalSize: position.notionalValue
        };
      } else if (
        Math.abs(position.liquidationPrice - currentCluster.price) / currentCluster.price
        <= priceThreshold
      ) {
        currentCluster.positions.push(position);
        currentCluster.totalSize += position.notionalValue;
      } else {
        clusters.push(currentCluster);
        currentCluster = null;
      }
    }

    if (currentCluster) {
      clusters.push(currentCluster);
    }

    return clusters;
  }

  private calculateCascadeProbability(
    clusters: any[],
    historicalPatterns: CascadePattern[]
  ): number {
    if (clusters.length === 0 || historicalPatterns.length === 0) return 0;

    // Calculate size similarity with historical patterns
    const avgHistoricalSize = historicalPatterns.reduce(
      (sum, pattern) => sum + pattern.totalSize,
      0
    ) / historicalPatterns.length;

    const currentSize = clusters.reduce(
      (sum, cluster) => sum + cluster.totalSize,
      0
    );

    const sizeSimilarity = Math.min(
      1,
      currentSize / avgHistoricalSize
    );

    // Calculate concentration similarity
    const historicalConcentration = this.calculateAverageConcentration(
      historicalPatterns
    );
    const currentConcentration = this.calculateClusterConcentration(clusters);

    const concentrationSimilarity = 1 - Math.abs(
      historicalConcentration - currentConcentration
    );

    // Combine factors
    return Math.min(
      1,
      (sizeSimilarity * 0.6 + concentrationSimilarity * 0.4) *
      (clusters.length / this.parameters.minCascadeSize)
    );
  }

  private calculateAverageConcentration(patterns: CascadePattern[]): number {
    if (patterns.length === 0) return 0;

    return patterns.reduce((sum, pattern) => {
      const timeWindow = pattern.endTime - pattern.startTime;
      return sum + (pattern.totalSize / timeWindow);
    }, 0) / patterns.length;
  }

  private calculateClusterConcentration(clusters: any[]): number {
    const totalSize = clusters.reduce(
      (sum, cluster) => sum + cluster.totalSize,
      0
    );
    const maxClusterSize = Math.max(
      ...clusters.map(c => c.totalSize)
    );

    return maxClusterSize / totalSize;
  }

  private estimateCascadeImpact(
    clusters: any[],
    historicalPatterns: CascadePattern[]
  ): number {
    if (clusters.length === 0) return 0;

    // Calculate potential impact based on historical price movements
    const avgHistoricalImpact = historicalPatterns.length > 0 ?
      historicalPatterns.reduce(
        (sum, pattern) => sum + pattern.maxPriceImpact,
        0
      ) / historicalPatterns.length :
      this.parameters.priceImpactThreshold;

    const totalSize = clusters.reduce(
      (sum, cluster) => sum + cluster.totalSize,
      0
    );

    const avgHistoricalSize = historicalPatterns.length > 0 ?
      historicalPatterns.reduce(
        (sum, pattern) => sum + pattern.totalSize,
        0
      ) / historicalPatterns.length :
      totalSize;

    return Math.min(
      1,
      (totalSize / avgHistoricalSize) * avgHistoricalImpact
    );
  }

  private calculateRiskConcentration(positions: any[]): number {
    if (positions.length === 0) return 0;

    const totalSize = positions.reduce(
      (sum, pos) => sum + pos.notionalValue,
      0
    );
    const maxSize = Math.max(...positions.map(p => p.notionalValue));

    return maxSize / totalSize;
  }

  private generateWarnings(cascadeRisk: {
    probability: number;
    impact: number;
    triggerPrice: number;
    timeWindow: number;
  }): string[] {
    const warnings: string[] = [];

    if (cascadeRisk.probability >= 0.7) {
      warnings.push('high_cascade_probability');
    } else if (cascadeRisk.probability >= 0.4) {
      warnings.push('moderate_cascade_probability');
    }

    if (cascadeRisk.impact >= 0.05) {
      warnings.push('severe_impact_potential');
    } else if (cascadeRisk.impact >= 0.02) {
      warnings.push('significant_impact_potential');
    }

    return warnings;
  }
} 