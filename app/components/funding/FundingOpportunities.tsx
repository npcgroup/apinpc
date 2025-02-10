'use client'

import { Card } from '../ui/card'
import { formatPercent, formatNumber, formatUSD } from '@/lib/formatters'
import { FundingRate } from '../types/funding'

interface Props {
  directional: FundingRate[];
  crossExchange: Array<{
    symbol: string;
    spread: number;
    binance_rate: number;
    hyperliquid_rate: number;
    strategy: string;
    annual_return: number;
  }>;
}

export const FundingOpportunities: React.FC<Props> = ({ 
  directional, 
  crossExchange 
}) => {
  return (
    <div className="space-y-8">
      {/* Directional Opportunities */}
      <div>
        <h3 className="text-xl font-semibold mb-4">Top Directional Opportunities</h3>
        {/* Render directional opportunities table */}
      </div>

      {/* Cross-Exchange Opportunities */}
      <div>
        <h3 className="text-xl font-semibold mb-4">Cross-Exchange Opportunities</h3>
        {/* Render cross-exchange opportunities table */}
      </div>
    </div>
  );
}; 