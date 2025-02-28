import { BaseStrategy, StrategyConfig, StrategyResult } from '../base_strategy';
import { SupabaseClient } from '@supabase/supabase-js';

interface ArbitrageConfig extends StrategyConfig {
  parameters: {
    assets: string[];
    exchanges: string[];
    minProfitThreshold: number;
    maxSlippageTolerance: number;
    minLiquidityRequired: number;
    rebalanceThreshold: number;
  };
}

interface ArbitrageOpportunity {
  asset: string;
  longExchange: string;
  shortExchange: string;
  fundingDifferential: number;
  estimatedProfit: number;
  requiredCapital: number;
  liquidityScore: number;
  timestamp: number;
}

export class CrossExchangeArbitrageStrategy extends BaseStrategy {
  private opportunities: Map<string, ArbitrageOpportunity[]> = new Map();
  private liquidityScores: Map<string, Map<string, number>> = new Map();

  constructor(config: ArbitrageConfig, supabaseClient: SupabaseClient) {
    super(config, supabaseClient);
  }

  async initialize(): Promise<void> {
    const endDate = new Date();
    const startDate = new Date(endDate.getTime() - (24 * 60 * 60 * 1000));

    // Initialize liquidity scores for each exchange-asset pair
    for (const asset of this.parameters.assets) {
      const assetLiquidity = new Map<string, number>();
      
      for (const exchange of this.parameters.exchanges) {
        const orderbooks = await this.fetchHistoricalData(
          `orderbooks_${exchange}_${asset}`,
          startDate,
          endDate
        );
        
        assetLiquidity.set(exchange, this.calculateLiquidityScore(orderbooks));
      }
      
      this.liquidityScores.set(asset, assetLiquidity);
    }
  }

  async execute(): Promise<StrategyResult> {
    const currentTimestamp = Date.now();
    const signals: Record<string, any> = {};
    const metrics: Record<string, number> = {};

    for (const asset of this.parameters.assets) {
      const opportunities = await this.findArbitrageOpportunities(asset, currentTimestamp);
      this.opportunities.set(asset, opportunities);

      const bestOpportunity = this.selectBestOpportunity(opportunities);
      
      signals[asset] = {
        hasViableArbitrage: !!bestOpportunity,
        bestOpportunity: bestOpportunity ? {
          longExchange: bestOpportunity.longExchange,
          shortExchange: bestOpportunity.shortExchange,
          expectedReturn: bestOpportunity.estimatedProfit / bestOpportunity.requiredCapital,
          fundingDifferential: bestOpportunity.fundingDifferential
        } : null,
        marketEfficiency: this.calculateMarketEfficiency(opportunities)
      };

      if (bestOpportunity) {
        metrics[`${asset}_arb_profit`] = bestOpportunity.estimatedProfit;
        metrics[`${asset}_funding_spread`] = bestOpportunity.fundingDifferential;
        metrics[`${asset}_liquidity_score`] = bestOpportunity.liquidityScore;
      }
      
      metrics[`${asset}_market_efficiency`] = signals[asset].marketEfficiency;
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
    this.opportunities.clear();
    this.liquidityScores.clear();
  }

  private async findArbitrageOpportunities(
    asset: string,
    timestamp: number
  ): Promise<ArbitrageOpportunity[]> {
    const opportunities: ArbitrageOpportunity[] = [];
    const exchanges = this.parameters.exchanges;

    // Fetch current funding rates for all exchanges
    const fundingRates = new Map<string, number>();
    for (const exchange of exchanges) {
      const rates = await this.fetchHistoricalData(
        `funding_rates_${exchange}_${asset}`,
        new Date(timestamp - (5 * 60 * 1000)), // Last 5 minutes
        new Date(timestamp)
      );
      
      if (rates.length > 0) {
        fundingRates.set(exchange, rates[rates.length - 1].funding_rate);
      }
    }

    // Find opportunities between exchange pairs
    for (let i = 0; i < exchanges.length; i++) {
      for (let j = i + 1; j < exchanges.length; j++) {
        const exchange1 = exchanges[i];
        const exchange2 = exchanges[j];
        
        const rate1 = fundingRates.get(exchange1);
        const rate2 = fundingRates.get(exchange2);
        
        if (rate1 === undefined || rate2 === undefined) continue;
        
        const differential = rate2 - rate1;
        const absSpread = Math.abs(differential);
        
        if (absSpread > this.parameters.minProfitThreshold) {
          const longExchange = differential > 0 ? exchange1 : exchange2;
          const shortExchange = differential > 0 ? exchange2 : exchange1;
          
          const liquidityScore = Math.min(
            this.liquidityScores.get(asset)?.get(longExchange) || 0,
            this.liquidityScores.get(asset)?.get(shortExchange) || 0
          );

          if (liquidityScore >= this.parameters.minLiquidityRequired) {
            opportunities.push({
              asset,
              longExchange,
              shortExchange,
              fundingDifferential: absSpread,
              estimatedProfit: this.estimateArbitrageProfitability(
                absSpread,
                liquidityScore
              ),
              requiredCapital: this.calculateRequiredCapital(
                asset,
                longExchange,
                shortExchange
              ),
              liquidityScore,
              timestamp
            });
          }
        }
      }
    }

    return opportunities;
  }

  private calculateLiquidityScore(orderbooks: any[]): number {
    if (orderbooks.length === 0) return 0;
    
    // Calculate average depth and tightness of the orderbook
    const depths = orderbooks.map(ob => {
      const bidDepth = ob.bids.reduce((sum: number, [_, size]: number[]) => sum + size, 0);
      const askDepth = ob.asks.reduce((sum: number, [_, size]: number[]) => sum + size, 0);
      return (bidDepth + askDepth) / 2;
    });

    const spreads = orderbooks.map(ob => {
      const bestBid = Math.max(...ob.bids.map(([price]: number[]) => price));
      const bestAsk = Math.min(...ob.asks.map(([price]: number[]) => price));
      return (bestAsk - bestBid) / ((bestAsk + bestBid) / 2);
    });

    const avgDepth = depths.reduce((a, b) => a + b, 0) / depths.length;
    const avgSpread = spreads.reduce((a, b) => a + b, 0) / spreads.length;
    
    // Normalize and combine metrics
    return (avgDepth / this.parameters.minLiquidityRequired) * (1 - avgSpread);
  }

  private estimateArbitrageProfitability(
    fundingDifferential: number,
    liquidityScore: number
  ): number {
    // Adjust raw funding differential by liquidity and slippage factors
    const slippageAdjustment = 1 - (1 - liquidityScore) * this.parameters.maxSlippageTolerance;
    return fundingDifferential * slippageAdjustment;
  }

  private calculateRequiredCapital(
    asset: string,
    longExchange: string,
    shortExchange: string
  ): number {
    // Simple implementation - can be enhanced with actual margin requirements
    const baseCapital = 1000; // Base capital requirement
    const marginMultiplier = 2; // Additional margin safety factor
    return baseCapital * marginMultiplier;
  }

  private selectBestOpportunity(
    opportunities: ArbitrageOpportunity[]
  ): ArbitrageOpportunity | null {
    if (opportunities.length === 0) return null;
    
    // Sort by risk-adjusted return (profit / required capital * liquidity score)
    return opportunities.reduce((best, current) => {
      const bestScore = best.estimatedProfit / best.requiredCapital * best.liquidityScore;
      const currentScore = current.estimatedProfit / current.requiredCapital * current.liquidityScore;
      return currentScore > bestScore ? current : best;
    });
  }

  private calculateMarketEfficiency(opportunities: ArbitrageOpportunity[]): number {
    if (opportunities.length === 0) return 1; // Perfectly efficient

    // Calculate average profit potential relative to threshold
    const avgProfitPotential = opportunities.reduce(
      (sum, opp) => sum + opp.estimatedProfit / this.parameters.minProfitThreshold,
      0
    ) / opportunities.length;

    // Efficiency decreases as profit potential increases
    return 1 / (1 + avgProfitPotential);
  }
} 