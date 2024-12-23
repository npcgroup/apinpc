import { PerpetualMetrics } from '../../types/perpetuals';

export interface StrategyConfig {
  minFundingRate: number;
  maxSlippage: number;
}

export class FundingArbitrageStrategy {
  constructor(private config: StrategyConfig) {}
  
  analyze(metrics: PerpetualMetrics) {
    // Implementation
  }
} 