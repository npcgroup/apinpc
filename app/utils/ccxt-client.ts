import ccxt from 'ccxt';
import type { FundingRateSnapshot } from '@/types/supabase';

export const exchanges = {
  hyperliquid: new ccxt.hyperliquid({
    apiKey: process.env.HYPERLIQUID_API_KEY,
    secret: process.env.HYPERLIQUID_SECRET
  }),
  bybit: new ccxt.bybit({
    apiKey: process.env.BYBIT_API_KEY,
    secret: process.env.BYBIT_SECRET
  })
};

export async function fetchPerpData(): Promise<Omit<FundingRateSnapshot, 'id'>[]> {
  const results: Omit<FundingRateSnapshot, 'id'>[] = [];
  
  for (const [exchangeName, exchange] of Object.entries(exchanges)) {
    try {
      console.log(`Fetching data from ${exchangeName}...`);
      await exchange.loadMarkets();
      const markets = await exchange.fetchMarkets();
      
      const perpMarkets = markets.filter(market => 
        market.type === 'swap' || market.linear === true
      );

      console.log(`Found ${perpMarkets.length} perp markets on ${exchangeName}`);

      for (const market of perpMarkets) {
        try {
          const ticker = await exchange.fetchTicker(market.symbol);
          const fundingRate = await exchange.fetchFundingRate(market.symbol);
          
          if (!ticker || !fundingRate) {
            console.log(`Skipping ${market.symbol} due to missing data`);
            continue;
          }

          results.push({
            token: market.baseAsset || market.base,
            exchange: exchangeName,
            timestamp: new Date().toISOString(),
            current_funding_rate: fundingRate.fundingRate || 0,
            predicted_funding_rate: fundingRate.predictedFundingRate || fundingRate.fundingRate || 0,
            mark_price: ticker.last || 0,
            open_interest: market.info?.openInterest || 0,
            notional_open_interest: (market.info?.openInterest || 0) * (ticker.last || 0),
            volume_24h: ticker.quoteVolume || 0,
            avg_24h_funding_rate: fundingRate.fundingRate || 0,
            metadata: {
              funding_difference: Math.abs(
                (fundingRate.predictedFundingRate || 0) - (fundingRate.fundingRate || 0)
              )
            }
          });
          console.log(`Successfully fetched data for ${market.symbol}`);
        } catch (marketError) {
          console.error(`Error fetching data for ${market.symbol} on ${exchangeName}:`, marketError);
          continue;
        }
      }
    } catch (error) {
      console.error(`Error fetching data from ${exchangeName}:`, error);
    }
  }
  
  console.log(`Total markets fetched: ${results.length}`);
  return results;
} 