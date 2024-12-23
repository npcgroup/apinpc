import { TokenBoost, TokenOrder, TokenPair } from '../types/dexscreener';
import { withRetry, withTimeout } from './retryUtils';

export interface DexScreenerToken {
  tokenAddress: string;
  symbol: string;
  name: string;
  price: number;
  volume24h: number;
  marketCap: number;
  icon?: string;
  description?: string;
}

interface DexScreenerPair {
  baseToken: {
    address: string;
    symbol: string;
    name: string;
  };
  priceUsd: string;
  volume24h: string;
  marketCap: string;
}

interface DexScreenerResponse {
  pairs: DexScreenerPair[];
}

export class DexScreenerClient {
  private baseUrl = 'https://api.dexscreener.com/latest/dex';
  private rateLimit = 60; // requests per minute for most endpoints
  private pairsRateLimit = 300; // requests per minute for pairs endpoints

  async getLatestTokenProfiles(): Promise<DexScreenerToken[]> {
    try {
      const response = await fetch('https://api.dexscreener.com/latest/dex/tokens/list');
      const data = await response.json() as DexScreenerResponse;
      
      if (!data || !Array.isArray(data.pairs)) {
        throw new Error('Invalid response from DexScreener API');
      }

      return data.pairs.map((pair: DexScreenerPair) => ({
        tokenAddress: pair.baseToken.address,
        symbol: pair.baseToken.symbol,
        name: pair.baseToken.name,
        price: parseFloat(pair.priceUsd) || 0,
        volume24h: parseFloat(pair.volume24h) || 0,
        marketCap: parseFloat(pair.marketCap) || 0
      }));
    } catch (error) {
      console.error('Error fetching from DexScreener:', error);
      throw error;
    }
  }

  async getPairsByTokenAddresses(tokenAddresses: string[]): Promise<{pairs: DexScreenerPair[]}> {
    try {
      if (!tokenAddresses.length) {
        // If no addresses provided, get some default pairs
        const response = await fetch(`${this.baseUrl}/pairs/ethereum/0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2`, {
          method: 'GET',
          headers: {}
        });

        if (!response.ok) {
          throw new Error(`DexScreener API error: ${response.status} ${response.statusText}`);
        }

        return { pairs: [] };
      }

      // DexScreener allows max 30 addresses per request
      const addressesStr = tokenAddresses.slice(0, 30).join(',');
      const response = await fetch(`${this.baseUrl}/tokens/${addressesStr}`, {
        method: 'GET',
        headers: {}
      });

      if (!response.ok) {
        throw new Error(`DexScreener API error: ${response.status} ${response.statusText}`);
      }

      return { pairs: [] };
    } catch (error) {
      console.error('Error fetching pairs by token addresses:', error);
      return { pairs: [] };
    }
  }

  async searchPairs(query: string): Promise<{pairs: DexScreenerPair[]}> {
    try {
      const response = await fetch(`${this.baseUrl}/search?q=${encodeURIComponent(query)}`, {
        method: 'GET',
        headers: {}
      });

      if (!response.ok) {
        throw new Error(`DexScreener API error: ${response.status} ${response.statusText}`);
      }

      return { pairs: [] };
    } catch (error) {
      console.error('Error searching pairs:', error);
      return { pairs: [] };
    }
  }
} 