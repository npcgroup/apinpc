import { TokenDetailsData } from '../types/api';
import { Token } from '../types/tokens';

export class CoinGeckoClient {
  private baseUrl = 'https://api.coingecko.com/api/v3';
  private retryDelay = 1000; // 1 second
  private maxRetries = 3;

  private async fetchWithRetry(url: string, retries = 0): Promise<any> {
    try {
      const response = await fetch(url);
      
      if (response.status === 429 && retries < this.maxRetries) {
        console.warn(`Rate limited by CoinGecko, retrying in ${this.retryDelay}ms...`);
        await new Promise(resolve => setTimeout(resolve, this.retryDelay));
        return this.fetchWithRetry(url, retries + 1);
      }

      if (!response.ok) {
        throw new Error(`CoinGecko API error: ${response.status} ${response.statusText}`);
      }

      return response.json();
    } catch (error) {
      if (retries < this.maxRetries) {
        console.warn(`Failed to fetch from CoinGecko, retrying in ${this.retryDelay}ms...`);
        await new Promise(resolve => setTimeout(resolve, this.retryDelay));
        return this.fetchWithRetry(url, retries + 1);
      }
      throw error;
    }
  }

  async getTopTokens(): Promise<Token[]> {
    try {
      console.log('Fetching top tokens from CoinGecko...');
      
      const data = await this.fetchWithRetry(
        `${this.baseUrl}/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=250&page=1&sparkline=false`
      );

      console.log(`Fetched ${data.length} tokens from CoinGecko`);

      return data.map((token: any) => ({
        address: token.id,
        symbol: token.symbol.toUpperCase(),
        name: token.name,
        price: token.current_price,
        volume24h: token.total_volume,
        marketCap: token.market_cap,
        totalSupply: token.total_supply
      }));
    } catch (error) {
      console.error('Error fetching top tokens from CoinGecko:', error);
      return [];
    }
  }

  async getTokenAddresses(): Promise<Map<string, string>> {
    try {
      const data = await this.fetchWithRetry(`${this.baseUrl}/coins/list?include_platform=true`);
      
      const addressMap = new Map<string, string>();
      data.forEach((token: any) => {
        if (token.platforms?.ethereum) {
          addressMap.set(token.id, token.platforms.ethereum);
        }
      });
      
      return addressMap;
    } catch (error) {
      console.error('Error fetching token addresses from CoinGecko:', error);
      return new Map();
    }
  }

  async getTokenDetails(tokenId: string): Promise<TokenDetailsData> {
    try {
      const data = await this.fetchWithRetry(
        `${this.baseUrl}/coins/${tokenId}?localization=false&tickers=false&community_data=false&developer_data=false`
      );

      return {
        price: data.market_data?.current_price?.usd || 0,
        marketCap: data.market_data?.market_cap?.usd || 0,
        volume24h: data.market_data?.total_volume?.usd || 0,
        totalSupply: data.market_data?.total_supply
      };
    } catch (error) {
      console.error('Error fetching token details from CoinGecko:', error);
      return {
        price: 0,
        marketCap: 0,
        volume24h: 0
      };
    }
  }
} 