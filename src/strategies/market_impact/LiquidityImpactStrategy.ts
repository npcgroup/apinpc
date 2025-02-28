import { BaseStrategy, StrategyConfig, StrategyResult } from '../base_strategy';
import { SupabaseClient } from '@supabase/supabase-js';

interface LiquidityImpactConfig extends StrategyConfig {
  parameters: {
    assets: string[];
    tradeQuintiles: number[];
    impactWindowMinutes: number;
    minTradeCount: number;
    significanceLevel: number;
  };
}

interface TradeImpact {
  size: number;
  priceImpact: number;
  timestamp: number;
}

export class LiquidityImpactStrategy extends BaseStrategy {
  private impactCoefficients: Map<string, Map<number, number>> = new Map();
  private recentTrades: Map<string, TradeImpact[]> = new Map();

  constructor(config: LiquidityImpactConfig, supabaseClient: SupabaseClient) {
    super(config, supabaseClient);
  }

  async initialize(): Promise<void> {
    const endDate = new Date();
    const startDate = new Date(endDate.getTime() - (24 * 60 * 60 * 1000)); // Last 24 hours

    for (const asset of this.parameters.assets) {
      const trades = await this.fetchHistoricalData('trades', startDate, endDate);
      
      if (trades.length < this.parameters.minTradeCount) {
        throw new Error(`Insufficient trade data for ${asset}`);
      }

      // Group trades by size quintiles
      const sortedSizes = trades.map(t => t.size).sort((a, b) => a - b);
      const quintileThresholds = this.parameters.tradeQuintiles.map((q: number) => 
        sortedSizes[Math.floor(q * sortedSizes.length)]
      );

      // Calculate impact coefficients for each quintile
      const coefficients = new Map<number, number>();
      for (let i = 0; i < quintileThresholds.length; i++) {
        const quintileTrades = trades.filter(t => 
          t.size >= (quintileThresholds[i-1] || 0) && 
          t.size < (quintileThresholds[i] || Infinity)
        );
        coefficients.set(i, this.calculateImpactCoefficient(quintileTrades));
      }

      this.impactCoefficients.set(asset, coefficients);
      this.recentTrades.set(asset, this.processTradeImpacts(trades));
    }
  }

  async execute(): Promise<StrategyResult> {
    const currentTimestamp = Date.now();
    const signals: Record<string, any> = {};
    const metrics: Record<string, number> = {};

    for (const asset of this.parameters.assets) {
      // Fetch recent trades
      const recentTrades = await this.fetchHistoricalData(
        'trades',
        new Date(currentTimestamp - (this.parameters.impactWindowMinutes * 60 * 1000)),
        new Date(currentTimestamp)
      );

      const impacts = this.processTradeImpacts(recentTrades);
      const marketImpactMetrics = this.calculateMarketImpactMetrics(asset, impacts);
      
      signals[asset] = {
        currentImpactRegime: this.determineImpactRegime(marketImpactMetrics),
        recentLargeTradeCount: impacts.filter(i => i.size > this.parameters.tradeQuintiles[3]).length,
        averageImpact: marketImpactMetrics.averageImpact
      };

      metrics[`${asset}_avg_impact`] = marketImpactMetrics.averageImpact;
      metrics[`${asset}_impact_volatility`] = marketImpactMetrics.impactVolatility;
      metrics[`${asset}_liquidity_score`] = marketImpactMetrics.liquidityScore;
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
    this.impactCoefficients.clear();
    this.recentTrades.clear();
  }

  private processTradeImpacts(trades: any[]): TradeImpact[] {
    return trades.map(trade => ({
      size: trade.size,
      priceImpact: this.calculatePriceImpact(trade),
      timestamp: new Date(trade.timestamp).getTime()
    }));
  }

  private calculatePriceImpact(trade: any): number {
    // Simple implementation - can be enhanced with more sophisticated models
    const midPrice = (trade.best_bid + trade.best_ask) / 2;
    return Math.abs(trade.price - midPrice) / midPrice;
  }

  private calculateImpactCoefficient(trades: any[]): number {
    if (trades.length === 0) return 0;
    
    // Calculate impact coefficient using linear regression
    const sizes = trades.map(t => t.size);
    const impacts = trades.map(t => this.calculatePriceImpact(t));
    
    const meanSize = sizes.reduce((a, b) => a + b, 0) / sizes.length;
    const meanImpact = impacts.reduce((a, b) => a + b, 0) / impacts.length;
    
    const numerator = sizes.reduce((sum, size, i) => 
      sum + (size - meanSize) * (impacts[i] - meanImpact), 0
    );
    
    const denominator = sizes.reduce((sum, size) => 
      sum + Math.pow(size - meanSize, 2), 0
    );
    
    return denominator === 0 ? 0 : numerator / denominator;
  }

  private calculateMarketImpactMetrics(asset: string, impacts: TradeImpact[]) {
    const averageImpact = impacts.reduce((sum, imp) => sum + imp.priceImpact, 0) / impacts.length;
    
    const impactVolatility = Math.sqrt(
      impacts.reduce((sum, imp) => 
        sum + Math.pow(imp.priceImpact - averageImpact, 2), 0
      ) / impacts.length
    );

    const coefficients = this.impactCoefficients.get(asset);
    const liquidityScore = coefficients ? 
      1 / (Array.from(coefficients.values()).reduce((a, b) => a + b, 0) / coefficients.size) : 
      0;

    return {
      averageImpact,
      impactVolatility,
      liquidityScore
    };
  }

  private determineImpactRegime(metrics: { 
    averageImpact: number; 
    impactVolatility: number; 
    liquidityScore: number; 
  }): string {
    if (metrics.liquidityScore < 0.3) return 'low_liquidity';
    if (metrics.impactVolatility > 0.02) return 'volatile';
    if (metrics.averageImpact > 0.01) return 'high_impact';
    return 'stable';
  }
} 