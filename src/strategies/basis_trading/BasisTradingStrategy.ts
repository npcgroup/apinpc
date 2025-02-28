import { BaseStrategy, StrategyConfig, StrategyResult } from '../base_strategy';
import { SupabaseClient } from '@supabase/supabase-js';

interface BasisTradingConfig extends StrategyConfig {
  parameters: {
    assets: string[];
    exchanges: string[];
    minBasisThreshold: number;
    lookbackPeriodHours: number;
    minSpotLiquidity: number;
    minPerpLiquidity: number;
    rebalanceThreshold: number;
  };
}

interface BasisOpportunity {
  asset: string;
  exchange: string;
  basisSpread: number;
  annualizedReturn: number;
  spotPrice: number;
  perpPrice: number;
  spotLiquidity: number;
  perpLiquidity: number;
  timestamp: number;
}

export class BasisTradingStrategy extends BaseStrategy {
  private opportunities: Map<string, BasisOpportunity[]> = new Map();
  private historicalBasis: Map<string, number[]> = new Map();

  constructor(config: BasisTradingConfig, supabaseClient: SupabaseClient) {
    super(config, supabaseClient);
  }

  async initialize(): Promise<void> {
    const endDate = new Date();
    const startDate = new Date(
      endDate.getTime() - (this.parameters.lookbackPeriodHours * 60 * 60 * 1000)
    );

    for (const asset of this.parameters.assets) {
      const basisHistory: number[] = [];
      
      for (const exchange of this.parameters.exchanges) {
        // Fetch historical spot and perp prices
        const spotPrices = await this.fetchHistoricalData(
          `spot_prices_${exchange}_${asset}`,
          startDate,
          endDate
        );
        
        const perpPrices = await this.fetchHistoricalData(
          `perp_prices_${exchange}_${asset}`,
          startDate,
          endDate
        );

        // Calculate historical basis
        const basis = this.calculateHistoricalBasis(spotPrices, perpPrices);
        basisHistory.push(...basis);
      }

      this.historicalBasis.set(asset, basisHistory);
    }
  }

  async execute(): Promise<StrategyResult> {
    const currentTimestamp = Date.now();
    const signals: Record<string, any> = {};
    const metrics: Record<string, number> = {};

    for (const asset of this.parameters.assets) {
      const opportunities = await this.findBasisOpportunities(asset, currentTimestamp);
      this.opportunities.set(asset, opportunities);

      const bestOpportunity = this.selectBestOpportunity(opportunities);
      const basisEfficiency = this.calculateBasisEfficiency(
        asset,
        opportunities,
        this.historicalBasis.get(asset) || []
      );
      
      signals[asset] = {
        hasViableBasisTrade: !!bestOpportunity,
        bestOpportunity: bestOpportunity ? {
          exchange: bestOpportunity.exchange,
          basisSpread: bestOpportunity.basisSpread,
          annualizedReturn: bestOpportunity.annualizedReturn,
          spotPrice: bestOpportunity.spotPrice,
          perpPrice: bestOpportunity.perpPrice
        } : null,
        basisEfficiency,
        marketState: this.determineBasisMarketState(basisEfficiency)
      };

      if (bestOpportunity) {
        metrics[`${asset}_basis_spread`] = bestOpportunity.basisSpread;
        metrics[`${asset}_annualized_return`] = bestOpportunity.annualizedReturn;
        metrics[`${asset}_spot_liquidity`] = bestOpportunity.spotLiquidity;
        metrics[`${asset}_perp_liquidity`] = bestOpportunity.perpLiquidity;
      }
      
      metrics[`${asset}_basis_efficiency`] = basisEfficiency;
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
    this.historicalBasis.clear();
  }

  private calculateHistoricalBasis(
    spotPrices: any[],
    perpPrices: any[]
  ): number[] {
    const basis: number[] = [];
    let spotIndex = 0;
    let perpIndex = 0;

    while (spotIndex < spotPrices.length && perpIndex < perpPrices.length) {
      const spotTime = new Date(spotPrices[spotIndex].timestamp).getTime();
      const perpTime = new Date(perpPrices[perpIndex].timestamp).getTime();

      if (Math.abs(spotTime - perpTime) < 1000) { // Within 1 second
        const basisSpread = (perpPrices[perpIndex].price - spotPrices[spotIndex].price) / 
          spotPrices[spotIndex].price;
        basis.push(basisSpread);
        spotIndex++;
        perpIndex++;
      } else if (spotTime < perpTime) {
        spotIndex++;
      } else {
        perpIndex++;
      }
    }

    return basis;
  }

  private async findBasisOpportunities(
    asset: string,
    timestamp: number
  ): Promise<BasisOpportunity[]> {
    const opportunities: BasisOpportunity[] = [];
    const timeWindow = 5 * 60 * 1000; // 5 minutes

    for (const exchange of this.parameters.exchanges) {
      // Fetch recent spot and perp prices
      const spotPrices = await this.fetchHistoricalData(
        `spot_prices_${exchange}_${asset}`,
        new Date(timestamp - timeWindow),
        new Date(timestamp)
      );

      const perpPrices = await this.fetchHistoricalData(
        `perp_prices_${exchange}_${asset}`,
        new Date(timestamp - timeWindow),
        new Date(timestamp)
      );

      if (spotPrices.length === 0 || perpPrices.length === 0) continue;

      const latestSpot = spotPrices[spotPrices.length - 1];
      const latestPerp = perpPrices[perpPrices.length - 1];
      
      const basisSpread = (latestPerp.price - latestSpot.price) / latestSpot.price;
      
      if (Math.abs(basisSpread) > this.parameters.minBasisThreshold) {
        // Calculate liquidity scores
        const spotLiquidity = this.calculateSpotLiquidity(spotPrices);
        const perpLiquidity = this.calculatePerpLiquidity(perpPrices);

        if (spotLiquidity >= this.parameters.minSpotLiquidity && 
            perpLiquidity >= this.parameters.minPerpLiquidity) {
          opportunities.push({
            asset,
            exchange,
            basisSpread,
            annualizedReturn: this.calculateAnnualizedReturn(basisSpread),
            spotPrice: latestSpot.price,
            perpPrice: latestPerp.price,
            spotLiquidity,
            perpLiquidity,
            timestamp
          });
        }
      }
    }

    return opportunities;
  }

  private calculateSpotLiquidity(prices: any[]): number {
    // Simple implementation using volume and price volatility
    if (prices.length < 2) return 0;
    
    const volumes = prices.map(p => p.volume);
    const avgVolume = volumes.reduce((a, b) => a + b, 0) / volumes.length;
    
    const returns = prices.slice(1).map((p, i) => 
      Math.abs(p.price - prices[i].price) / prices[i].price
    );
    const volatility = Math.sqrt(
      returns.reduce((sum, ret) => sum + ret * ret, 0) / returns.length
    );

    return avgVolume / (1 + volatility);
  }

  private calculatePerpLiquidity(prices: any[]): number {
    // Similar to spot liquidity but also considers open interest
    const spotLiquidity = this.calculateSpotLiquidity(prices);
    const avgOpenInterest = prices.reduce((sum, p) => sum + p.openInterest, 0) / prices.length;
    
    return spotLiquidity * (1 + avgOpenInterest / 1000000); // Normalize OI by $1M
  }

  private calculateAnnualizedReturn(basisSpread: number): number {
    // Assuming 8-hour funding intervals
    const fundingPeriodsPerYear = (365 * 24) / 8;
    return Math.abs(basisSpread) * fundingPeriodsPerYear;
  }

  private selectBestOpportunity(
    opportunities: BasisOpportunity[]
  ): BasisOpportunity | null {
    if (opportunities.length === 0) return null;

    // Sort by risk-adjusted return (annualized return * liquidity score)
    return opportunities.reduce((best, current) => {
      const bestScore = best.annualizedReturn * 
        Math.min(best.spotLiquidity, best.perpLiquidity);
      const currentScore = current.annualizedReturn * 
        Math.min(current.spotLiquidity, current.perpLiquidity);
      return currentScore > bestScore ? current : best;
    });
  }

  private calculateBasisEfficiency(
    asset: string,
    currentOpportunities: BasisOpportunity[],
    historicalBasis: number[]
  ): number {
    if (historicalBasis.length === 0) return 1;

    // Calculate historical basis volatility
    const meanBasis = historicalBasis.reduce((a, b) => a + b, 0) / historicalBasis.length;
    const basisVolatility = Math.sqrt(
      historicalBasis.reduce((sum, basis) => 
        sum + Math.pow(basis - meanBasis, 2), 0
      ) / historicalBasis.length
    );

    // Calculate current basis deviation
    const currentBasis = currentOpportunities.length > 0
      ? Math.max(...currentOpportunities.map(o => Math.abs(o.basisSpread)))
      : 0;

    // Efficiency decreases with higher volatility and larger current basis
    return 1 / (1 + basisVolatility + Math.abs(currentBasis - meanBasis));
  }

  private determineBasisMarketState(efficiency: number): string {
    if (efficiency > 0.8) return 'efficient';
    if (efficiency > 0.5) return 'moderately_efficient';
    if (efficiency > 0.3) return 'inefficient';
    return 'highly_inefficient';
  }
} 