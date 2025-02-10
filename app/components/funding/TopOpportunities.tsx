import React from 'react';
import { FundingRate } from '../../types/funding';

interface Props {
  opportunities: FundingRate[];
}

export const TopOpportunities: React.FC<Props> = ({ opportunities }) => {
  // Split opportunities into directional and cross-exchange
  const directionalOpps = opportunities
    .sort((a, b) => Math.abs(b.funding_rate) - Math.abs(a.funding_rate))
    .slice(0, 25);

  const crossExchangeOpps = opportunities
    .reduce((acc, curr) => {
      const existing = acc.find(x => x.symbol === curr.symbol);
      if (existing && existing.exchange !== curr.exchange) {
        const spread = Math.abs(existing.funding_rate - curr.funding_rate);
        return [...acc, { ...curr, spread }];
      }
      return [...acc, curr];
    }, [] as (FundingRate & { spread?: number })[])
    .filter(x => x.spread)
    .sort((a, b) => (b.spread || 0) - (a.spread || 0))
    .slice(0, 25);

  return (
    <div className="grid grid-cols-2 gap-4 mt-4">
      {/* Directional Opportunities */}
      <div className="bg-white rounded-lg shadow p-4">
        <h3 className="text-lg font-semibold mb-4">🎯 Directional Opportunities</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead>
              <tr className="border-b">
                <th className="px-4 py-2">Symbol</th>
                <th className="px-4 py-2">Position</th>
                <th className="px-4 py-2">Rate</th>
                <th className="px-4 py-2">Predicted</th>
                <th className="px-4 py-2">APR</th>
              </tr>
            </thead>
            <tbody>
              {directionalOpps.map((opp, idx) => (
                <tr key={`${opp.symbol}-${opp.exchange}`} 
                    className={idx % 2 === 0 ? 'bg-gray-50' : ''}>
                  <td className="px-4 py-2">{opp.symbol}</td>
                  <td className="px-4 py-2">
                    <span className={`px-2 py-1 rounded ${
                      opp.funding_rate < 0 ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {opp.funding_rate < 0 ? '🟢 Long' : '🔴 Short'}
                    </span>
                  </td>
                  <td className="px-4 py-2">{opp.funding_rate.toFixed(4)}%</td>
                  <td className="px-4 py-2">{opp.predicted_rate.toFixed(4)}%</td>
                  <td className="px-4 py-2">{opp.annualized_rate.toFixed(2)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Cross-Exchange Opportunities */}
      <div className="bg-white rounded-lg shadow p-4">
        <h3 className="text-lg font-semibold mb-4">🔄 Cross-Exchange Arbitrage</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead>
              <tr className="border-b">
                <th className="px-4 py-2">Symbol</th>
                <th className="px-4 py-2">Strategy</th>
                <th className="px-4 py-2">Spread</th>
                <th className="px-4 py-2">Annual Return</th>
              </tr>
            </thead>
            <tbody>
              {crossExchangeOpps.map((opp, idx) => (
                <tr key={opp.symbol} className={idx % 2 === 0 ? 'bg-gray-50' : ''}>
                  <td className="px-4 py-2">{opp.symbol}</td>
                  <td className="px-4 py-2">
                    <span className={`px-2 py-1 rounded ${
                      opp.spread && opp.spread > 0 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {opp.spread && opp.spread > 0 
                        ? '🟢 Long Bin/Short HL' 
                        : '🔴 Short Bin/Long HL'}
                    </span>
                  </td>
                  <td className="px-4 py-2">{opp.spread?.toFixed(4)}%</td>
                  <td className="px-4 py-2">
                    {((opp.spread || 0) * 365 * 24).toFixed(2)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}; 