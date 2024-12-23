import { TokenMetrics } from '@/types/database';

export interface DuneMetrics {
  volume24h?: number;
  fees24h?: number;
  users24h?: number;
  transactions24h?: number;
  activeAddresses24h?: number;
  trades24h?: number;
  uniqueTraders24h?: number;
  totalBorrowed?: number;
  totalSupplied?: number;
  borrowApy?: number;
  supplyApy?: number;
  openInterest?: number;
}

// Create a separate interface for Dune's token response
interface DuneTokenResponse {
  volume_24h: number;
  holders: number;
  total_supply: number;
}

export class DuneClient {
  private apiKey: string;
  private baseUrl = 'https://api.dune.com/api/v1';

  constructor(apiKey: string) {
    if (!apiKey) {
      throw new Error('Dune API key is required');
    }
    this.apiKey = apiKey;
  }

  async executeQuery(query: string): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/query/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Dune-API-Key': this.apiKey
        },
        body: JSON.stringify({
          query,
          parameters: {}
        })
      });
      
      if (!response.ok) {
        throw new Error(`Dune API error: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      throw new Error(`Failed to execute Dune query: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async getProtocolMetrics(protocol: string): Promise<DuneMetrics> {
    // Implement Dune API call
    return {};
  }

  async getChainMetrics(chain: string): Promise<DuneMetrics> {
    // Implement Dune API call
    return {};
  }

  async getDexMetrics(dex: string): Promise<DuneMetrics> {
    // Implement Dune API call
    return {};
  }

  async getLendingMetrics(protocol: string): Promise<DuneMetrics> {
    // Implement Dune API call
    return {};
  }

  async getDerivativesMetrics(protocol: string): Promise<DuneMetrics> {
    // Implement Dune API call
    return {};
  }

  async getTokenMetrics(address: string): Promise<TokenMetrics> {
    try {
      const query = `
        SELECT 
          SUM(t.value * p.price) as volume_24h,
          COUNT(DISTINCT t.to) as holders,
          MAX(t.total_supply) as total_supply
        FROM erc20_transfers t
        LEFT JOIN token_prices p ON t.token = p.token_address
        WHERE t.token = '${address}'
          AND t.block_time >= NOW() - INTERVAL '24 hours'
        GROUP BY t.token;
      `;

      const result = await this.executeQuery(query);
      
      // Return object matching TokenMetrics interface
      return {
        address,
        symbol: '', // This should be populated from elsewhere
        name: '', // This should be populated from elsewhere
        price: 0, // This should be populated from elsewhere
        volume24h: result[0]?.volume_24h || 0,
        marketCap: 0, // This should be populated from elsewhere
        totalSupply: result[0]?.total_supply || 0,
        timestamp: new Date()
      };
    } catch (error) {
      console.error(`Error fetching token metrics from Dune for ${address}:`, error);
      
      // Return default values matching TokenMetrics interface
      return {
        address,
        symbol: '',
        name: '',
        price: 0,
        volume24h: 0,
        marketCap: 0,
        totalSupply: 0,
        timestamp: new Date()
      };
    }
  }
} 