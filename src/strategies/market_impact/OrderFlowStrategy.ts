import { BaseStrategy, StrategyConfig, StrategyResult } from '../base_strategy';
import { SupabaseClient } from '@supabase/supabase-js';

interface OrderFlowConfig extends StrategyConfig {
  parameters: {
    assets: string[];
    windowSizeMinutes: number;
    toxicityThreshold: number;
    minOrderSize: number;
    volumeOutlierThreshold: number;
    priceImpactThreshold: number;
  };
}

interface OrderFlowMetrics {
  timestamp: number;
  orderCount: number;
  totalVolume: number;
  buyVolume: number;
  sellVolume: number;
  toxicityScore: number;
  volumeImbalance: number;
  priceImpact: number;
}

interface ToxicFlowPattern {
  startTime: number;
  endTime: number;
  direction: 'buy' | 'sell';
  averageSize: number;
  priceImpact: number;
  confidence: number;
}

export class OrderFlowStrategy extends BaseStrategy {
  private flowMetrics: Map<string, OrderFlowMetrics[]> = new Map();
  private toxicPatterns: Map<string, ToxicFlowPattern[]> = new Map();
  private historicalImbalances: Map<string, number[]> = new Map();

  constructor(config: OrderFlowConfig, supabaseClient: SupabaseClient) {
    super(config, supabaseClient);
  }

  async initialize(): Promise<void> {
    const endDate = new Date();
    const startDate = new Date(
      endDate.getTime() - (24 * 60 * 60 * 1000) // Last 24 hours
    );

    for (const asset of this.parameters.assets) {
      // Fetch and analyze historical order flow
      const orderFlow = await this.fetchHistoricalData(
        `order_flow_${asset}`,
        startDate,
        endDate
      );

      const metrics = this.calculateFlowMetrics(orderFlow);
      this.flowMetrics.set(asset, metrics);

      // Identify toxic flow patterns
      const patterns = this.identifyToxicPatterns(metrics);
      this.toxicPatterns.set(asset, patterns);

      // Store historical imbalances
      const imbalances = metrics.map(m => m.volumeImbalance);
      this.historicalImbalances.set(asset, imbalances);
    }
  }

  async execute(): Promise<StrategyResult> {
    const currentTimestamp = Date.now();
    const signals: Record<string, any> = {};
    const metrics: Record<string, number> = {};

    for (const asset of this.parameters.assets) {
      // Analyze recent order flow
      const recentFlow = await this.analyzeRecentFlow(asset, currentTimestamp);
      const toxicFlow = this.detectToxicFlow(recentFlow);
      
      signals[asset] = {
        currentMetrics: {
          orderCount: recentFlow.orderCount,
          volumeImbalance: recentFlow.volumeImbalance,
          toxicityScore: recentFlow.toxicityScore
        },
        toxicFlow: toxicFlow ? {
          direction: toxicFlow.direction,
          size: toxicFlow.averageSize,
          impact: toxicFlow.priceImpact,
          confidence: toxicFlow.confidence
        } : null,
        flowState: this.determineFlowState(recentFlow),
        warnings: this.generateWarnings(recentFlow, toxicFlow)
      };

      metrics[`${asset}_order_count`] = recentFlow.orderCount;
      metrics[`${asset}_volume_imbalance`] = recentFlow.volumeImbalance;
      metrics[`${asset}_toxicity_score`] = recentFlow.toxicityScore;
      metrics[`${asset}_price_impact`] = recentFlow.priceImpact;
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
    this.flowMetrics.clear();
    this.toxicPatterns.clear();
    this.historicalImbalances.clear();
  }

  private calculateFlowMetrics(orderFlow: any[]): OrderFlowMetrics[] {
    const metrics: OrderFlowMetrics[] = [];
    const windowSize = this.parameters.windowSizeMinutes * 60 * 1000;
    let windowStart = 0;

    while (windowStart < orderFlow.length) {
      const windowEnd = this.findWindowEnd(
        orderFlow,
        windowStart,
        windowSize
      );

      const windowOrders = orderFlow.slice(windowStart, windowEnd);
      if (windowOrders.length === 0) break;

      const buyOrders = windowOrders.filter(o => o.side === 'buy');
      const sellOrders = windowOrders.filter(o => o.side === 'sell');

      const buyVolume = this.sumOrderVolume(buyOrders);
      const sellVolume = this.sumOrderVolume(sellOrders);
      const totalVolume = buyVolume + sellVolume;

      const volumeImbalance = totalVolume > 0 ? 
        (buyVolume - sellVolume) / totalVolume : 0;

      const priceImpact = this.calculatePriceImpact(windowOrders);
      const toxicityScore = this.calculateToxicityScore(
        windowOrders,
        volumeImbalance,
        priceImpact
      );

      metrics.push({
        timestamp: new Date(windowOrders[0].timestamp).getTime(),
        orderCount: windowOrders.length,
        totalVolume,
        buyVolume,
        sellVolume,
        toxicityScore,
        volumeImbalance,
        priceImpact
      });

      windowStart = windowEnd;
    }

    return metrics;
  }

  private findWindowEnd(
    orderFlow: any[],
    start: number,
    windowSize: number
  ): number {
    const startTime = new Date(orderFlow[start].timestamp).getTime();
    let end = start;

    while (end < orderFlow.length) {
      const currentTime = new Date(orderFlow[end].timestamp).getTime();
      if (currentTime - startTime > windowSize) break;
      end++;
    }

    return end;
  }

  private sumOrderVolume(orders: any[]): number {
    return orders.reduce((sum, order) => sum + order.size * order.price, 0);
  }

  private calculatePriceImpact(orders: any[]): number {
    if (orders.length < 2) return 0;

    const startPrice = orders[0].price;
    const endPrice = orders[orders.length - 1].price;
    return Math.abs(endPrice - startPrice) / startPrice;
  }

  private calculateToxicityScore(
    orders: any[],
    volumeImbalance: number,
    priceImpact: number
  ): number {
    // Combine multiple factors to determine toxicity
    const imbalanceScore = Math.abs(volumeImbalance);
    const impactScore = priceImpact / this.parameters.priceImpactThreshold;
    const sizeScore = this.calculateSizeScore(orders);

    return Math.min(1, (
      imbalanceScore * 0.4 +
      impactScore * 0.4 +
      sizeScore * 0.2
    ));
  }

  private calculateSizeScore(orders: any[]): number {
    const avgSize = orders.reduce((sum, o) => sum + o.size, 0) / orders.length;
    return Math.min(1, avgSize / this.parameters.minOrderSize);
  }

  private identifyToxicPatterns(metrics: OrderFlowMetrics[]): ToxicFlowPattern[] {
    const patterns: ToxicFlowPattern[] = [];
    let currentPattern: ToxicFlowPattern | null = null;

    for (const metric of metrics) {
      if (metric.toxicityScore >= this.parameters.toxicityThreshold) {
        if (!currentPattern) {
          currentPattern = {
            startTime: metric.timestamp,
            endTime: metric.timestamp,
            direction: metric.volumeImbalance > 0 ? 'buy' : 'sell',
            averageSize: metric.totalVolume / metric.orderCount,
            priceImpact: metric.priceImpact,
            confidence: metric.toxicityScore
          };
        } else {
          currentPattern.endTime = metric.timestamp;
          currentPattern.priceImpact += metric.priceImpact;
          currentPattern.confidence = Math.max(
            currentPattern.confidence,
            metric.toxicityScore
          );
        }
      } else if (currentPattern) {
        patterns.push(currentPattern);
        currentPattern = null;
      }
    }

    if (currentPattern) {
      patterns.push(currentPattern);
    }

    return patterns;
  }

  private async analyzeRecentFlow(
    asset: string,
    currentTimestamp: number
  ): Promise<OrderFlowMetrics> {
    const windowStart = new Date(
      currentTimestamp - (this.parameters.windowSizeMinutes * 60 * 1000)
    );
    const windowEnd = new Date(currentTimestamp);

    const recentOrders = await this.fetchHistoricalData(
      `order_flow_${asset}`,
      windowStart,
      windowEnd
    );

    const metrics = this.calculateFlowMetrics([recentOrders]);
    return metrics[0] || {
      timestamp: currentTimestamp,
      orderCount: 0,
      totalVolume: 0,
      buyVolume: 0,
      sellVolume: 0,
      toxicityScore: 0,
      volumeImbalance: 0,
      priceImpact: 0
    };
  }

  private detectToxicFlow(
    currentMetrics: OrderFlowMetrics
  ): ToxicFlowPattern | null {
    if (currentMetrics.toxicityScore < this.parameters.toxicityThreshold) {
      return null;
    }

    return {
      startTime: currentMetrics.timestamp,
      endTime: currentMetrics.timestamp,
      direction: currentMetrics.volumeImbalance > 0 ? 'buy' : 'sell',
      averageSize: currentMetrics.totalVolume / currentMetrics.orderCount,
      priceImpact: currentMetrics.priceImpact,
      confidence: currentMetrics.toxicityScore
    };
  }

  private determineFlowState(metrics: OrderFlowMetrics): string {
    if (metrics.toxicityScore >= this.parameters.toxicityThreshold) {
      return 'toxic';
    }

    if (Math.abs(metrics.volumeImbalance) >= this.parameters.volumeOutlierThreshold) {
      return 'imbalanced';
    }

    if (metrics.priceImpact >= this.parameters.priceImpactThreshold) {
      return 'high_impact';
    }

    return 'normal';
  }

  private generateWarnings(
    metrics: OrderFlowMetrics,
    toxicFlow: ToxicFlowPattern | null
  ): string[] {
    const warnings: string[] = [];

    if (toxicFlow) {
      warnings.push(`toxic_flow_detected_${toxicFlow.direction}`);
    }

    if (Math.abs(metrics.volumeImbalance) >= this.parameters.volumeOutlierThreshold) {
      warnings.push(`significant_imbalance_${metrics.volumeImbalance > 0 ? 'buy' : 'sell'}`);
    }

    if (metrics.priceImpact >= this.parameters.priceImpactThreshold) {
      warnings.push('high_price_impact');
    }

    return warnings;
  }
} 