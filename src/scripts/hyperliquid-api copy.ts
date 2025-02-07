import fetch from 'node-fetch';

interface FundingRate {
  asset: string;
  predicted: number;
  timestamp: number;
}

// Define the expected response type from HyperLiquid API
type HyperLiquidResponse = [string, string][];

export class HyperLiquidAPI {
  private readonly baseUrl: string;

  constructor() {
    this.baseUrl = 'https://api.hyperliquid.xyz';
  }

  /**
   * Get predicted funding rates for all assets
   */
  async getPredictedFundingRates(): Promise<FundingRate[]> {
    const response = await fetch(`${this.baseUrl}/info`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        type: 'predictedFundings'
      })
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API Error ${response.status}: ${errorText}`);
    }

    const rawData = await response.json() as HyperLiquidResponse;
    console.log('Raw API response:', JSON.stringify(rawData, null, 2));

    // Transform the response into a more readable format
    return rawData.map(([asset, predictedRate]) => {
      const predicted = parseFloat(predictedRate);
      return {
        asset,
        predicted: isNaN(predicted) ? 0 : predicted,  // Default to 0 if NaN
        timestamp: Date.now()
      };
    });
  }

  /**
   * Get predicted funding rate for a specific asset
   */
  async getPredictedFundingRate(asset: string): Promise<FundingRate | null> {
    const rates = await this.getPredictedFundingRates();
    return rates.find(rate => rate.asset === asset) || null;
  }
} 