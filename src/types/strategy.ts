import { PerpetualMetrics } from './perpetuals';

export interface StrategyResult {
  signal: 'LONG' | 'SHORT' | 'NONE';
  size?: number;
  expectedReturn?: number;
  reason?: string;
  metrics?: {
    [key: string]: number;
  };
}

export interface Position {
  id: string;
  symbol: string;
  direction: 'LONG' | 'SHORT';
  size: number;
  entryPrice: number;
  metric: PerpetualMetrics;
  timestamp: Date;
  status: 'OPEN' | 'CLOSED';
}

export type Signal = 'LONG' | 'SHORT' | 'NONE';

export interface Strategy {
  analyze(metric: PerpetualMetrics): StrategyResult;
  validateEntry(position: Position): boolean;
  shouldExit(position: Position, currentMetric: PerpetualMetrics): boolean;
} 