export class FootprintClient {
  private baseUrl = 'https://api.footprint.network/api/v1';
  private apiKey: string;

  constructor(apiKey: string) {
    this.apiKey = apiKey;
  }

  async getProtocolMetrics(protocol: string): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/protocol/${protocol}`, {
        headers: {
          'Authorization': `Bearer ${this.apiKey}`
        }
      });

      if (!response.ok) {
        console.warn(`Failed to fetch Footprint metrics for ${protocol}`);
        return {};
      }

      const data = await response.json();
      return {
        tvl: data.tvl || 0,
        volume24h: data.volume24h || 0,
        users24h: data.users24h || 0,
        transactions24h: data.transactions24h || 0
      };
    } catch (error) {
      console.error(`Error fetching Footprint data for ${protocol}:`, error);
      return {};
    }
  }
} 