import { BaseStrategy, StrategyConfig, StrategyResult } from '../base_strategy';
import { SupabaseClient } from '@supabase/supabase-js';

interface PositionFlipConfig extends StrategyConfig {
  parameters: {
    assets: string[];
    windowMinutesBefore: number;
    windowMinutesAfter: number;
    minPositionSize: number;
    significanceThreshold: number;
    minFlipCount: number;
  };
}

interface PositionFlip {
  asset: string;
  timestamp: number;
  direction: 'long_to_short' | 'short_to_long';
  size: number;
  priceImpact: number;
  timeTillFunding: number;
  isSignificant: boolean;
}

interface FlipPattern {
  asset: string;
  frequency: number;
  avgSize: number;
  avgImpact: number;
  timeDistribution: number[];
  profitability: number;
}

export class PositionFlipStrategy extends BaseStrategy {
  private recentFlips: Map<string, PositionFlip[]> = new Map();
  private patterns: Map<string, FlipPattern> = new Map();
  private nextFundingTimes: Map<string, number> = new Map();

  constructor(config: PositionFlipConfig, supabaseClient: SupabaseClient) {
    super(config, supabaseClient);
  }

  async initialize(): Promise<void> {
    const endDate = new Date();
    const startDate = new Date(
      endDate.getTime() - (24 * 60 * 60 * 1000) // Last 24 hours
    );

    for (const asset of this.parameters.assets) {
      // Get next funding timestamp
      const fundingSchedule = await this.fetchHistoricalData(
        `funding_schedule_${asset}`,
        startDate,
        endDate
      );
      
      if (fundingSchedule.length > 0) {
        this.nextFundingTimes.set(
          asset,
          new Date(fundingSchedule[0].next_funding).getTime()
        );
      }

      // Analyze historical flips
      const flips = await this.analyzeHistoricalFlips(asset, startDate, endDate);
      this.recentFlips.set(asset, flips);
      
      // Identify patterns
      const pattern = this.identifyFlipPattern(flips);
      this.patterns.set(asset, pattern);
    }
  }

  async execute(): Promise<StrategyResult> {
    const currentTimestamp = Date.now();
    const signals: Record<string, any> = {};
    const metrics: Record<string, number> = {};

    for (const asset of this.parameters.assets) {
      // Analyze recent position changes
      const recentFlips = await this.detectRecentFlips(asset, currentTimestamp);
      const pattern = this.patterns.get(asset);
      const nextFunding = this.nextFundingTimes.get(asset) || 0;

      if (pattern) {
        const prediction = this.predictFlipLikelihood(
          asset,
          currentTimestamp,
          nextFunding,
          pattern
        );

        signals[asset] = {
          recentFlips: recentFlips.map(flip => ({
            direction: flip.direction,
            size: flip.size,
            timeTillFunding: flip.timeTillFunding,
            isSignificant: flip.isSignificant
          })),
          pattern: {
            frequency: pattern.frequency,
            avgSize: pattern.avgSize,
            timeDistribution: pattern.timeDistribution
          },
          prediction: {
            flipLikelihood: prediction.probability,
            expectedDirection: prediction.direction,
            expectedSize: prediction.size,
            confidence: prediction.confidence
          }
        };

        metrics[`${asset}_flip_frequency`] = pattern.frequency;
        metrics[`${asset}_avg_flip_size`] = pattern.avgSize;
        metrics[`${asset}_avg_impact`] = pattern.avgImpact;
        metrics[`${asset}_flip_likelihood`] = prediction.probability;
      }
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
    this.recentFlips.clear();
    this.patterns.clear();
    this.nextFundingTimes.clear();
  }

  private async analyzeHistoricalFlips(
    asset: string,
    startDate: Date,
    endDate: Date
  ): Promise<PositionFlip[]> {
    // Fetch position changes and funding timestamps
    const positions = await this.fetchHistoricalData(
      `position_changes_${asset}`,
      startDate,
      endDate
    );

    const fundingTimes = await this.fetchHistoricalData(
      `funding_payments_${asset}`,
      startDate,
      endDate
    );

    return this.identifyFlips(positions, fundingTimes);
  }

  private identifyFlips(
    positions: any[],
    fundingTimes: any[]
  ): PositionFlip[] {
    const flips: PositionFlip[] = [];
    let lastPosition = null;

    for (let i = 1; i < positions.length; i++) {
      const current = positions[i];
      const previous = positions[i - 1];
      
      // Check for position flip
      if (this.isFlip(previous, current)) {
        const nearestFunding = this.findNearestFunding(
          current.timestamp,
          fundingTimes
        );
        
        const timeTillFunding = nearestFunding - new Date(current.timestamp).getTime();
        const isWithinWindow = Math.abs(timeTillFunding) <= 
          (this.parameters.windowMinutesBefore * 60 * 1000);

        if (isWithinWindow) {
          flips.push({
            asset: current.asset,
            timestamp: new Date(current.timestamp).getTime(),
            direction: this.getFlipDirection(previous, current),
            size: Math.abs(current.size),
            priceImpact: this.calculatePriceImpact(previous, current),
            timeTillFunding,
            isSignificant: Math.abs(current.size) >= this.parameters.minPositionSize
          });
        }
      }
    }

    return flips;
  }

  private isFlip(previous: any, current: any): boolean {
    return (previous.size > 0 && current.size < 0) || 
           (previous.size < 0 && current.size > 0);
  }

  private getFlipDirection(
    previous: any,
    current: any
  ): 'long_to_short' | 'short_to_long' {
    return previous.size > 0 ? 'long_to_short' : 'short_to_long';
  }

  private calculatePriceImpact(previous: any, current: any): number {
    return Math.abs(current.price - previous.price) / previous.price;
  }

  private findNearestFunding(
    timestamp: string,
    fundingTimes: any[]
  ): number {
    const time = new Date(timestamp).getTime();
    let nearest = Infinity;
    let nearestDiff = Infinity;

    for (const funding of fundingTimes) {
      const fundingTime = new Date(funding.timestamp).getTime();
      const diff = Math.abs(fundingTime - time);
      if (diff < nearestDiff) {
        nearest = fundingTime;
        nearestDiff = diff;
      }
    }

    return nearest;
  }

  private identifyFlipPattern(flips: PositionFlip[]): FlipPattern {
    if (flips.length < this.parameters.minFlipCount) {
      return {
        asset: flips[0]?.asset || '',
        frequency: 0,
        avgSize: 0,
        avgImpact: 0,
        timeDistribution: new Array(24).fill(0),
        profitability: 0
      };
    }

    // Calculate basic metrics
    const frequency = flips.length / (24 * 60 * 60 * 1000); // Flips per second
    const avgSize = flips.reduce((sum, f) => sum + f.size, 0) / flips.length;
    const avgImpact = flips.reduce((sum, f) => sum + f.priceImpact, 0) / flips.length;

    // Analyze time distribution (24 hour bins)
    const timeDistribution = new Array(24).fill(0);
    for (const flip of flips) {
      const hour = new Date(flip.timestamp).getHours();
      timeDistribution[hour]++;
    }

    // Normalize distribution
    const total = timeDistribution.reduce((a, b) => a + b, 0);
    for (let i = 0; i < timeDistribution.length; i++) {
      timeDistribution[i] /= total;
    }

    // Calculate profitability (simple implementation)
    const profitability = flips.reduce((sum, flip) => {
      const timingScore = Math.exp(-Math.abs(flip.timeTillFunding) / (60 * 60 * 1000));
      return sum + (flip.priceImpact * timingScore);
    }, 0) / flips.length;

    return {
      asset: flips[0].asset,
      frequency,
      avgSize,
      avgImpact,
      timeDistribution,
      profitability
    };
  }

  private async detectRecentFlips(
    asset: string,
    currentTimestamp: number
  ): Promise<PositionFlip[]> {
    const windowStart = new Date(
      currentTimestamp - (this.parameters.windowMinutesBefore * 60 * 1000)
    );
    const windowEnd = new Date(currentTimestamp);

    const positions = await this.fetchHistoricalData(
      `position_changes_${asset}`,
      windowStart,
      windowEnd
    );

    const fundingTimes = await this.fetchHistoricalData(
      `funding_payments_${asset}`,
      windowStart,
      windowEnd
    );

    return this.identifyFlips(positions, fundingTimes);
  }

  private predictFlipLikelihood(
    asset: string,
    currentTimestamp: number,
    nextFunding: number,
    pattern: FlipPattern
  ): {
    probability: number;
    direction: 'long_to_short' | 'short_to_long';
    size: number;
    confidence: number;
  } {
    const timeTillFunding = nextFunding - currentTimestamp;
    const currentHour = new Date(currentTimestamp).getHours();

    // Base probability on historical frequency and time distribution
    let probability = pattern.frequency * pattern.timeDistribution[currentHour];

    // Adjust based on proximity to funding
    const timingFactor = Math.exp(-Math.abs(timeTillFunding) / (30 * 60 * 1000));
    probability *= timingFactor;

    // Predict direction based on historical pattern
    const recentFlips = this.recentFlips.get(asset) || [];
    const lastFlip = recentFlips[recentFlips.length - 1];
    const predictedDirection = lastFlip ? 
      (lastFlip.direction === 'long_to_short' ? 'short_to_long' : 'long_to_short') :
      'long_to_short';

    // Confidence based on pattern consistency
    const confidence = Math.min(
      1,
      (pattern.profitability * timingFactor) + 
      (pattern.frequency * pattern.timeDistribution[currentHour])
    );

    return {
      probability: Math.min(1, probability),
      direction: predictedDirection,
      size: pattern.avgSize,
      confidence
    };
  }
} 