import { config } from 'dotenv';
import { createClient } from '@supabase/supabase-js';
import { StrategyRunner } from '../strategies/StrategyRunner';
import { MarkovRegimeFundingStrategy } from '../strategies/funding_rate_regime/MarkovRegimeFundingStrategy';
import { LiquidityImpactStrategy } from '../strategies/market_impact/LiquidityImpactStrategy';
import { CrossExchangeArbitrageStrategy } from '../strategies/arbitrage/CrossExchangeArbitrageStrategy';
import { FundingVolatilityStrategy } from '../strategies/volatility_clustering/FundingVolatilityStrategy';
import { BasisTradingStrategy } from '../strategies/basis_trading/BasisTradingStrategy';
import { LiquidationCascadeStrategy } from '../strategies/liquidation/LiquidationCascadeStrategy';
import { MarginHealthStrategy } from '../strategies/margin/MarginHealthStrategy';
import { PositionFlipStrategy } from '../strategies/funding_rate_regime/PositionFlipStrategy';
import { OrderFlowStrategy } from '../strategies/market_impact/OrderFlowStrategy';

// Load environment variables
config();

const ASSETS = ['BTC', 'ETH', 'SOL', 'ARB', 'OP'];
const EXCHANGES = ['binance', 'hyperliquid', 'bybit'];

async function main() {
  // Validate environment variables
  const requiredEnvVars = [
    'SUPABASE_URL',
    'SUPABASE_KEY'
  ];

  for (const envVar of requiredEnvVars) {
    if (!process.env[envVar]) {
      throw new Error(`Missing required environment variable: ${envVar}`);
    }
  }

  // Initialize Supabase client
  const supabaseClient = createClient(
    process.env.SUPABASE_URL!,
    process.env.SUPABASE_KEY!
  );

  // Initialize strategies
  const strategies = [
    new MarkovRegimeFundingStrategy({
      name: 'funding_regime_analysis',
      description: 'Analyzes funding rate regimes using Markov models',
      parameters: {
        lookbackPeriodDays: 30,
        minSampleSize: 100,
        regimeCount: 3,
        confidenceThreshold: 0.7,
        assets: ASSETS
      }
    }, supabaseClient),

    new LiquidityImpactStrategy({
      name: 'liquidity_impact_analysis',
      description: 'Analyzes market impact and liquidity conditions',
      parameters: {
        assets: ASSETS,
        tradeQuintiles: [0.2, 0.4, 0.6, 0.8],
        impactWindowMinutes: 60,
        minTradeCount: 50,
        significanceLevel: 0.05
      }
    }, supabaseClient),

    new CrossExchangeArbitrageStrategy({
      name: 'cross_exchange_arbitrage',
      description: 'Analyzes cross-exchange funding rate arbitrage opportunities',
      parameters: {
        assets: ASSETS,
        exchanges: EXCHANGES,
        minProfitThreshold: 0.0001, // 1 basis point
        maxSlippageTolerance: 0.002, // 20 basis points
        minLiquidityRequired: 100000, // $100k minimum liquidity
        rebalanceThreshold: 0.005 // 50 basis points
      }
    }, supabaseClient),

    new FundingVolatilityStrategy({
      name: 'funding_volatility_clustering',
      description: 'Analyzes funding rate volatility clustering during market stress',
      parameters: {
        assets: ASSETS,
        lookbackDays: 30,
        volatilityThreshold: 0.002, // 20 basis points
        clusterMinSize: 3,
        stressEventThreshold: 0.005 // 50 basis points
      }
    }, supabaseClient),

    new BasisTradingStrategy({
      name: 'basis_trading_efficiency',
      description: 'Analyzes basis trading efficiency between perpetuals and spot',
      parameters: {
        assets: ASSETS,
        exchanges: EXCHANGES,
        minBasisThreshold: 0.001, // 10 basis points
        lookbackPeriodHours: 24,
        minSpotLiquidity: 50000, // $50k minimum spot liquidity
        minPerpLiquidity: 100000, // $100k minimum perp liquidity
        rebalanceThreshold: 0.003 // 30 basis points
      }
    }, supabaseClient),

    new LiquidationCascadeStrategy({
      name: 'liquidation_cascade_analysis',
      description: 'Analyzes and predicts liquidation cascades',
      parameters: {
        assets: ASSETS,
        lookbackPeriodHours: 48,
        minCascadeSize: 5,
        priceImpactThreshold: 0.02, // 2% price impact
        liquidationThreshold: 0.0375, // 3.75% margin ratio
        riskWindowMinutes: 60
      }
    }, supabaseClient),

    new MarginHealthStrategy({
      name: 'margin_health_scoring',
      description: 'Analyzes and forecasts margin health scores',
      parameters: {
        assets: ASSETS,
        lookbackPeriodHours: 24,
        marginThresholds: {
          critical: 0.0375, // 3.75%
          warning: 0.05, // 5%
          healthy: 0.1 // 10%
        },
        volatilityWindowSize: 24,
        forecastHorizonMinutes: 60,
        confidenceLevel: 0.95
      }
    }, supabaseClient),

    new PositionFlipStrategy({
      name: 'position_flip_analysis',
      description: 'Analyzes position flips around funding timestamps',
      parameters: {
        assets: ASSETS,
        windowMinutesBefore: 30,
        windowMinutesAfter: 30,
        minPositionSize: 100000, // $100k minimum position size
        significanceThreshold: 0.02, // 2% price impact
        minFlipCount: 3
      }
    }, supabaseClient),

    new OrderFlowStrategy({
      name: 'order_flow_analysis',
      description: 'Analyzes order flow and detects toxic flow patterns',
      parameters: {
        assets: ASSETS,
        windowSizeMinutes: 15,
        toxicityThreshold: 0.7,
        minOrderSize: 50000, // $50k minimum order size
        volumeOutlierThreshold: 0.6, // 60% imbalance
        priceImpactThreshold: 0.01 // 1% price impact
      }
    }, supabaseClient)
  ];

  // Initialize and start the strategy runner
  const runner = new StrategyRunner({
    supabaseUrl: process.env.SUPABASE_URL!,
    supabaseKey: process.env.SUPABASE_KEY!,
    strategies,
    executionIntervalMs: 5 * 60 * 1000, // Run every 5 minutes
    errorRetryCount: 3,
    errorRetryDelayMs: 30 * 1000 // 30 seconds
  });

  // Handle shutdown signals
  process.on('SIGINT', async () => {
    console.log('Received SIGINT signal');
    await runner.stop();
    process.exit(0);
  });

  process.on('SIGTERM', async () => {
    console.log('Received SIGTERM signal');
    await runner.stop();
    process.exit(0);
  });

  // Start the runner
  try {
    await runner.start();
  } catch (error) {
    console.error('Failed to start strategy runner:', error);
    process.exit(1);
  }
}

main().catch(error => {
  console.error('Unhandled error:', error);
  process.exit(1);
}); 