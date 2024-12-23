import { ErrorWithDetails } from '../types/errors';
import { TokenPriceData, TokenPricesResponse } from '../types/api';

export interface Protocol {
  name: string;
  tvl: number;
  chains: string[];
}

export class DefiLlamaClient {
  private baseUrl = 'https://api.llama.fi';
  private coinsUrl = 'https://coins.llama.fi';
  private lendingUrl = 'https://yields.llama.fi';

  async getTopProtocols(): Promise<any[]> {
    try {
      console.log('Fetching protocols from DefiLlama...');
      const response = await fetch(`${this.baseUrl}/protocols`);
      
      if (!response.ok) {
        throw new Error(`DefiLlama API error: ${response.status} ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log(`Fetched ${data.length} protocols from DefiLlama`);
      
      // Filter and sort by TVL
      const validProtocols = data
        .filter((p: any) => p.tvl && p.tvl > 0)
        .sort((a: any, b: any) => b.tvl - a.tvl)
        .slice(0, 100); // Get top 100 protocols

      if (validProtocols.length > 0) {
        console.log('Sample protocol data:', JSON.stringify(validProtocols[0], null, 2));
      }
      
      return validProtocols;
    } catch (error: unknown) {
      const err = error as ErrorWithDetails;
      console.error('DefiLlama client error:', {
        name: err.name || 'Unknown Error',
        message: err.message || 'An unknown error occurred',
        stack: err.stack,
        details: err.details
      });
      throw err;
    }
  }

  async getProtocolTVL(protocol: string): Promise<number> {
    try {
      // Map common protocol names to their DefiLlama slugs
      const protocolSlugMap: { [key: string]: string } = {
        'curve': 'curve-dex', // Use correct slug for Curve
        'uniswap': 'uniswap-v3',
        'aave': 'aave-v3',
        'compound': 'compound-v3',
        // Add more mappings as needed
      };

      const protocolSlug = protocolSlugMap[protocol.toLowerCase()] || protocol;
      
      console.log(`Fetching TVL for protocol: ${protocolSlug}`);
      const response = await fetch(`${this.baseUrl}/protocol/${protocolSlug}`);
      
      if (!response.ok) {
        if (response.status === 404) {
          console.warn(`Protocol ${protocolSlug} not found on DefiLlama`);
          return 0;
        }
        throw new Error(`DefiLlama API error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      
      // DefiLlama returns TVL in different formats, handle both
      const tvl = typeof data.tvl === 'number' ? 
        data.tvl : 
        Array.isArray(data.tvl) ? 
          data.tvl[data.tvl.length - 1]?.totalLiquidityUSD || 0 : 
          0;

      console.log(`TVL for ${protocolSlug}: $${tvl.toLocaleString()}`);
      return tvl;
    } catch (error) {
      console.error(`Error fetching TVL for protocol ${protocol}:`, error);
      return 0;
    }
  }

  async getChainTVL(chain: string): Promise<number> {
    // Implement DeFiLlama API call
    return 0;
  }

  async getTokenPrices(tokenAddresses?: string | string[]): Promise<TokenPricesResponse> {
    try {
      // Handle both single address and array of addresses
      const addresses = typeof tokenAddresses === 'string' 
        ? [`ethereum:${tokenAddresses}`]
        : tokenAddresses?.map(addr => `ethereum:${addr}`) || 
          ['ethereum:0x0000000000000000000000000000000000000000']; // ETH as default
      
      const queryString = addresses.join(',');
      const response = await fetch(`${this.coinsUrl}/prices/current/${queryString}`);
      
      if (!response.ok) {
        throw new Error(`DefiLlama API error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      const transformed: TokenPricesResponse = {};

      if (data?.coins) {
        Object.entries(data.coins).forEach(([key, value]: [string, any]) => {
          const [chain, address] = key.split(':');
          transformed[address.toLowerCase()] = {
            price: value.price || 0,
            totalSupply: value.totalSupply
          };
        });
      }

      return transformed;
    } catch (error) {
      console.error('Error fetching token prices from DefiLlama:', error);
      return {};
    }
  }

  private transformTokenPrices(data: any): TokenPriceData {
    if (data?.coins) {
      const firstCoin = Object.values(data.coins)[0] as any;
      return {
        price: firstCoin?.price || 0,
        totalSupply: firstCoin?.totalSupply
      };
    }
    return { price: 0 };
  }

  async getLendingProtocols(): Promise<any[]> {
    const response = await fetch(`${this.lendingUrl}/pools`);
    if (!response.ok) {
      throw new Error(`DefiLlama API error: ${response.status} ${response.statusText}`);
    }
    return response.json();
  }

  async getProtocolLendingData(protocol: string): Promise<any> {
    const response = await fetch(`${this.lendingUrl}/pool/${protocol}`);
    if (!response.ok) {
      throw new Error(`DefiLlama API error: ${response.status} ${response.statusText}`);
    }
    return response.json();
  }

  // Add method to get top tokens directly
  async getTopTokens(limit: number = 100): Promise<any[]> {
    try {
      const response = await fetch(`${this.baseUrl}/protocols`);
      if (!response.ok) {
        throw new Error(`DefiLlama API error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      return data
        .filter((p: any) => p.tvl > 0)
        .sort((a: any, b: any) => b.tvl - a.tvl)
        .slice(0, limit);
    } catch (error) {
      console.error('Error fetching top tokens from DefiLlama:', error);
      return [];
    }
  }
} 