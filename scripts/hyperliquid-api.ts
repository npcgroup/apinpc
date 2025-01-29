import fetch from 'node-fetch';

interface FundingRate {
  asset: string;
  predicted: number;
  timestamp: number;
}

interface FundingAnalysis {
  topOpportunities: FundingRate[];
  statistics: {
    totalPairs: number;
    pairsWithFunding: number;
    positiveRates: number;
    negativeRates: number;
    highestRate: FundingRate | null;
    averageRate: number;
  };
}

interface ExchangeData {
  fundingRate: string;
  nextFundingTime: number;
}

type HyperLiquidResponse = [string, Array<[string, ExchangeData | null]>][];

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
    
    // Transform the response into a more readable format
    return rawData
      .map(([asset, exchangeData]) => {
        // Find HyperLiquid data (marked as "HlPerp" in the response)
        const hlData = exchangeData.find(([exchange]) => exchange === 'HlPerp')?.[1];
        
        if (!hlData) return null;

        const predicted = parseFloat(hlData.fundingRate);
        
        return {
          asset,
          predicted: isNaN(predicted) ? 0 : predicted,
          timestamp: Date.now()
        };
      })
      .filter((rate): rate is FundingRate => 
        rate !== null && 
        !isNaN(rate.predicted) &&
        rate.predicted !== 0
      );
  }

  /**
   * Get predicted funding rate for a specific asset
   */
  async getPredictedFundingRate(asset: string): Promise<FundingRate | null> {
    const rates = await this.getPredictedFundingRates();
    return rates.find(rate => rate.asset === asset) || null;
  }

  /**
   * Analyze funding rates data
   */
  analyzeFundingRates(rates: FundingRate[], topN: number = 5): FundingAnalysis {
    const validRates = rates.filter(rate => !isNaN(rate.predicted) && rate.predicted !== 0);
    const sortedRates = validRates.sort((a, b) => Math.abs(b.predicted) - Math.abs(a.predicted));
    
    const positiveRates = validRates.filter(r => r.predicted > 0);
    const negativeRates = validRates.filter(r => r.predicted < 0);
    const averageRate = validRates.length > 0 
      ? validRates.reduce((sum, rate) => sum + rate.predicted, 0) / validRates.length
      : 0;

    return {
      topOpportunities: sortedRates.slice(0, topN),
      statistics: {
        totalPairs: rates.length,
        pairsWithFunding: validRates.length,
        positiveRates: positiveRates.length,
        negativeRates: negativeRates.length,
        highestRate: sortedRates[0] || null,
        averageRate
      }
    };
  }

  /**
   * Format funding rate for display
   */
  formatFundingRate(rate: FundingRate, includeAnnualized: boolean = true): string {
    const fundingPercent = (rate.predicted * 100).toFixed(6);
    const direction = rate.predicted >= 0 ? 'LONGS PAY' : 'SHORTS PAY';
    const annualized = (rate.predicted * 100 * 365).toFixed(2);
    
    return includeAnnualized
      ? `${rate.asset.padEnd(10)} ${fundingPercent.padStart(10)}% (${annualized}% APR) - ${direction}`
      : `${rate.asset.padEnd(10)} ${fundingPercent.padStart(10)}% (${direction})`;
  }
} 