import { PerpetualMetrics } from '../../types/perpetuals';
import { StrategyResult, Position, Strategy } from '../../types/strategy';

interface FundingConfig {
  minFundingRate: number;    // Minimum funding rate to trigger
  maxSlippage: number;       // Maximum allowed slippage
  minLiquidity: number;      // Minimum required liquidity
  positionSizePercent: number; // Position size as % of liquidity
}

export class FundingArbitrageStrategy implements Strategy {
  private config: FundingConfig;

  constructor(config: FundingConfig) {
    this.config = config;
  }

  analyze(metric: PerpetualMetrics): StrategyResult {
    // Calculate annualized funding rate
    const annualizedFunding = metric.funding_rate * 24 * 365;
    
    // Calculate price deviation
    const priceDiff = (metric.mark_price - metric.spot_price) / metric.spot_price;
    
    // Check if opportunity exists
    const isValid = 
      Math.abs(annualizedFunding) > this.config.minFundingRate &&
      Math.abs(priceDiff) < this.config.maxSlippage &&
      metric.liquidity > this.config.minLiquidity;

    if (!isValid) {
      return { signal: 'NONE', reason: 'No valid opportunity' };
    }

    // Calculate position size
    const positionSize = Math.min(
      metric.liquidity * this.config.positionSizePercent,
      metric.open_interest * 0.05
    );

    // Determine direction
    const direction = priceDiff > 0 ? 'SHORT' : 'LONG';
    
    // Calculate expected return
    const expectedReturn = Math.abs(annualizedFunding) - Math.abs(priceDiff);

    return {
      signal: direction,
      size: positionSize,
      expectedReturn,
      metrics: {
        annualizedFunding,
        priceDiff,
        impliedYield: expectedReturn * 100
      }
    };
  }

  validateEntry(position: Position): boolean {
    return position.size <= position.metric.liquidity * this.config.positionSizePercent;
  }

  shouldExit(position: Position, currentMetric: PerpetualMetrics): boolean {
    const currentPriceDiff = (currentMetric.mark_price - currentMetric.spot_price) / 
                            currentMetric.spot_price;
    
    return Math.abs(currentPriceDiff) > this.config.maxSlippage * 2 ||
           currentMetric.funding_rate * 24 * 365 < this.config.minFundingRate / 2;
  }
} 