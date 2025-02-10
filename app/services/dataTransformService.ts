import { FundingRate, FundingStats } from '../types/funding';

export class DataTransformService {
  static processDirectionalOpportunities(rates: FundingRate[]) {
    // Mirror the Streamlit directional opportunities logic
    const directionalDf = [...rates];
    
    // Sort by absolute funding rate
    return directionalDf
      .sort((a, b) => Math.abs(b.funding_rate) - Math.abs(a.funding_rate))
      .slice(0, 25)
      .map(rate => ({
        ...rate,
        position: rate.funding_rate < 0 ? "🟢 Long" : "🔴 Short",
        annualized_rate: rate.funding_rate * 365 * 24
      }));
  }

  static processCrossExchangeOpportunities(rates: FundingRate[]) {
    const binanceRates = rates.filter(r => r.exchange === 'Binance');
    const hlRates = rates.filter(r => r.exchange === 'Hyperliquid');
    
    const arbOpportunities = [];
    
    // Mirror the Streamlit cross-exchange logic
    for (const bRate of binanceRates) {
      const symbol = bRate.symbol.replace('USDT', '').replace('PERP', '').trim();
      const hlRate = hlRates.find(r => 
        r.symbol.replace('USDT', '').replace('PERP', '').trim() === symbol
      );
      
      if (hlRate) {
        const spread = bRate.funding_rate - hlRate.funding_rate;
        if (Math.abs(spread) > 0.0001) {
          arbOpportunities.push({
            symbol,
            spread,
            binance_rate: bRate.funding_rate,
            hyperliquid_rate: hlRate.funding_rate,
            strategy: spread < 0 ? "🟢 Long Bin/Short HL" : "🔴 Short Bin/Long HL",
            annual_return: Math.abs(spread) * 365 * 24
          });
        }
      }
    }
    
    return arbOpportunities
      .sort((a, b) => b.annual_return - a.annual_return)
      .slice(0, 25);
  }

  static processDetailedView(rates: FundingRate[]) {
    return rates.map(rate => ({
      ...rate,
      rate_diff: Math.abs(rate.predicted_rate - rate.funding_rate),
      next_funding: `${rate.time_to_funding?.toFixed(1)}h`,
      suggested_position: rate.funding_rate < 0 ? "Long" : "Short",
      opportunity_score: rate.opportunity_score || 
        Math.abs(rate.funding_rate) * (1 + Math.abs(rate.predicted_rate - rate.funding_rate))
    })).sort((a, b) => b.opportunity_score - a.opportunity_score);
  }
} 