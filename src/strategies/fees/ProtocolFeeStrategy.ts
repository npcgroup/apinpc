import { BaseStrategy, StrategyConfig, StrategyResult } from '../base_strategy';
import { SupabaseClient } from '@supabase/supabase-js';

interface FeeConfig extends StrategyConfig {
  parameters: {
    assets: string[];
    feeTypes: {
      trading: {
        min: number;
        max: number;
        step: number;
      };
      funding: {
        min: number;
        max: number;
        step: number;
      };
      liquidation: {
        min: number;
        max: number;
        step: number;
      };
    };
    elasticityWindow: number;
    minRevenueThreshold: number;
    volumeImpactThreshold: number;
    optimizationHorizon: number;
  };
}

interface FeeMetrics {
  tradingFee: number;
  fundingFee: number;
  liquidationFee: number;
  revenue: number;
  volume: number;
  elasticity: number;
  efficiency: number;
}

interface FeeSimulation {
  fees: {
    trading: number;
    funding: number;
    liquidation: number;
  };
  metrics: {
    revenue: number;
    volume: number;
    userCost: number;
    marketQuality: number;
  };
  impact: {
    volumeChange: number;
    revenueChange: number;
    liquidityChange: number;
  };
}

interface OptimizationResult {
  optimalFees: {
    trading: number;
    funding: number;
    liquidation: number;
  };
  expectedMetrics: {
    revenue: number;
    volume: number;
    marketQuality: number;
  };
  confidence: number;
  tradeoffs: {
    revenueVsVolume: number;
    revenueVsQuality: number;
    volumeVsQuality: number;
  };
}

export class ProtocolFeeStrategy extends BaseStrategy {
  private feeMetrics: Map<string, FeeMetrics[]> = new Map();
  private elasticityModels: Map<string, any> = new Map();
  private revenueProjections: Map<string, number[]> = new Map();
  private marketImpact: Map<string, any> = new Map();

  constructor(config: FeeConfig, supabaseClient: SupabaseClient) {
    super(config, supabaseClient);
  }

  async initialize(): Promise<void> {
    const endDate = new Date();
    const startDate = new Date(
      endDate.getTime() - (this.parameters.elasticityWindow * 24 * 60 * 60 * 1000)
    );

    // Initialize fee metrics and elasticity models
    await this.initializeFeeMetrics(startDate, endDate);
    this.buildElasticityModels();

    // Calculate initial market impact
    await this.calculateMarketImpact(startDate, endDate);

    // Generate revenue projections
    this.generateRevenueProjections();
  }

  async execute(): Promise<StrategyResult> {
    const currentTimestamp = Date.now();
    const signals: Record<string, any> = {};
    const metrics: Record<string, number> = {};

    // Update metrics and models
    await this.updateFeeMetrics();
    this.updateElasticityModels();

    // Run fee optimizations
    const optimizations = await this.optimizeFeeStructures();
    const sensitivityAnalysis = this.analyzeSensitivity();
    const recommendations = this.generateRecommendations(optimizations);

    // Generate signals and metrics for each asset
    for (const asset of this.parameters.assets) {
      const assetMetrics = this.feeMetrics.get(asset);
      if (!assetMetrics || assetMetrics.length === 0) continue;

      const currentMetrics = assetMetrics[assetMetrics.length - 1];
      const optimization = optimizations.get(asset);

      signals[asset] = {
        currentMetrics: {
          tradingFee: currentMetrics.tradingFee,
          fundingFee: currentMetrics.fundingFee,
          liquidationFee: currentMetrics.liquidationFee,
          revenue: currentMetrics.revenue,
          elasticity: currentMetrics.elasticity
        },
        optimization: optimization ? {
          optimalFees: optimization.optimalFees,
          expectedMetrics: optimization.expectedMetrics,
          confidence: optimization.confidence
        } : null,
        sensitivity: sensitivityAnalysis.get(asset),
        recommendations: recommendations.get(asset)
      };

      metrics[`${asset}_trading_fee`] = currentMetrics.tradingFee;
      metrics[`${asset}_funding_fee`] = currentMetrics.fundingFee;
      metrics[`${asset}_revenue`] = currentMetrics.revenue;
      metrics[`${asset}_elasticity`] = currentMetrics.elasticity;
      metrics[`${asset}_efficiency`] = currentMetrics.efficiency;
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
    this.feeMetrics.clear();
    this.elasticityModels.clear();
    this.revenueProjections.clear();
    this.marketImpact.clear();
  }

  private async initializeFeeMetrics(
    startDate: Date,
    endDate: Date
  ): Promise<void> {
    for (const asset of this.parameters.assets) {
      const [fees, volumes, revenues] = await Promise.all([
        this.fetchHistoricalData(`fees_${asset}`, startDate, endDate),
        this.fetchHistoricalData(`volumes_${asset}`, startDate, endDate),
        this.fetchHistoricalData(`revenues_${asset}`, startDate, endDate)
      ]);

      const metrics = this.calculateFeeMetrics(fees, volumes, revenues);
      this.feeMetrics.set(asset, metrics);
    }
  }

  private calculateFeeMetrics(
    fees: any[],
    volumes: any[],
    revenues: any[]
  ): FeeMetrics[] {
    return fees.map((fee, i) => ({
      tradingFee: fee.trading,
      fundingFee: fee.funding,
      liquidationFee: fee.liquidation,
      revenue: revenues[i].total,
      volume: volumes[i].total,
      elasticity: this.calculateElasticity(
        fees.slice(Math.max(0, i - 10), i + 1),
        volumes.slice(Math.max(0, i - 10), i + 1)
      ),
      efficiency: this.calculateEfficiency(
        fee,
        volumes[i],
        revenues[i]
      )
    }));
  }

  private calculateElasticity(
    fees: any[],
    volumes: any[]
  ): number {
    if (fees.length < 2) return 0;

    const feeChanges = fees.slice(1).map((fee, i) =>
      (fee.trading - fees[i].trading) / fees[i].trading
    );

    const volumeChanges = volumes.slice(1).map((vol, i) =>
      (vol.total - volumes[i].total) / volumes[i].total
    );

    // Calculate price elasticity of demand
    const avgFeeChange = feeChanges.reduce((a, b) => a + b, 0) / feeChanges.length;
    const avgVolumeChange = volumeChanges.reduce((a, b) => a + b, 0) / volumeChanges.length;

    return avgFeeChange === 0 ? 0 : -(avgVolumeChange / avgFeeChange);
  }

  private calculateEfficiency(
    fees: any,
    volume: any,
    revenue: any
  ): number {
    const theoreticalRevenue = volume.total * (
      fees.trading +
      fees.funding +
      fees.liquidation * volume.liquidations / volume.total
    );

    return revenue.total / theoreticalRevenue;
  }

  private buildElasticityModels(): void {
    for (const [asset, metrics] of this.feeMetrics.entries()) {
      const model = this.buildElasticityModel(metrics);
      this.elasticityModels.set(asset, model);
    }
  }

  private buildElasticityModel(metrics: FeeMetrics[]): any {
    // Simple linear regression model for elasticity
    const x = metrics.map(m => m.tradingFee);
    const y = metrics.map(m => m.volume);

    const n = x.length;
    const sumX = x.reduce((a, b) => a + b, 0);
    const sumY = y.reduce((a, b) => a + b, 0);
    const sumXY = x.reduce((sum, xi, i) => sum + xi * y[i], 0);
    const sumXX = x.reduce((sum, xi) => sum + xi * xi, 0);

    const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
    const intercept = (sumY - slope * sumX) / n;

    return {
      slope,
      intercept,
      elasticity: -slope * (sumX / n) / (sumY / n)
    };
  }

  private async calculateMarketImpact(
    startDate: Date,
    endDate: Date
  ): Promise<void> {
    for (const asset of this.parameters.assets) {
      const [trades, liquidations] = await Promise.all([
        this.fetchHistoricalData(`trades_${asset}`, startDate, endDate),
        this.fetchHistoricalData(`liquidations_${asset}`, startDate, endDate)
      ]);

      this.marketImpact.set(asset, {
        volumeImpact: this.calculateVolumeImpact(trades),
        liquidityImpact: this.calculateLiquidityImpact(trades),
        liquidationImpact: this.calculateLiquidationImpact(liquidations)
      });
    }
  }

  private calculateVolumeImpact(trades: any[]): number {
    const volumes = trades.map(t => t.volume);
    const fees = trades.map(t => t.fee);

    const correlation = this.calculateCorrelation(volumes, fees);
    return -correlation * Math.sqrt(
      this.calculateVariance(volumes) / this.calculateVariance(fees)
    );
  }

  private calculateLiquidityImpact(trades: any[]): number {
    const spreads = trades.map(t => t.spread);
    const fees = trades.map(t => t.fee);

    return this.calculateCorrelation(spreads, fees);
  }

  private calculateLiquidationImpact(liquidations: any[]): number {
    const volumes = liquidations.map(l => l.volume);
    const fees = liquidations.map(l => l.fee);

    return this.calculateCorrelation(volumes, fees);
  }

  private calculateCorrelation(x: number[], y: number[]): number {
    const n = Math.min(x.length, y.length);
    if (n < 2) return 0;

    const meanX = x.reduce((a, b) => a + b, 0) / n;
    const meanY = y.reduce((a, b) => a + b, 0) / n;

    const covariance = x.reduce(
      (sum, xi, i) => sum + (xi - meanX) * (y[i] - meanY),
      0
    ) / n;

    const stdX = Math.sqrt(this.calculateVariance(x));
    const stdY = Math.sqrt(this.calculateVariance(y));

    return covariance / (stdX * stdY);
  }

  private calculateVariance(x: number[]): number {
    const mean = x.reduce((a, b) => a + b, 0) / x.length;
    return x.reduce(
      (sum, xi) => sum + Math.pow(xi - mean, 2),
      0
    ) / x.length;
  }

  private generateRevenueProjections(): void {
    for (const [asset, metrics] of this.feeMetrics.entries()) {
      const model = this.elasticityModels.get(asset);
      if (!model) continue;

      const projections = this.projectRevenue(
        metrics[metrics.length - 1],
        model
      );
      this.revenueProjections.set(asset, projections);
    }
  }

  private projectRevenue(
    currentMetrics: FeeMetrics,
    model: any
  ): number[] {
    const projections: number[] = [];
    const horizon = this.parameters.optimizationHorizon;

    for (let i = 1; i <= horizon; i++) {
      const projectedVolume = model.intercept + model.slope * currentMetrics.tradingFee;
      const projectedRevenue = projectedVolume * currentMetrics.tradingFee;
      projections.push(projectedRevenue);
    }

    return projections;
  }

  private async updateFeeMetrics(): Promise<void> {
    const endDate = new Date();
    const startDate = new Date(
      endDate.getTime() - (24 * 60 * 60 * 1000)
    );

    await this.initializeFeeMetrics(startDate, endDate);
  }

  private updateElasticityModels(): void {
    this.buildElasticityModels();
  }

  private async optimizeFeeStructures(): Promise<Map<string, OptimizationResult>> {
    const results = new Map<string, OptimizationResult>();

    for (const asset of this.parameters.assets) {
      const metrics = this.feeMetrics.get(asset);
      const model = this.elasticityModels.get(asset);
      const impact = this.marketImpact.get(asset);

      if (!metrics || !model || !impact) continue;

      const result = await this.optimizeFees(
        asset,
        metrics[metrics.length - 1],
        model,
        impact
      );
      results.set(asset, result);
    }

    return results;
  }

  private async optimizeFees(
    asset: string,
    currentMetrics: FeeMetrics,
    elasticityModel: any,
    marketImpact: any
  ): Promise<OptimizationResult> {
    const simulations = await this.runFeeSimulations(
      asset,
      currentMetrics,
      elasticityModel
    );

    const optimal = this.findOptimalFees(simulations, marketImpact);
    const confidence = this.calculateOptimizationConfidence(
      optimal,
      simulations,
      currentMetrics
    );

    const tradeoffs = this.analyzeTradeoffs(
      optimal,
      simulations,
      currentMetrics
    );

    return {
      optimalFees: optimal.fees,
      expectedMetrics: optimal.metrics,
      confidence,
      tradeoffs
    };
  }

  private async runFeeSimulations(
    asset: string,
    currentMetrics: FeeMetrics,
    elasticityModel: any
  ): Promise<FeeSimulation[]> {
    const simulations: FeeSimulation[] = [];
    const { trading, funding, liquidation } = this.parameters.feeTypes;

    for (let t = trading.min; t <= trading.max; t += trading.step) {
      for (let f = funding.min; f <= funding.max; f += funding.step) {
        for (let l = liquidation.min; l <= liquidation.max; l += liquidation.step) {
          const simulation = await this.simulateFees(
            asset,
            { trading: t, funding: f, liquidation: l },
            currentMetrics,
            elasticityModel
          );
          simulations.push(simulation);
        }
      }
    }

    return simulations;
  }

  private async simulateFees(
    asset: string,
    fees: { trading: number; funding: number; liquidation: number },
    currentMetrics: FeeMetrics,
    elasticityModel: any
  ): Promise<FeeSimulation> {
    const volumeChange = elasticityModel.slope * (
      fees.trading - currentMetrics.tradingFee
    );
    const projectedVolume = currentMetrics.volume * (1 + volumeChange);

    const revenue = projectedVolume * (
      fees.trading +
      fees.funding +
      fees.liquidation * 0.1 // Assume 10% of volume is liquidations
    );

    const marketQuality = await this.estimateMarketQuality(
      asset,
      fees,
      volumeChange
    );

    return {
      fees,
      metrics: {
        revenue,
        volume: projectedVolume,
        userCost: (fees.trading + fees.funding) * projectedVolume,
        marketQuality
      },
      impact: {
        volumeChange,
        revenueChange: (revenue - currentMetrics.revenue) / currentMetrics.revenue,
        liquidityChange: marketQuality - currentMetrics.efficiency
      }
    };
  }

  private async estimateMarketQuality(
    asset: string,
    fees: { trading: number; funding: number; liquidation: number },
    volumeChange: number
  ): Promise<number> {
    const impact = this.marketImpact.get(asset);
    if (!impact) return 0;

    const liquidityScore = 1 - impact.liquidityImpact * fees.trading;
    const volumeScore = Math.max(0, 1 + volumeChange);
    const stabilityScore = 1 - impact.liquidationImpact * fees.liquidation;

    return (
      liquidityScore * 0.4 +
      volumeScore * 0.3 +
      stabilityScore * 0.3
    );
  }

  private findOptimalFees(
    simulations: FeeSimulation[],
    marketImpact: any
  ): FeeSimulation {
    // Score each simulation based on multiple objectives
    const scoredSimulations = simulations.map(sim => ({
      simulation: sim,
      score: this.calculateSimulationScore(sim, marketImpact)
    }));

    // Return simulation with highest score
    return scoredSimulations.reduce(
      (best, current) => current.score > best.score ? current : best,
      { simulation: simulations[0], score: -Infinity }
    ).simulation;
  }

  private calculateSimulationScore(
    simulation: FeeSimulation,
    marketImpact: any
  ): number {
    const revenueScore = Math.min(
      1,
      simulation.metrics.revenue / this.parameters.minRevenueThreshold
    );

    const volumeScore = Math.max(
      0,
      1 - Math.abs(simulation.impact.volumeChange) / 
        this.parameters.volumeImpactThreshold
    );

    const qualityScore = simulation.metrics.marketQuality;

    const impactScore = 1 - (
      marketImpact.volumeImpact * Math.abs(simulation.impact.volumeChange) +
      marketImpact.liquidityImpact * Math.abs(simulation.impact.liquidityChange)
    );

    return (
      revenueScore * 0.4 +
      volumeScore * 0.2 +
      qualityScore * 0.2 +
      impactScore * 0.2
    );
  }

  private calculateOptimizationConfidence(
    optimal: FeeSimulation,
    simulations: FeeSimulation[],
    currentMetrics: FeeMetrics
  ): number {
    // Calculate confidence based on multiple factors
    const revenueDelta = (optimal.metrics.revenue - currentMetrics.revenue) /
      currentMetrics.revenue;

    const volumeStability = 1 - Math.abs(optimal.impact.volumeChange);
    const qualityImprovement = optimal.metrics.marketQuality - currentMetrics.efficiency;

    const robustness = this.calculateRobustness(optimal, simulations);

    return (
      (1 + Math.max(0, revenueDelta)) * 0.3 +
      volumeStability * 0.3 +
      (1 + Math.max(0, qualityImprovement)) * 0.2 +
      robustness * 0.2
    );
  }

  private calculateRobustness(
    optimal: FeeSimulation,
    simulations: FeeSimulation[]
  ): number {
    // Calculate how many simulations are within 10% of optimal
    const optimalRevenue = optimal.metrics.revenue;
    const nearOptimal = simulations.filter(sim =>
      Math.abs(sim.metrics.revenue - optimalRevenue) / optimalRevenue <= 0.1
    );

    return nearOptimal.length / simulations.length;
  }

  private analyzeTradeoffs(
    optimal: FeeSimulation,
    simulations: FeeSimulation[],
    currentMetrics: FeeMetrics
  ): {
    revenueVsVolume: number;
    revenueVsQuality: number;
    volumeVsQuality: number;
  } {
    const revenueVsVolume = this.calculateTradeoff(
      simulations,
      s => s.metrics.revenue / currentMetrics.revenue,
      s => 1 - Math.abs(s.impact.volumeChange)
    );

    const revenueVsQuality = this.calculateTradeoff(
      simulations,
      s => s.metrics.revenue / currentMetrics.revenue,
      s => s.metrics.marketQuality / currentMetrics.efficiency
    );

    const volumeVsQuality = this.calculateTradeoff(
      simulations,
      s => 1 - Math.abs(s.impact.volumeChange),
      s => s.metrics.marketQuality / currentMetrics.efficiency
    );

    return {
      revenueVsVolume,
      revenueVsQuality,
      volumeVsQuality
    };
  }

  private calculateTradeoff(
    simulations: FeeSimulation[],
    metric1: (s: FeeSimulation) => number,
    metric2: (s: FeeSimulation) => number
  ): number {
    const values1 = simulations.map(metric1);
    const values2 = simulations.map(metric2);

    return -this.calculateCorrelation(values1, values2);
  }

  private analyzeSensitivity(): Map<string, {
    tradingFee: number;
    fundingFee: number;
    liquidationFee: number;
    volumeSensitivity: number;
    revenueSensitivity: number;
  }> {
    const analysis = new Map();

    for (const [asset, metrics] of this.feeMetrics.entries()) {
      if (metrics.length < 2) continue;

      const recent = metrics.slice(-10);
      
      analysis.set(asset, {
        tradingFee: this.calculateFeeSensitivity(
          recent,
          m => m.tradingFee,
          m => m.volume
        ),
        fundingFee: this.calculateFeeSensitivity(
          recent,
          m => m.fundingFee,
          m => m.volume
        ),
        liquidationFee: this.calculateFeeSensitivity(
          recent,
          m => m.liquidationFee,
          m => m.volume
        ),
        volumeSensitivity: this.calculateVolumeSensitivity(recent),
        revenueSensitivity: this.calculateRevenueSensitivity(recent)
      });
    }

    return analysis;
  }

  private calculateFeeSensitivity(
    metrics: FeeMetrics[],
    feeSelector: (m: FeeMetrics) => number,
    impactSelector: (m: FeeMetrics) => number
  ): number {
    const fees = metrics.map(feeSelector);
    const impacts = metrics.map(impactSelector);

    const feeChanges = fees.slice(1).map((f, i) => (f - fees[i]) / fees[i]);
    const impactChanges = impacts.slice(1).map((v, i) => (v - impacts[i]) / impacts[i]);

    return this.calculateCorrelation(feeChanges, impactChanges);
  }

  private calculateVolumeSensitivity(metrics: FeeMetrics[]): number {
    const volumes = metrics.map(m => m.volume);
    const totalFees = metrics.map(m =>
      m.tradingFee + m.fundingFee + m.liquidationFee
    );

    return -this.calculateCorrelation(volumes, totalFees);
  }

  private calculateRevenueSensitivity(metrics: FeeMetrics[]): number {
    const revenues = metrics.map(m => m.revenue);
    const totalFees = metrics.map(m =>
      m.tradingFee + m.fundingFee + m.liquidationFee
    );

    return this.calculateCorrelation(revenues, totalFees);
  }

  private generateRecommendations(
    optimizations: Map<string, OptimizationResult>
  ): Map<string, string[]> {
    const recommendations = new Map<string, string[]>();

    for (const [asset, optimization] of optimizations.entries()) {
      const assetRecommendations: string[] = [];
      const metrics = this.feeMetrics.get(asset);
      if (!metrics || metrics.length === 0) continue;

      const current = metrics[metrics.length - 1];

      // Trading fee recommendations
      if (Math.abs(optimization.optimalFees.trading - current.tradingFee) /
          current.tradingFee > 0.1) {
        assetRecommendations.push(
          `Adjust trading fee from ${(current.tradingFee * 100).toFixed(3)}% to ${
            (optimization.optimalFees.trading * 100).toFixed(3)
          }% to ${
            optimization.optimalFees.trading > current.tradingFee ?
              'increase revenue' : 'improve volume'
          }`
        );
      }

      // Funding fee recommendations
      if (Math.abs(optimization.optimalFees.funding - current.fundingFee) /
          current.fundingFee > 0.1) {
        assetRecommendations.push(
          `Modify funding fee from ${(current.fundingFee * 100).toFixed(3)}% to ${
            (optimization.optimalFees.funding * 100).toFixed(3)
          }% to optimize market efficiency`
        );
      }

      // Liquidation fee recommendations
      if (Math.abs(optimization.optimalFees.liquidation - current.liquidationFee) /
          current.liquidationFee > 0.1) {
        assetRecommendations.push(
          `Update liquidation fee from ${(current.liquidationFee * 100).toFixed(3)}% to ${
            (optimization.optimalFees.liquidation * 100).toFixed(3)
          }% to balance risk and revenue`
        );
      }

      // Market quality recommendations
      if (optimization.expectedMetrics.marketQuality < 0.7) {
        assetRecommendations.push(
          'Consider implementing tiered fee structure to improve market quality'
        );
      }

      // Volume impact recommendations
      if (Math.abs(optimization.tradeoffs.revenueVsVolume) > 0.7) {
        assetRecommendations.push(
          'High revenue-volume tradeoff detected. Consider gradual fee adjustments'
        );
      }

      recommendations.set(asset, assetRecommendations);
    }

    return recommendations;
  }
} 