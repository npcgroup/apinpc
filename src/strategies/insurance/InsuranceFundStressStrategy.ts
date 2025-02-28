import { BaseStrategy, StrategyConfig, StrategyResult } from '../base_strategy';
import { SupabaseClient } from '@supabase/supabase-js';

interface InsuranceFundConfig extends StrategyConfig {
  parameters: {
    assets: string[];
    stressScenarios: {
      volatilityShock: number;
      liquidityShock: number;
      correlationShock: number;
      deleveragingSpeed: number;
    };
    historicalWindow: number;
    confidenceLevel: number;
    minCoverageRatio: number;
    stressHorizon: number;
  };
}

interface StressScenario {
  name: string;
  shockFactors: {
    volatility: number;
    liquidity: number;
    correlation: number;
  };
  marketConditions: {
    priceChange: number;
    volumeChange: number;
    spreadChange: number;
  };
  systemLoad: {
    positionCount: number;
    leverageUtilization: number;
    concentrationRisk: number;
  };
}

interface FundMetrics {
  balance: number;
  utilizationRate: number;
  coverageRatio: number;
  historicalDrawdowns: number[];
  recoveryTimes: number[];
  adequacyScore: number;
}

interface StressTestResult {
  scenario: StressScenario;
  expectedLoss: number;
  maxDrawdown: number;
  recoveryTime: number;
  survivabilityScore: number;
  systemImpact: {
    marketDepth: number;
    liquidationCascade: number;
    contagionRisk: number;
  };
}

export class InsuranceFundStressStrategy extends BaseStrategy {
  private fundMetrics: FundMetrics | null = null;
  private stressScenarios: StressScenario[] = [];
  private historicalStresses: Map<string, StressTestResult[]> = new Map();
  private systemState: Map<string, any> = new Map();

  constructor(config: InsuranceFundConfig, supabaseClient: SupabaseClient) {
    super(config, supabaseClient);
  }

  async initialize(): Promise<void> {
    const endDate = new Date();
    const startDate = new Date(
      endDate.getTime() - (this.parameters.historicalWindow * 24 * 60 * 60 * 1000)
    );

    // Initialize fund metrics
    await this.initializeFundMetrics(startDate, endDate);

    // Generate stress scenarios
    this.generateStressScenarios();

    // Initialize system state
    await this.initializeSystemState(startDate, endDate);

    // Run historical stress tests
    await this.runHistoricalStressTests(startDate, endDate);
  }

  async execute(): Promise<StrategyResult> {
    const currentTimestamp = Date.now();
    const signals: Record<string, any> = {};
    const metrics: Record<string, number> = {};

    // Update fund metrics and system state
    await this.updateFundMetrics();
    await this.updateSystemState();

    // Run stress tests for current state
    const stressResults = await this.runStressTests();
    const adequacyAssessment = this.assessFundAdequacy(stressResults);
    const riskMetrics = this.calculateRiskMetrics(stressResults);

    // Generate signals and metrics for each asset
    for (const asset of this.parameters.assets) {
      const assetResults = stressResults.filter(r =>
        r.scenario.name.includes(asset)
      );

      signals[asset] = {
        stressResults: assetResults.map(r => ({
          scenario: r.scenario.name,
          expectedLoss: r.expectedLoss,
          survivability: r.survivabilityScore,
          systemImpact: r.systemImpact
        })),
        adequacy: {
          coverageRatio: this.fundMetrics?.coverageRatio || 0,
          utilizationRate: this.fundMetrics?.utilizationRate || 0,
          adequacyScore: adequacyAssessment.assetScores.get(asset) || 0
        }
      };

      metrics[`${asset}_stress_loss`] = Math.max(
        ...assetResults.map(r => r.expectedLoss)
      );
      metrics[`${asset}_survivability`] = Math.min(
        ...assetResults.map(r => r.survivabilityScore)
      );
    }

    // Add system-wide metrics
    metrics.fund_balance = this.fundMetrics?.balance || 0;
    metrics.fund_utilization = this.fundMetrics?.utilizationRate || 0;
    metrics.fund_adequacy = adequacyAssessment.systemScore;
    metrics.risk_concentration = riskMetrics.concentration;
    metrics.systemic_risk = riskMetrics.systemic;

    const result: StrategyResult = {
      timestamp: currentTimestamp,
      signals: {
        ...signals,
        system: {
          fundMetrics: this.fundMetrics,
          adequacyAssessment,
          riskMetrics,
          recommendations: this.generateRecommendations(
            adequacyAssessment,
            riskMetrics
          )
        }
      },
      metrics
    };

    await this.logResult(result);
    return result;
  }

  async cleanup(): Promise<void> {
    this.fundMetrics = null;
    this.stressScenarios = [];
    this.historicalStresses.clear();
    this.systemState.clear();
  }

  private async initializeFundMetrics(
    startDate: Date,
    endDate: Date
  ): Promise<void> {
    const fundHistory = await this.fetchHistoricalData(
      'insurance_fund',
      startDate,
      endDate
    );

    const balance = fundHistory[fundHistory.length - 1]?.balance || 0;
    const utilizationRates = this.calculateUtilizationRates(fundHistory);
    const coverageRatios = this.calculateCoverageRatios(fundHistory);
    const drawdowns = this.calculateHistoricalDrawdowns(fundHistory);
    const recoveryTimes = this.calculateRecoveryTimes(drawdowns);

    this.fundMetrics = {
      balance,
      utilizationRate: utilizationRates[utilizationRates.length - 1] || 0,
      coverageRatio: coverageRatios[coverageRatios.length - 1] || 0,
      historicalDrawdowns: drawdowns,
      recoveryTimes,
      adequacyScore: this.calculateAdequacyScore(
        balance,
        utilizationRates,
        coverageRatios,
        drawdowns
      )
    };
  }

  private calculateUtilizationRates(history: any[]): number[] {
    return history.map(h => h.usedFunds / h.balance);
  }

  private calculateCoverageRatios(history: any[]): number[] {
    return history.map(h => h.balance / h.totalRisk);
  }

  private calculateHistoricalDrawdowns(history: any[]): number[] {
    const balances = history.map(h => h.balance);
    const drawdowns: number[] = [];
    let peak = balances[0];

    for (const balance of balances) {
      if (balance > peak) {
        peak = balance;
        drawdowns.push(0);
      } else {
        drawdowns.push((peak - balance) / peak);
      }
    }

    return drawdowns;
  }

  private calculateRecoveryTimes(drawdowns: number[]): number[] {
    const recoveryTimes: number[] = [];
    let currentDrawdown = 0;
    let drawdownStart = -1;

    for (let i = 0; i < drawdowns.length; i++) {
      if (drawdowns[i] > 0 && currentDrawdown === 0) {
        drawdownStart = i;
        currentDrawdown = drawdowns[i];
      } else if (drawdowns[i] === 0 && currentDrawdown > 0) {
        recoveryTimes.push(i - drawdownStart);
        currentDrawdown = 0;
        drawdownStart = -1;
      }
    }

    return recoveryTimes;
  }

  private calculateAdequacyScore(
    balance: number,
    utilization: number[],
    coverage: number[],
    drawdowns: number[]
  ): number {
    const utilizationScore = 1 - (
      utilization.reduce((a, b) => a + b, 0) / utilization.length
    );
    const coverageScore = coverage.reduce((a, b) => a + b, 0) / coverage.length;
    const drawdownScore = 1 - (
      drawdowns.reduce((a, b) => a + b, 0) / drawdowns.length
    );
    const balanceScore = Math.min(1, balance / 1000000); // Normalize to $1M

    return (
      utilizationScore * 0.3 +
      coverageScore * 0.3 +
      drawdownScore * 0.2 +
      balanceScore * 0.2
    );
  }

  private generateStressScenarios(): void {
    const baseScenarios = [
      {
        name: 'severe_market_crash',
        shockFactors: {
          volatility: this.parameters.stressScenarios.volatilityShock * 2,
          liquidity: this.parameters.stressScenarios.liquidityShock * 2,
          correlation: this.parameters.stressScenarios.correlationShock * 1.5
        }
      },
      {
        name: 'gradual_deleveraging',
        shockFactors: {
          volatility: this.parameters.stressScenarios.volatilityShock,
          liquidity: this.parameters.stressScenarios.liquidityShock,
          correlation: this.parameters.stressScenarios.correlationShock
        }
      },
      {
        name: 'liquidity_crisis',
        shockFactors: {
          volatility: this.parameters.stressScenarios.volatilityShock * 1.5,
          liquidity: this.parameters.stressScenarios.liquidityShock * 3,
          correlation: this.parameters.stressScenarios.correlationShock * 2
        }
      }
    ];

    // Generate asset-specific scenarios
    for (const asset of this.parameters.assets) {
      for (const base of baseScenarios) {
        this.stressScenarios.push(
          this.generateAssetSpecificScenario(asset, base)
        );
      }
    }
  }

  private generateAssetSpecificScenario(
    asset: string,
    baseScenario: any
  ): StressScenario {
    const assetState = this.systemState.get(asset);
    const volatilityMod = assetState?.volatility || 1;
    const liquidityMod = assetState?.liquidity || 1;

    return {
      name: `${asset}_${baseScenario.name}`,
      shockFactors: {
        volatility: baseScenario.shockFactors.volatility * volatilityMod,
        liquidity: baseScenario.shockFactors.liquidity * liquidityMod,
        correlation: baseScenario.shockFactors.correlation
      },
      marketConditions: {
        priceChange: -baseScenario.shockFactors.volatility * volatilityMod,
        volumeChange: -baseScenario.shockFactors.liquidity * liquidityMod,
        spreadChange: baseScenario.shockFactors.liquidity * liquidityMod
      },
      systemLoad: {
        positionCount: assetState?.positionCount || 0,
        leverageUtilization: assetState?.leverage || 0,
        concentrationRisk: assetState?.concentration || 0
      }
    };
  }

  private async initializeSystemState(
    startDate: Date,
    endDate: Date
  ): Promise<void> {
    for (const asset of this.parameters.assets) {
      const [positions, trades] = await Promise.all([
        this.fetchHistoricalData(`positions_${asset}`, startDate, endDate),
        this.fetchHistoricalData(`trades_${asset}`, startDate, endDate)
      ]);

      this.systemState.set(asset, {
        volatility: this.calculateVolatility(trades),
        liquidity: this.calculateLiquidity(trades),
        positionCount: positions.length,
        leverage: this.calculateAverageLeverage(positions),
        concentration: this.calculateConcentration(positions)
      });
    }
  }

  private async updateSystemState(): Promise<void> {
    const endDate = new Date();
    const startDate = new Date(
      endDate.getTime() - (24 * 60 * 60 * 1000) // Last 24 hours
    );

    await this.initializeSystemState(startDate, endDate);
  }

  private async updateFundMetrics(): Promise<void> {
    const endDate = new Date();
    const startDate = new Date(
      endDate.getTime() - (24 * 60 * 60 * 1000)
    );

    await this.initializeFundMetrics(startDate, endDate);
  }

  private calculateVolatility(trades: any[]): number {
    const returns = trades.slice(1).map((t, i) =>
      Math.log(t.price / trades[i].price)
    );

    const mean = returns.reduce((a, b) => a + b, 0) / returns.length;
    const variance = returns.reduce(
      (sum, ret) => sum + Math.pow(ret - mean, 2),
      0
    ) / returns.length;

    return Math.sqrt(variance * 365 * 24); // Annualized
  }

  private calculateLiquidity(trades: any[]): number {
    const volumes = trades.map(t => t.volume);
    const spreads = trades.map(t => t.spread);

    const avgVolume = volumes.reduce((a, b) => a + b, 0) / volumes.length;
    const avgSpread = spreads.reduce((a, b) => a + b, 0) / spreads.length;

    return avgVolume / (1 + avgSpread);
  }

  private calculateAverageLeverage(positions: any[]): number {
    return positions.reduce(
      (sum, pos) => sum + pos.notionalValue / pos.margin,
      0
    ) / positions.length;
  }

  private calculateConcentration(positions: any[]): number {
    const totalValue = positions.reduce(
      (sum, pos) => sum + pos.notionalValue,
      0
    );
    const maxPosition = Math.max(
      ...positions.map(p => p.notionalValue)
    );

    return maxPosition / totalValue;
  }

  private async runHistoricalStressTests(
    startDate: Date,
    endDate: Date
  ): Promise<void> {
    for (const asset of this.parameters.assets) {
      const results: StressTestResult[] = [];
      const assetScenarios = this.stressScenarios.filter(s =>
        s.name.includes(asset)
      );

      for (const scenario of assetScenarios) {
        const result = await this.runStressTest(
          asset,
          scenario,
          startDate,
          endDate
        );
        results.push(result);
      }

      this.historicalStresses.set(asset, results);
    }
  }

  private async runStressTests(): Promise<StressTestResult[]> {
    const results: StressTestResult[] = [];

    for (const scenario of this.stressScenarios) {
      const asset = this.parameters.assets.find(a =>
        scenario.name.includes(a)
      );
      if (!asset) continue;

      const result = await this.runStressTest(
        asset,
        scenario,
        new Date(Date.now() - (24 * 60 * 60 * 1000)),
        new Date()
      );
      results.push(result);
    }

    return results;
  }

  private async runStressTest(
    asset: string,
    scenario: StressScenario,
    startDate: Date,
    endDate: Date
  ): Promise<StressTestResult> {
    const positions = await this.fetchHistoricalData(
      `positions_${asset}`,
      startDate,
      endDate
    );

    const expectedLoss = this.calculateExpectedLoss(
      positions,
      scenario
    );

    const maxDrawdown = this.calculateStressDrawdown(
      this.fundMetrics?.balance || 0,
      expectedLoss,
      scenario
    );

    const recoveryTime = this.estimateRecoveryTime(
      maxDrawdown,
      scenario
    );

    const survivabilityScore = this.calculateSurvivabilityScore(
      maxDrawdown,
      recoveryTime,
      scenario
    );

    const systemImpact = this.calculateSystemImpact(
      expectedLoss,
      scenario
    );

    return {
      scenario,
      expectedLoss,
      maxDrawdown,
      recoveryTime,
      survivabilityScore,
      systemImpact
    };
  }

  private calculateExpectedLoss(
    positions: any[],
    scenario: StressScenario
  ): number {
    const totalExposure = positions.reduce(
      (sum, pos) => sum + pos.notionalValue,
      0
    );

    const leverageImpact = scenario.systemLoad.leverageUtilization *
      scenario.shockFactors.volatility;

    const liquidityImpact = scenario.systemLoad.concentrationRisk *
      scenario.shockFactors.liquidity;

    const correlationImpact = Math.sqrt(
      scenario.systemLoad.positionCount
    ) * scenario.shockFactors.correlation;

    return totalExposure * (
      leverageImpact * 0.4 +
      liquidityImpact * 0.3 +
      correlationImpact * 0.3
    );
  }

  private calculateStressDrawdown(
    balance: number,
    loss: number,
    scenario: StressScenario
  ): number {
    const baseDrawdown = loss / balance;
    const marketImpact = Math.abs(scenario.marketConditions.priceChange);
    const liquidityFactor = 1 + Math.abs(scenario.marketConditions.volumeChange);

    return Math.min(1, baseDrawdown * liquidityFactor * (1 + marketImpact));
  }

  private estimateRecoveryTime(
    drawdown: number,
    scenario: StressScenario
  ): number {
    const baseRecovery = drawdown * this.parameters.stressHorizon;
    const marketFactor = 1 + Math.abs(scenario.marketConditions.priceChange);
    const deleveragingFactor = 1 + this.parameters.stressScenarios.deleveragingSpeed;

    return baseRecovery * marketFactor * deleveragingFactor;
  }

  private calculateSurvivabilityScore(
    drawdown: number,
    recoveryTime: number,
    scenario: StressScenario
  ): number {
    const drawdownScore = 1 - drawdown;
    const recoveryScore = 1 - (
      recoveryTime / (this.parameters.stressHorizon * 2)
    );
    const resilienceScore = 1 - (
      (scenario.shockFactors.volatility +
       scenario.shockFactors.liquidity +
       scenario.shockFactors.correlation) / 3
    );

    return Math.max(
      0,
      drawdownScore * 0.4 +
      recoveryScore * 0.3 +
      resilienceScore * 0.3
    );
  }

  private calculateSystemImpact(
    loss: number,
    scenario: StressScenario
  ): {
    marketDepth: number;
    liquidationCascade: number;
    contagionRisk: number;
  } {
    const marketDepth = Math.min(
      1,
      Math.abs(scenario.marketConditions.volumeChange) *
      scenario.shockFactors.liquidity
    );

    const liquidationCascade = Math.min(
      1,
      scenario.systemLoad.leverageUtilization *
      scenario.shockFactors.volatility
    );

    const contagionRisk = Math.min(
      1,
      scenario.systemLoad.concentrationRisk *
      scenario.shockFactors.correlation
    );

    return {
      marketDepth,
      liquidationCascade,
      contagionRisk
    };
  }

  private assessFundAdequacy(
    stressResults: StressTestResult[]
  ): {
    systemScore: number;
    assetScores: Map<string, number>;
    weaknesses: string[];
    recommendations: string[];
  } {
    const assetScores = new Map<string, number>();
    const weaknesses: string[] = [];
    const recommendations: string[] = [];

    // Calculate asset-specific scores
    for (const asset of this.parameters.assets) {
      const assetResults = stressResults.filter(r =>
        r.scenario.name.includes(asset)
      );
      const score = this.calculateAssetAdequacyScore(assetResults);
      assetScores.set(asset, score);

      if (score < 0.6) {
        weaknesses.push(`Low adequacy for ${asset}: ${score.toFixed(2)}`);
        recommendations.push(
          this.generateAssetRecommendation(asset, score, assetResults)
        );
      }
    }

    // Calculate system-wide score
    const systemScore = Array.from(assetScores.values()).reduce(
      (sum, score) => sum + score,
      0
    ) / assetScores.size;

    // Add system-wide recommendations
    if (systemScore < 0.7) {
      weaknesses.push(`Low system-wide adequacy: ${systemScore.toFixed(2)}`);
      recommendations.push(
        this.generateSystemRecommendation(systemScore, stressResults)
      );
    }

    return {
      systemScore,
      assetScores,
      weaknesses,
      recommendations
    };
  }

  private calculateAssetAdequacyScore(
    results: StressTestResult[]
  ): number {
    if (results.length === 0) return 0;

    const survivabilityScore = results.reduce(
      (sum, r) => sum + r.survivabilityScore,
      0
    ) / results.length;

    const lossRatio = results.reduce(
      (sum, r) => sum + r.expectedLoss / (this.fundMetrics?.balance || 1),
      0
    ) / results.length;

    const impactScore = 1 - results.reduce(
      (sum, r) => sum + (
        r.systemImpact.marketDepth +
        r.systemImpact.liquidationCascade +
        r.systemImpact.contagionRisk
      ) / 3,
      0
    ) / results.length;

    return (
      survivabilityScore * 0.4 +
      (1 - lossRatio) * 0.3 +
      impactScore * 0.3
    );
  }

  private generateAssetRecommendation(
    asset: string,
    score: number,
    results: StressTestResult[]
  ): string {
    const worstResult = results.reduce(
      (worst, current) => current.survivabilityScore < worst.survivabilityScore ?
        current : worst
    );

    if (score < 0.3) {
      return `Critical: Increase insurance fund allocation for ${asset} by ${
        ((1 - score) * 100).toFixed(0)
      }% to handle ${worstResult.scenario.name}`;
    } else if (score < 0.6) {
      return `Warning: Consider adjusting risk parameters for ${asset} to improve resilience against ${
        worstResult.scenario.name
      }`;
    } else {
      return `Monitor: Maintain current coverage for ${asset} and review periodically`;
    }
  }

  private generateSystemRecommendation(
    score: number,
    results: StressTestResult[]
  ): string {
    const systemImpacts = results.map(r => ({
      scenario: r.scenario.name,
      impact: (
        r.systemImpact.marketDepth +
        r.systemImpact.liquidationCascade +
        r.systemImpact.contagionRisk
      ) / 3
    }));

    const worstImpact = systemImpacts.reduce(
      (worst, current) => current.impact > worst.impact ?
        current : worst
    );

    if (score < 0.3) {
      return `Critical: System-wide insurance fund inadequacy. Increase total fund size by ${
        ((1 - score) * 100).toFixed(0)
      }% to handle ${worstImpact.scenario}`;
    } else if (score < 0.6) {
      return `Warning: Review system-wide risk parameters and consider deleveraging to improve resilience`;
    } else {
      return `Monitor: Maintain current system state and review stress scenarios periodically`;
    }
  }

  private calculateRiskMetrics(
    results: StressTestResult[]
  ): {
    concentration: number;
    systemic: number;
    temporal: number;
    recovery: number;
  } {
    const concentration = results.reduce(
      (max, r) => Math.max(max, r.scenario.systemLoad.concentrationRisk),
      0
    );

    const systemic = results.reduce(
      (sum, r) => sum + (
        r.systemImpact.marketDepth +
        r.systemImpact.liquidationCascade +
        r.systemImpact.contagionRisk
      ) / 3,
      0
    ) / results.length;

    const temporal = results.reduce(
      (sum, r) => sum + r.recoveryTime,
      0
    ) / (results.length * this.parameters.stressHorizon);

    const recovery = results.reduce(
      (sum, r) => sum + r.survivabilityScore,
      0
    ) / results.length;

    return {
      concentration,
      systemic,
      temporal,
      recovery
    };
  }

  private generateRecommendations(
    adequacy: {
      systemScore: number;
      assetScores: Map<string, number>;
      weaknesses: string[];
      recommendations: string[];
    },
    riskMetrics: {
      concentration: number;
      systemic: number;
      temporal: number;
      recovery: number;
    }
  ): string[] {
    const recommendations = [...adequacy.recommendations];

    // Add risk-based recommendations
    if (riskMetrics.concentration > 0.7) {
      recommendations.push(
        'High concentration risk: Implement position limits and encourage diversification'
      );
    }

    if (riskMetrics.systemic > 0.6) {
      recommendations.push(
        'Elevated systemic risk: Review cross-asset correlation limits and circuit breakers'
      );
    }

    if (riskMetrics.temporal > 0.5) {
      recommendations.push(
        'Extended recovery periods: Adjust deleveraging mechanisms and liquidation parameters'
      );
    }

    if (riskMetrics.recovery < 0.4) {
      recommendations.push(
        'Poor recovery metrics: Increase insurance fund buffer and review fee structure'
      );
    }

    return recommendations;
  }
} 