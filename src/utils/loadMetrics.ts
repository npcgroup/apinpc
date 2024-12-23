import fs from 'fs';
import path from 'path';
import { TokenMetric, DexPair, MetricsData } from '../types/metrics';

export function getLatestDataFile(directory: string): string | null {
  const files = fs.readdirSync(directory)
    .filter(file => file.endsWith('.json'))
    .sort()
    .reverse();
  
  return files[0] || null;
}

export function loadMetricsData(): MetricsData {
  const dataDir = path.join(process.cwd(), 'data');
  
  // Load token metrics
  const tokenMetricsDir = path.join(dataDir, 'token_metrics');
  const latestTokenFile = getLatestDataFile(tokenMetricsDir);
  const tokens: TokenMetric[] = latestTokenFile 
    ? JSON.parse(fs.readFileSync(path.join(tokenMetricsDir, latestTokenFile), 'utf-8'))
    : [];

  // Load DEX pairs
  const dexPairsDir = path.join(dataDir, 'dexscreener');
  const latestPairsFile = getLatestDataFile(dexPairsDir);
  const pairs: DexPair[] = latestPairsFile
    ? JSON.parse(fs.readFileSync(path.join(dexPairsDir, latestPairsFile), 'utf-8'))
    : [];

  return { tokens, pairs };
}

export function getTokenMetrics(address?: string): TokenMetric[] {
  const { tokens } = loadMetricsData();
  
  if (address) {
    return tokens.filter((token: TokenMetric) => 
      token.address.toLowerCase() === address.toLowerCase()
    );
  }
  
  return tokens;
}

export function getDexPairs(pairAddress?: string): DexPair[] {
  const { pairs } = loadMetricsData();
  
  if (pairAddress) {
    return pairs.filter((pair: DexPair) => 
      pair.pair_address.toLowerCase() === pairAddress.toLowerCase()
    );
  }
  
  return pairs;
}

export function getTokenStats() {
  const { tokens } = loadMetricsData();
  
  return {
    totalTokens: tokens.length,
    totalMarketCap: tokens.reduce((sum: number, token: TokenMetric) => 
      sum + (token.marketCap || 0), 0),
    averagePrice: tokens.reduce((sum: number, token: TokenMetric) => 
      sum + (token.price || 0), 0) / tokens.length,
    totalVolume24h: tokens.reduce((sum: number, token: TokenMetric) => 
      sum + (token.volume24h || 0), 0),
  };
} 