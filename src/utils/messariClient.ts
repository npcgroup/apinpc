export class MessariClient {
  private baseUrl = 'https://data.messari.io/api/v1';
  private apiKey: string;

  constructor(apiKey: string) {
    this.apiKey = apiKey;
  }

  async getAssetMetrics(asset: string): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/assets/${asset}/metrics`, {
        headers: {
          'x-messari-api-key': this.apiKey
        }
      });

      if (!response.ok) {
        console.warn(`Failed to fetch Messari metrics for ${asset}`);
        return {};
      }

      const data = await response.json();
      return {
        price: data.data?.market_data?.price_usd || 0,
        volume24h: data.data?.market_data?.volume_last_24_hours || 0,
        marketCap: data.data?.marketcap?.current_marketcap_usd || 0,
        supply: data.data?.supply?.circulating || 0
      };
    } catch (error) {
      console.error(`Error fetching Messari data for ${asset}:`, error);
      return {};
    }
  }
} 