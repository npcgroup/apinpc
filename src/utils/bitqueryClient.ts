export class BitqueryClient {
  private baseUrl = 'https://graphql.bitquery.io';
  private apiKey: string;

  constructor(apiKey: string) {
    this.apiKey = apiKey;
  }

  async getTokenMetrics(address: string): Promise<any> {
    const query = `
      query ($address: String!) {
        ethereum {
          transfers(
            date: {since: "-24h"}
            tokenAddress: {is: $address}
          ) {
            count
            senders: count(uniq: senders)
            receivers: count(uniq: receivers)
            amount
            median: amount(calculate: median)
          }
        }
      }
    `;

    try {
      const response = await fetch(this.baseUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-KEY': this.apiKey
        },
        body: JSON.stringify({
          query,
          variables: { address }
        })
      });

      if (!response.ok) {
        console.warn(`Failed to fetch Bitquery metrics for ${address}`);
        return {};
      }

      const data = await response.json();
      const metrics = data.data?.ethereum?.transfers?.[0] || {};

      return {
        transactions24h: metrics.count || 0,
        uniqueSenders24h: metrics.senders || 0,
        uniqueReceivers24h: metrics.receivers || 0,
        volume24h: metrics.amount || 0
      };
    } catch (error) {
      console.error(`Error fetching Bitquery data for ${address}:`, error);
      return {};
    }
  }
} 