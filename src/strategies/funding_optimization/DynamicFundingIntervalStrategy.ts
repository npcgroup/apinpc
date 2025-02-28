import { BaseStrategy, StrategyConfig, StrategyResult } from '../base_strategy';
import { SupabaseClient } from '@supabase/supabase-js';

interface FundingIntervalConfig extends StrategyConfig {
  parameters: {
    assets: string[];
    minIntervalHours: number;
    maxIntervalHours: number;
    volatilityWindowSize: number;
    volumeThreshold: number;
    efficiencyThreshold: number;
    adaptationRate: number;
    stabilityWeight: number;
  };
}

interface MarketState {
  volatility: number;
  volume: number;
  basis: number;
  fundingEfficiency: number;
  marketEfficiency: number;
  timestamp: number;
}

interface IntervalRecommendation {
  optimalInterval: number;
  confidence: number;
  factors: {
    volatilityScore: number;
    volumeScore: number;
    efficiencyScore: number;
    stabilityScore: number;
  };
  expectedBenefit: {
    costReduction: number;
    marketEfficiency: number;
    volumeImprovement: number;
  };
}

export class DynamicFundingIntervalStrategy extends BaseStrategy {
  private marketStates: Map<string, MarketState[]> = new Map();
  private currentIntervals: Map<string, number> = new Map();
  private stateTransitions: Map<string, number[][]> = new Map();
  private performanceMetrics: Map<string, number[]> = new Map();

  constructor(config: FundingIntervalConfig, supabaseClient: SupabaseClient) {
    super(config, supabaseClient);
  }

  async initialize(): Promise<void> {
    const endDate = new Date();
    const startDate = new Date(
      endDate.getTime() - (7 * 24 * 60 * 60 * 1000) // Last 7 days
    );

    for (const asset of this.parameters.assets) {
      // Fetch historical market data
      const [prices, volumes, fundingRates] = await Promise.all([
        this.fetchHistoricalData(`prices_${asset}`, startDate, endDate),
        this.fetchHistoricalData(`volumes_${asset}`, startDate, endDate),
        this.fetchHistoricalData(`funding_rates_${asset}`, startDate, endDate)
      ]);

      // Calculate market states and transitions
      const states = this.calculateMarketStates(prices, volumes, fundingRates);
      this.marketStates.set(asset, states);

      const transitions = this.calculateStateTransitions(states);
      this.stateTransitions.set(asset, transitions);

      // Initialize current intervals
      this.currentIntervals.set(asset, 8); // Default 8-hour interval

      // Calculate historical performance metrics
      const metrics = this.calculatePerformanceMetrics(states, fundingRates);
      this.performanceMetrics.set(asset, metrics);
    }
  }

  async execute(): Promise<StrategyResult> {
    const currentTimestamp = Date.now();
    const signals: Record<string, any> = {};
    const metrics: Record<string, number> = {};

    for (const asset of this.parameters.assets) {
      // Get current market state
      const currentState = await this.getCurrentMarketState(asset, currentTimestamp);
      const states = this.marketStates.get(asset) || [];
      states.push(currentState);
      this.marketStates.set(asset, states.slice(-100)); // Keep last 100 states

      // Calculate optimal interval
      const recommendation = this.calculateOptimalInterval(
        asset,
        currentState,
        states
      );

      // Update current interval with adaptation rate
      const currentInterval = this.currentIntervals.get(asset) || 8;
      const newInterval = this.adaptInterval(
        currentInterval,
        recommendation.optimalInterval
      );
      this.currentIntervals.set(asset, newInterval);

      signals[asset] = {
        currentState: {
          volatility: currentState.volatility,
          volume: currentState.volume,
          marketEfficiency: currentState.marketEfficiency
        },
        recommendation: {
          currentInterval,
          optimalInterval: recommendation.optimalInterval,
          confidence: recommendation.confidence,
          factors: recommendation.factors
        },
        expectedBenefits: recommendation.expectedBenefit,
        transitionProbabilities: this.calculateTransitionProbabilities(
          asset,
          currentState
        )
      };

      metrics[`${asset}_optimal_interval`] = recommendation.optimalInterval;
      metrics[`${asset}_interval_confidence`] = recommendation.confidence;
      metrics[`${asset}_market_efficiency`] = currentState.marketEfficiency;
      metrics[`${asset}_adaptation_rate`] = this.calculateAdaptationRate(
        currentState,
        states
      );
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
    this.marketStates.clear();
    this.currentIntervals.clear();
    this.stateTransitions.clear();
    this.performanceMetrics.clear();
  }

  private calculateMarketStates(
    prices: any[],
    volumes: any[],
    fundingRates: any[]
  ): MarketState[] {
    const states: MarketState[] = [];
    const windowSize = this.parameters.volatilityWindowSize;

    for (let i = windowSize; i < prices.length; i++) {
      const windowPrices = prices.slice(i - windowSize, i);
      const windowVolumes = volumes.slice(i - windowSize, i);
      const windowRates = fundingRates.slice(i - windowSize, i);

      states.push({
        volatility: this.calculateVolatility(windowPrices),
        volume: this.calculateAverageVolume(windowVolumes),
        basis: this.calculateAverageBasis(windowPrices, windowRates),
        fundingEfficiency: this.calculateFundingEfficiency(windowRates),
        marketEfficiency: this.calculateMarketEfficiency(windowPrices, windowRates),
        timestamp: new Date(prices[i].timestamp).getTime()
      });
    }

    return states;
  }

  private calculateVolatility(prices: any[]): number {
    const returns = prices.slice(1).map((p, i) =>
      Math.log(p.price / prices[i].price)
    );

    const mean = returns.reduce((a, b) => a + b, 0) / returns.length;
    const variance = returns.reduce(
      (sum, ret) => sum + Math.pow(ret - mean, 2),
      0
    ) / returns.length;

    return Math.sqrt(variance * 365 * 24); // Annualized
  }

  private calculateAverageVolume(volumes: any[]): number {
    return volumes.reduce((sum, v) => sum + v.volume, 0) / volumes.length;
  }

  private calculateAverageBasis(prices: any[], rates: any[]): number {
    const spotPrices = prices.map(p => p.price);
    const fundingRates = rates.map(r => r.rate);

    return fundingRates.reduce((sum, rate, i) =>
      sum + Math.abs(rate - (spotPrices[i + 1] / spotPrices[i] - 1)),
      0
    ) / fundingRates.length;
  }

  private calculateFundingEfficiency(rates: any[]): number {
    if (rates.length < 2) return 1;

    const changes = rates.slice(1).map((r, i) =>
      Math.abs(r.rate - rates[i].rate)
    );

    const avgChange = changes.reduce((a, b) => a + b, 0) / changes.length;
    return 1 / (1 + avgChange);
  }

  private calculateMarketEfficiency(prices: any[], rates: any[]): number {
    const priceEfficiency = this.calculatePriceEfficiency(prices);
    const fundingEfficiency = this.calculateFundingEfficiency(rates);
    
    return (priceEfficiency + fundingEfficiency) / 2;
  }

  private calculatePriceEfficiency(prices: any[]): number {
    if (prices.length < 2) return 1;

    const returns = prices.slice(1).map((p, i) =>
      Math.abs(Math.log(p.price / prices[i].price))
    );

    const autocorrelation = this.calculateAutocorrelation(returns);
    return 1 / (1 + Math.abs(autocorrelation));
  }

  private calculateAutocorrelation(data: number[]): number {
    const mean = data.reduce((a, b) => a + b, 0) / data.length;
    const variance = data.reduce(
      (sum, x) => sum + Math.pow(x - mean, 2),
      0
    ) / data.length;

    const correlation = data.slice(1).reduce(
      (sum, x, i) => sum + (x - mean) * (data[i] - mean),
      0
    ) / (data.length - 1);

    return correlation / variance;
  }

  private calculateStateTransitions(states: MarketState[]): number[][] {
    const stateCount = 5; // Discretize states into 5 levels
    const transitions = Array(stateCount).fill(0).map(() =>
      Array(stateCount).fill(0)
    );

    for (let i = 1; i < states.length; i++) {
      const prevState = this.discretizeState(states[i - 1]);
      const currentState = this.discretizeState(states[i]);
      transitions[prevState][currentState]++;
    }

    // Normalize to probabilities
    return transitions.map(row => {
      const sum = row.reduce((a, b) => a + b, 0);
      return row.map(count => sum === 0 ? 0 : count / sum);
    });
  }

  private discretizeState(state: MarketState): number {
    // Simple discretization based on market efficiency
    const efficiency = state.marketEfficiency;
    if (efficiency > 0.8) return 4;
    if (efficiency > 0.6) return 3;
    if (efficiency > 0.4) return 2;
    if (efficiency > 0.2) return 1;
    return 0;
  }

  private async getCurrentMarketState(
    asset: string,
    timestamp: number
  ): Promise<MarketState> {
    const windowEnd = new Date(timestamp);
    const windowStart = new Date(
      timestamp - (this.parameters.volatilityWindowSize * 60 * 60 * 1000)
    );

    const [prices, volumes, rates] = await Promise.all([
      this.fetchHistoricalData(`prices_${asset}`, windowStart, windowEnd),
      this.fetchHistoricalData(`volumes_${asset}`, windowStart, windowEnd),
      this.fetchHistoricalData(`funding_rates_${asset}`, windowStart, windowEnd)
    ]);

    return {
      volatility: this.calculateVolatility(prices),
      volume: this.calculateAverageVolume(volumes),
      basis: this.calculateAverageBasis(prices, rates),
      fundingEfficiency: this.calculateFundingEfficiency(rates),
      marketEfficiency: this.calculateMarketEfficiency(prices, rates),
      timestamp
    };
  }

  private calculateOptimalInterval(
    asset: string,
    currentState: MarketState,
    historicalStates: MarketState[]
  ): IntervalRecommendation {
    // Calculate component scores
    const volatilityScore = this.calculateVolatilityScore(
      currentState.volatility,
      historicalStates
    );
    const volumeScore = this.calculateVolumeScore(
      currentState.volume,
      historicalStates
    );
    const efficiencyScore = currentState.marketEfficiency;
    const stabilityScore = this.calculateStabilityScore(
      asset,
      currentState,
      historicalStates
    );

    // Combine scores with weights
    const weights = {
      volatility: 0.3,
      volume: 0.2,
      efficiency: 0.3,
      stability: 0.2
    };

    const combinedScore = (
      volatilityScore * weights.volatility +
      volumeScore * weights.volume +
      efficiencyScore * weights.efficiency +
      stabilityScore * weights.stability
    );

    // Map combined score to interval range
    const intervalRange = this.parameters.maxIntervalHours - this.parameters.minIntervalHours;
    const optimalInterval = this.parameters.minIntervalHours +
      intervalRange * (1 - combinedScore);

    // Calculate confidence and expected benefits
    const confidence = this.calculateRecommendationConfidence(
      currentState,
      historicalStates,
      optimalInterval
    );

    const expectedBenefit = this.calculateExpectedBenefits(
      currentState,
      optimalInterval
    );

    return {
      optimalInterval,
      confidence,
      factors: {
        volatilityScore,
        volumeScore,
        efficiencyScore,
        stabilityScore
      },
      expectedBenefit
    };
  }

  private calculateVolatilityScore(
    currentVol: number,
    historicalStates: MarketState[]
  ): number {
    const historicalVols = historicalStates.map(s => s.volatility);
    const maxVol = Math.max(...historicalVols);
    return 1 - (currentVol / maxVol);
  }

  private calculateVolumeScore(
    currentVol: number,
    historicalStates: MarketState[]
  ): number {
    const avgVolume = historicalStates.reduce(
      (sum, state) => sum + state.volume,
      0
    ) / historicalStates.length;

    return Math.min(1, currentVol / (avgVolume * this.parameters.volumeThreshold));
  }

  private calculateStabilityScore(
    asset: string,
    currentState: MarketState,
    historicalStates: MarketState[]
  ): number {
    const transitions = this.stateTransitions.get(asset) || [];
    const currentStateIndex = this.discretizeState(currentState);

    if (transitions.length === 0) return 0.5;

    // Calculate probability of staying in current state
    const stayProbability = transitions[currentStateIndex][currentStateIndex];
    
    // Calculate trend stability
    const recentStates = historicalStates.slice(-12); // Last 12 states
    const trendStability = this.calculateTrendStability(recentStates);

    return (stayProbability + trendStability) / 2;
  }

  private calculateTrendStability(states: MarketState[]): number {
    if (states.length < 2) return 1;

    const efficiencyChanges = states.slice(1).map((state, i) =>
      Math.abs(state.marketEfficiency - states[i].marketEfficiency)
    );

    const avgChange = efficiencyChanges.reduce((a, b) => a + b, 0) / 
      efficiencyChanges.length;

    return 1 / (1 + avgChange * 10); // Scale factor of 10 for sensitivity
  }

  private calculateRecommendationConfidence(
    currentState: MarketState,
    historicalStates: MarketState[],
    recommendedInterval: number
  ): number {
    // Calculate historical accuracy
    const historicalAccuracy = this.calculateHistoricalAccuracy(
      historicalStates,
      recommendedInterval
    );

    // Calculate state stability
    const stateStability = this.calculateTrendStability(
      historicalStates.slice(-12)
    );

    // Calculate market predictability
    const marketPredictability = currentState.marketEfficiency;

    return (
      historicalAccuracy * 0.4 +
      stateStability * 0.3 +
      marketPredictability * 0.3
    );
  }

  private calculateHistoricalAccuracy(
    states: MarketState[],
    recommendedInterval: number
  ): number {
    if (states.length < 2) return 0.5;

    const metrics = this.performanceMetrics.get(states[0].asset) || [];
    const relevantMetrics = metrics.filter(m =>
      Math.abs(m - recommendedInterval) <= 2
    );

    return relevantMetrics.length / metrics.length;
  }

  private calculateExpectedBenefits(
    state: MarketState,
    optimalInterval: number
  ): {
    costReduction: number;
    marketEfficiency: number;
    volumeImprovement: number;
  } {
    // Estimate cost reduction from optimal interval
    const costReduction = Math.max(
      0,
      (1 - state.fundingEfficiency) * (optimalInterval / 8) // 8 hours as baseline
    );

    // Estimate market efficiency improvement
    const efficiencyImprovement = Math.max(
      0,
      0.1 * (1 - state.marketEfficiency) * (optimalInterval / 8)
    );

    // Estimate volume improvement
    const volumeImprovement = Math.max(
      0,
      0.05 * (1 - state.volume / this.parameters.volumeThreshold)
    );

    return {
      costReduction,
      marketEfficiency: efficiencyImprovement,
      volumeImprovement
    };
  }

  private adaptInterval(
    currentInterval: number,
    optimalInterval: number
  ): number {
    const adaptationRate = this.parameters.adaptationRate;
    const diff = optimalInterval - currentInterval;
    
    return Math.min(
      this.parameters.maxIntervalHours,
      Math.max(
        this.parameters.minIntervalHours,
        currentInterval + diff * adaptationRate
      )
    );
  }

  private calculateTransitionProbabilities(
    asset: string,
    currentState: MarketState
  ): number[] {
    const transitions = this.stateTransitions.get(asset) || [];
    const currentStateIndex = this.discretizeState(currentState);

    return transitions[currentStateIndex] || Array(5).fill(0.2);
  }

  private calculateAdaptationRate(
    currentState: MarketState,
    historicalStates: MarketState[]
  ): number {
    const baseRate = this.parameters.adaptationRate;
    const stability = this.calculateTrendStability(
      historicalStates.slice(-12)
    );

    // Adjust adaptation rate based on market stability
    return baseRate * (0.5 + 0.5 * stability);
  }

  private calculatePerformanceMetrics(
    states: MarketState[],
    fundingRates: any[]
  ): number[] {
    return states.map((state, i) => {
      if (i < 24) return 8; // Default to 8 hours for first day

      const prevStates = states.slice(i - 24, i);
      const prevRates = fundingRates.slice(i - 24, i);

      const volatility = this.calculateVolatility(prevStates.map(s => ({
        price: s.basis,
        timestamp: s.timestamp
      })));

      const efficiency = this.calculateFundingEfficiency(prevRates);

      // Calculate optimal interval based on historical performance
      return Math.min(
        this.parameters.maxIntervalHours,
        Math.max(
          this.parameters.minIntervalHours,
          8 * (1 + volatility) * (1 / efficiency)
        )
      );
    });
  }
} 