import { useEffect, useState } from 'react';
import { TokenMetric, DexPair } from '../types/metrics';
import { getTokenMetrics, getDexPairs, getTokenStats } from '../utils/loadMetrics';

export default function MetricsDisplay() {
  const [tokens, setTokens] = useState<TokenMetric[]>([]);
  const [pairs, setPairs] = useState<DexPair[]>([]);
  const [stats, setStats] = useState<any>(null);

  useEffect(() => {
    // Load all data
    setTokens(getTokenMetrics());
    setPairs(getDexPairs());
    setStats(getTokenStats());
  }, []);

  return (
    <div className="p-4">
      {/* Stats Overview */}
      {stats && (
        <div className="grid grid-cols-4 gap-4 mb-8">
          <div className="p-4 bg-white rounded shadow">
            <h3>Total Tokens</h3>
            <p className="text-2xl font-bold">{stats.totalTokens}</p>
          </div>
          <div className="p-4 bg-white rounded shadow">
            <h3>Total Market Cap</h3>
            <p className="text-2xl font-bold">${stats.totalMarketCap.toLocaleString()}</p>
          </div>
          <div className="p-4 bg-white rounded shadow">
            <h3>Average Price</h3>
            <p className="text-2xl font-bold">${stats.averagePrice.toFixed(4)}</p>
          </div>
          <div className="p-4 bg-white rounded shadow">
            <h3>24h Volume</h3>
            <p className="text-2xl font-bold">${stats.totalVolume24h.toLocaleString()}</p>
          </div>
        </div>
      )}

      {/* Token List */}
      <div className="mb-8">
        <h2 className="text-xl font-bold mb-4">Tokens</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {tokens.map(token => (
            <div key={token.address} className="p-4 bg-white rounded shadow">
              <h3 className="font-bold">{token.name} ({token.symbol})</h3>
              <p>Price: ${token.price.toFixed(6)}</p>
              <p>Market Cap: ${token.marketCap?.toLocaleString()}</p>
              <p>24h Volume: ${token.volume24h?.toLocaleString()}</p>
            </div>
          ))}
        </div>
      </div>

      {/* DEX Pairs */}
      <div>
        <h2 className="text-xl font-bold mb-4">DEX Pairs</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {pairs.map(pair => (
            <div key={pair.pair_address} className="p-4 bg-white rounded shadow">
              <h3 className="font-bold">{pair.token_1_symbol}/{pair.token_2_symbol}</h3>
              <p>Price: ${pair.price_usd.toFixed(6)}</p>
              <p>Liquidity: ${pair.liquidity_usd.toLocaleString()}</p>
              <p>24h Volume: ${pair.volume_24h.toLocaleString()}</p>
              <p>24h Change: {pair.price_change_24h.toFixed(2)}%</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
} 