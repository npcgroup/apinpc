import { BaseStrategy, StrategyConfig, StrategyResult } from '../base_strategy';
import { SupabaseClient } from '@supabase/supabase-js';

interface MarginEfficiencyConfig extends StrategyConfig {
  parameters: {
    assets: string[];
    minMarginRatio: number;
    targetMarginRatio: number;
    rebalanceThreshold: number;
    correlationWindow: number;
    riskLimits: {
      maxLeverage: number;
      maxConcentration: number;
      minDiversification: number;
    };
  };
}

interface AssetMetrics {
  asset: string;
  marginRatio: number;
  leverage: number;
  concentration: number;
  correlations: Map<string, number>;
  volatility: number;
  liquidity: number;
  efficiency: number;
}

interface PortfolioState {
  totalEquity: number;
  usedMargin: number;
  freeMargin: number;
  portfolioMarginRatio: number;
  diversificationScore: number;
  riskScore: number;
  timestamp: number;
}

interface RebalanceRecommendation {
  asset: string;
  currentMargin: number;
  recommendedMargin: number;
  priority: number;
  expectedBenefit: number;
  riskImpact: number;
}

export class CrossMarginEfficiencyStrategy extends BaseStrategy {
  private assetMetrics: Map<string, AssetMetrics> = new Map();
  private portfolioStates: PortfolioState[] = [];
  private correlationMatrix: Map<string, Map<string, number>> = new Map();
  private marginAllocation: Map<string, number> = new Map();

  constructor(config: MarginEfficiencyConfig, supabaseClient: SupabaseClient) {
    super(config, supabaseClient);
  }

  async initialize(): Promise<void> {
    const endDate = new Date();
    const startDate = new Date(
      endDate.getTime() - (24 * 60 * 60 * 1000)
    );

    // Initialize correlation matrix
    await this.initializeCorrelationMatrix(startDate, endDate);

    // Initialize asset metrics
    await this.initializeAssetMetrics(startDate, endDate);

    // Calculate initial portfolio state
    const initialState = await this.calculatePortfolioState();
    this.portfolioStates.push(initialState);
  }

  async execute(): Promise<StrategyResult> {
    const currentTimestamp = Date.now();
    const signals: Record<string, any> = {};
    const metrics: Record<string, number> = {};

    // Update asset metrics
    await this.updateAssetMetrics();

    // Calculate current portfolio state
    const currentState = await this.calculatePortfolioState();
    this.portfolioStates.push(currentState);

    // Generate rebalance recommendations
    const recommendations = this.generateRebalanceRecommendations(currentState);

    // Calculate efficiency scores
    const efficiencyScores = this.calculateEfficiencyScores();

    // Calculate risk metrics
    const riskMetrics = this.calculateRiskMetrics(currentState);

    for (const asset of this.parameters.assets) {
      const assetMetric = this.assetMetrics.get(asset);
      if (!assetMetric) continue;

      const recommendation = recommendations.find(r => r.asset === asset);

      signals[asset] = {
        currentMetrics: {
          marginRatio: assetMetric.marginRatio,
          leverage: assetMetric.leverage,
          efficiency: assetMetric.efficiency
        },
        rebalanceRecommendation: recommendation ? {
          currentMargin: recommendation.currentMargin,
          recommendedMargin: recommendation.recommendedMargin,
          priority: recommendation.priority,
          expectedBenefit: recommendation.expectedBenefit
        } : null,
        correlations: Object.fromEntries(assetMetric.correlations),
        riskMetrics: {
          concentration: assetMetric.concentration,
          volatility: assetMetric.volatility,
          liquidity: assetMetric.liquidity
        }
      };

      metrics[`${asset}_margin_ratio`] = assetMetric.marginRatio;
      metrics[`${asset}_leverage`] = assetMetric.leverage;
      metrics[`${asset}_efficiency`] = assetMetric.efficiency;
      metrics[`${asset}_concentration`] = assetMetric.concentration;
    }

    // Add portfolio-level metrics
    metrics['portfolio_margin_ratio'] = currentState.portfolioMarginRatio;
    metrics['portfolio_diversification'] = currentState.diversificationScore;
    metrics['portfolio_risk_score'] = currentState.riskScore;
    metrics['total_efficiency'] = efficiencyScores.total;
    metrics['margin_efficiency'] = efficiencyScores.margin;
    metrics['risk_efficiency'] = efficiencyScores.risk;

    const result: StrategyResult = {
      timestamp: currentTimestamp,
      signals,
      metrics
    };

    await this.logResult(result);
    return result;
  }

  async cleanup(): Promise<void> {
    this.assetMetrics.clear();
    this.portfolioStates = [];
    this.correlationMatrix.clear();
    this.marginAllocation.clear();
  }

  private async initializeCorrelationMatrix(
    startDate: Date,
    endDate: Date
  ): Promise<void> {
    const returns: Map<string, number[]> = new Map();

    // Fetch price data and calculate returns for each asset
    for (const asset of this.parameters.assets) {
      const prices = await this.fetchHistoricalData(
        `prices_${asset}`,
        startDate,
        endDate
      );

      returns.set(asset, this.calculateReturns(
        prices.map(p => p.price)
      ));
    }

    // Calculate correlations between all asset pairs
    for (const asset1 of this.parameters.assets) {
      const assetCorrelations = new Map<string, number>();
      const returns1 = returns.get(asset1) || [];

      for (const asset2 of this.parameters.assets) {
        const returns2 = returns.get(asset2) || [];
        const correlation = this.calculateCorrelation(returns1, returns2);
        assetCorrelations.set(asset2, correlation);
      }

      this.correlationMatrix.set(asset1, assetCorrelations);
    }
  }

  private async initializeAssetMetrics(
    startDate: Date,
    endDate: Date
  ): Promise<void> {
    for (const asset of this.parameters.assets) {
      const [positions, trades] = await Promise.all([
        this.fetchHistoricalData(
          `positions_${asset}`,
          startDate,
          endDate
        ),
        this.fetchHistoricalData(
          `trades_${asset}`,
          startDate,
          endDate
        )
      ]);

      const metrics = await this.calculateAssetMetrics(
        asset,
        positions,
        trades
      );

      this.assetMetrics.set(asset, metrics);
      this.marginAllocation.set(
        asset,
        positions.reduce((sum, pos) => sum + pos.margin, 0)
      );
    }
  }

  private async updateAssetMetrics(): Promise<void> {
    const endDate = new Date();
    const startDate = new Date(
      endDate.getTime() - (60 * 60 * 1000) // Last hour
    );

    for (const asset of this.parameters.assets) {
      const [positions, trades] = await Promise.all([
        this.fetchHistoricalData(
          `positions_${asset}`,
          startDate,
          endDate
        ),
        this.fetchHistoricalData(
          `trades_${asset}`,
          startDate,
          endDate
        )
      ]);

      const metrics = await this.calculateAssetMetrics(
        asset,
        positions,
        trades
      );

      this.assetMetrics.set(asset, metrics);
    }
  }

  private async calculateAssetMetrics(
    asset: string,
    positions: any[],
    trades: any[]
  ): Promise<AssetMetrics> {
    const totalNotional = positions.reduce(
      (sum, pos) => sum + pos.notionalValue,
      0
    );
    const totalMargin = positions.reduce(
      (sum, pos) => sum + pos.margin,
      0
    );

    const marginRatio = totalNotional > 0 ?
      totalMargin / totalNotional :
      this.parameters.targetMarginRatio;

    const leverage = marginRatio > 0 ? 1 / marginRatio : 0;
    const concentration = totalNotional / this.portfolioStates[0]?.totalEquity || 0;

    // Get correlations with other assets
    const correlations = this.correlationMatrix.get(asset) || new Map();

    // Calculate volatility and liquidity
    const volatility = this.calculateVolatility(
      trades.map(t => t.price)
    );
    const liquidity = this.calculateLiquidityScore(trades);

    // Calculate efficiency score
    const efficiency = this.calculateAssetEfficiency(
      marginRatio,
      leverage,
      concentration,
      volatility,
      liquidity
    );

    return {
      asset,
      marginRatio,
      leverage,
      concentration,
      correlations,
      volatility,
      liquidity,
      efficiency
    };
  }

  private async calculatePortfolioState(): Promise<PortfolioState> {
    const positions = Array.from(this.assetMetrics.values());
    const totalEquity = positions.reduce(
      (sum, pos) => sum + pos.marginRatio * (1 / pos.leverage),
      0
    );

    const usedMargin = positions.reduce(
      (sum, pos) => sum + (1 / pos.leverage),
      0
    );

    const freeMargin = totalEquity - usedMargin;
    const portfolioMarginRatio = totalEquity > 0 ?
      usedMargin / totalEquity :
      this.parameters.targetMarginRatio;

    const diversificationScore = this.calculateDiversificationScore(positions);
    const riskScore = this.calculatePortfolioRiskScore(positions);

    return {
      totalEquity,
      usedMargin,
      freeMargin,
      portfolioMarginRatio,
      diversificationScore,
      riskScore,
      timestamp: Date.now()
    };
  }

  private calculateReturns(prices: number[]): number[] {
    return prices.slice(1).map((price, i) =>
      Math.log(price / prices[i])
    );
  }

  private calculateCorrelation(
    returns1: number[],
    returns2: number[]
  ): number {
    if (returns1.length !== returns2.length || returns1.length < 2) {
      return 0;
    }

    const mean1 = returns1.reduce((a, b) => a + b, 0) / returns1.length;
    const mean2 = returns2.reduce((a, b) => a + b, 0) / returns2.length;

    const variance1 = returns1.reduce(
      (sum, ret) => sum + Math.pow(ret - mean1, 2),
      0
    ) / returns1.length;

    const variance2 = returns2.reduce(
      (sum, ret) => sum + Math.pow(ret - mean2, 2),
      0
    ) / returns2.length;

    const covariance = returns1.reduce(
      (sum, ret, i) => sum + (ret - mean1) * (returns2[i] - mean2),
      0
    ) / returns1.length;

    return covariance / Math.sqrt(variance1 * variance2);
  }

  private calculateVolatility(prices: number[]): number {
    const returns = this.calculateReturns(prices);
    const mean = returns.reduce((a, b) => a + b, 0) / returns.length;
    const variance = returns.reduce(
      (sum, ret) => sum + Math.pow(ret - mean, 2),
      0
    ) / returns.length;

    return Math.sqrt(variance * 365 * 24); // Annualized
  }

  private calculateLiquidityScore(trades: any[]): number {
    if (trades.length === 0) return 0;

    const volumes = trades.map(t => t.volume);
    const spreads = trades.map(t => t.spread);

    const avgVolume = volumes.reduce((a, b) => a + b, 0) / volumes.length;
    const avgSpread = spreads.reduce((a, b) => a + b, 0) / spreads.length;

    return avgVolume / (1 + avgSpread);
  }

  private calculateAssetEfficiency(
    marginRatio: number,
    leverage: number,
    concentration: number,
    volatility: number,
    liquidity: number
  ): number {
    // Calculate margin efficiency
    const marginEfficiency = Math.min(
      1,
      marginRatio / this.parameters.targetMarginRatio
    );

    // Calculate risk efficiency
    const leverageEfficiency = Math.max(
      0,
      1 - leverage / this.parameters.riskLimits.maxLeverage
    );
    const concentrationEfficiency = Math.max(
      0,
      1 - concentration / this.parameters.riskLimits.maxConcentration
    );

    // Calculate market efficiency
    const volatilityFactor = 1 / (1 + volatility);
    const liquidityFactor = Math.min(1, liquidity / 1000000); // Normalize to $1M

    // Combine factors with weights
    return (
      marginEfficiency * 0.3 +
      leverageEfficiency * 0.2 +
      concentrationEfficiency * 0.2 +
      volatilityFactor * 0.15 +
      liquidityFactor * 0.15
    );
  }

  private calculateDiversificationScore(positions: AssetMetrics[]): number {
    if (positions.length === 0) return 0;

    // Calculate effective number of positions using HHI
    const concentrations = positions.map(p => p.concentration);
    const hhi = concentrations.reduce(
      (sum, conc) => sum + conc * conc,
      0
    );

    const effectiveCount = 1 / hhi;
    return Math.min(
      1,
      effectiveCount / this.parameters.riskLimits.minDiversification
    );
  }

  private calculatePortfolioRiskScore(positions: AssetMetrics[]): number {
    if (positions.length === 0) return 0;

    // Calculate leverage risk
    const maxLeverage = Math.max(...positions.map(p => p.leverage));
    const leverageRisk = maxLeverage / this.parameters.riskLimits.maxLeverage;

    // Calculate concentration risk
    const maxConcentration = Math.max(...positions.map(p => p.concentration));
    const concentrationRisk = maxConcentration / 
      this.parameters.riskLimits.maxConcentration;

    // Calculate correlation risk
    const correlationRisk = positions.reduce(
      (sum, pos) => sum + this.calculateCorrelationRisk(pos),
      0
    ) / positions.length;

    return (leverageRisk + concentrationRisk + correlationRisk) / 3;
  }

  private calculateCorrelationRisk(position: AssetMetrics): number {
    const correlations = Array.from(position.correlations.values());
    return correlations.reduce((sum, corr) => sum + Math.abs(corr), 0) /
      correlations.length;
  }

  private generateRebalanceRecommendations(
    currentState: PortfolioState
  ): RebalanceRecommendation[] {
    const recommendations: RebalanceRecommendation[] = [];

    for (const [asset, metrics] of this.assetMetrics.entries()) {
      const currentMargin = this.marginAllocation.get(asset) || 0;
      const optimalMargin = this.calculateOptimalMargin(
        metrics,
        currentState
      );

      const marginDiff = Math.abs(optimalMargin - currentMargin);
      if (marginDiff / currentMargin > this.parameters.rebalanceThreshold) {
        const priority = this.calculateRebalancePriority(
          metrics,
          marginDiff,
          currentState
        );

        const expectedBenefit = this.calculateRebalanceBenefit(
          metrics,
          optimalMargin,
          currentState
        );

        const riskImpact = this.calculateRebalanceRiskImpact(
          metrics,
          optimalMargin,
          currentState
        );

        recommendations.push({
          asset,
          currentMargin,
          recommendedMargin: optimalMargin,
          priority,
          expectedBenefit,
          riskImpact
        });
      }
    }

    return recommendations.sort((a, b) => b.priority - a.priority);
  }

  private calculateOptimalMargin(
    position: AssetMetrics,
    portfolioState: PortfolioState
  ): number {
    const targetRatio = this.parameters.targetMarginRatio;
    const currentRatio = position.marginRatio;
    const volatilityAdjustment = 1 + position.volatility;
    const liquidityAdjustment = Math.min(1, position.liquidity / 1000000);

    // Calculate base optimal margin
    let optimalMargin = (1 / position.leverage) * (
      targetRatio / currentRatio
    ) * volatilityAdjustment * liquidityAdjustment;

    // Adjust for portfolio constraints
    optimalMargin = Math.min(
      optimalMargin,
      portfolioState.totalEquity * this.parameters.riskLimits.maxConcentration
    );

    return optimalMargin;
  }

  private calculateRebalancePriority(
    position: AssetMetrics,
    marginDiff: number,
    portfolioState: PortfolioState
  ): number {
    // Calculate efficiency improvement potential
    const efficiencyGap = 1 - position.efficiency;

    // Calculate risk reduction potential
    const riskGap = Math.max(
      0,
      position.leverage / this.parameters.riskLimits.maxLeverage - 0.8
    );

    // Calculate margin utilization improvement
    const marginGap = Math.abs(
      position.marginRatio - this.parameters.targetMarginRatio
    );

    return (
      efficiencyGap * 0.4 +
      riskGap * 0.3 +
      marginGap * 0.3
    ) * (marginDiff / portfolioState.totalEquity);
  }

  private calculateRebalanceBenefit(
    position: AssetMetrics,
    optimalMargin: number,
    portfolioState: PortfolioState
  ): number {
    // Calculate efficiency improvement
    const efficiencyImprovement = this.estimateEfficiencyImprovement(
      position,
      optimalMargin
    );

    // Calculate risk reduction
    const riskReduction = this.estimateRiskReduction(
      position,
      optimalMargin,
      portfolioState
    );

    // Calculate capital efficiency improvement
    const currentUtilization = position.marginRatio;
    const targetUtilization = this.parameters.targetMarginRatio;
    const utilizationImprovement = Math.max(
      0,
      1 - Math.abs(targetUtilization - currentUtilization) /
        targetUtilization
    );

    return (
      efficiencyImprovement * 0.4 +
      riskReduction * 0.4 +
      utilizationImprovement * 0.2
    );
  }

  private calculateRebalanceRiskImpact(
    position: AssetMetrics,
    optimalMargin: number,
    portfolioState: PortfolioState
  ): number {
    // Calculate leverage impact
    const newLeverage = 1 / (optimalMargin / position.leverage);
    const leverageImpact = Math.max(
      0,
      newLeverage / this.parameters.riskLimits.maxLeverage - 0.8
    );

    // Calculate concentration impact
    const newConcentration = optimalMargin / portfolioState.totalEquity;
    const concentrationImpact = Math.max(
      0,
      newConcentration / this.parameters.riskLimits.maxConcentration - 0.8
    );

    // Calculate correlation impact
    const correlationImpact = this.calculateCorrelationRisk(position);

    return (leverageImpact + concentrationImpact + correlationImpact) / 3;
  }

  private estimateEfficiencyImprovement(
    position: AssetMetrics,
    optimalMargin: number
  ): number {
    const newMarginRatio = optimalMargin / (1 / position.leverage);
    const newEfficiency = this.calculateAssetEfficiency(
      newMarginRatio,
      1 / newMarginRatio,
      position.concentration,
      position.volatility,
      position.liquidity
    );

    return Math.max(0, newEfficiency - position.efficiency);
  }

  private estimateRiskReduction(
    position: AssetMetrics,
    optimalMargin: number,
    portfolioState: PortfolioState
  ): number {
    const currentRisk = this.calculatePortfolioRiskScore([position]);
    
    const adjustedPosition = {
      ...position,
      marginRatio: optimalMargin / (1 / position.leverage),
      leverage: 1 / (optimalMargin / (1 / position.leverage))
    };

    const newRisk = this.calculatePortfolioRiskScore([adjustedPosition]);
    return Math.max(0, currentRisk - newRisk);
  }

  private calculateEfficiencyScores(): {
    total: number;
    margin: number;
    risk: number;
    diversification: number;
  } {
    const positions = Array.from(this.assetMetrics.values());
    if (positions.length === 0) {
      return {
        total: 0,
        margin: 0,
        risk: 0,
        diversification: 0
      };
    }

    // Calculate margin efficiency
    const marginEfficiency = positions.reduce(
      (sum, pos) => sum + Math.min(
        1,
        pos.marginRatio / this.parameters.targetMarginRatio
      ),
      0
    ) / positions.length;

    // Calculate risk efficiency
    const riskEfficiency = 1 - this.calculatePortfolioRiskScore(positions);

    // Calculate diversification efficiency
    const diversificationEfficiency = this.calculateDiversificationScore(
      positions
    );

    // Calculate total efficiency
    const totalEfficiency = (
      marginEfficiency * 0.4 +
      riskEfficiency * 0.3 +
      diversificationEfficiency * 0.3
    );

    return {
      total: totalEfficiency,
      margin: marginEfficiency,
      risk: riskEfficiency,
      diversification: diversificationEfficiency
    };
  }

  private calculateRiskMetrics(portfolioState: PortfolioState): {
    leverageUtilization: number;
    concentrationRisk: number;
    correlationRisk: number;
    marginBuffer: number;
  } {
    const positions = Array.from(this.assetMetrics.values());

    // Calculate leverage utilization
    const avgLeverage = positions.reduce(
      (sum, pos) => sum + pos.leverage,
      0
    ) / positions.length;
    const leverageUtilization = avgLeverage / this.parameters.riskLimits.maxLeverage;

    // Calculate concentration risk
    const maxConcentration = Math.max(...positions.map(p => p.concentration));
    const concentrationRisk = maxConcentration / 
      this.parameters.riskLimits.maxConcentration;

    // Calculate correlation risk
    const correlationRisk = positions.reduce(
      (sum, pos) => sum + this.calculateCorrelationRisk(pos),
      0
    ) / positions.length;

    // Calculate margin buffer
    const marginBuffer = Math.max(
      0,
      1 - portfolioState.usedMargin / portfolioState.totalEquity
    );

    return {
      leverageUtilization,
      concentrationRisk,
      correlationRisk,
      marginBuffer
    };
  }
} 