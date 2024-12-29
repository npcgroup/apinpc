import React, { useState, useEffect } from 'react'
import { TokenMetrics, DexPair } from '@/types/metrics'
import { loadTokenMetrics, loadDexPairs } from '@/utils/loadMetrics'
import { formatNumber } from '@/utils/metrics'

interface MetricsDisplayProps {
  symbol: string;
  onUpdate?: (metrics: TokenMetrics) => void;
}

export function MetricsDisplay({ symbol, onUpdate }: MetricsDisplayProps) {
  const [metrics, setMetrics] = useState<TokenMetrics | null>(null)
  const [pairs, setPairs] = useState<DexPair[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        const [tokenMetrics, dexPairs] = await Promise.all([
          loadTokenMetrics(symbol),
          loadDexPairs(symbol)
        ])
        
        setMetrics(tokenMetrics)
        setPairs(dexPairs)
        onUpdate?.(tokenMetrics)
        setError(null)
      } catch (err) {
        console.error('Error fetching metrics:', err)
        setError(err instanceof Error ? err.message : 'Failed to load metrics')
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [symbol, onUpdate])

  if (loading) {
    return (
      <div className="animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
        <div className="h-4 bg-gray-200 rounded w-1/2"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-red-500">
        Error: {error}
      </div>
    )
  }

  if (!metrics) {
    return null
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-gray-800 p-4 rounded-lg">
          <h3 className="text-lg font-semibold mb-2">Price</h3>
          <div className="text-2xl">${formatNumber(metrics.price)}</div>
          <div className={`text-sm ${metrics.priceChange24h >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {metrics.priceChange24h > 0 ? '+' : ''}{metrics.priceChange24h.toFixed(2)}%
          </div>
        </div>

        <div className="bg-gray-800 p-4 rounded-lg">
          <h3 className="text-lg font-semibold mb-2">Volume (24h)</h3>
          <div className="text-2xl">${formatNumber(metrics.volume24h)}</div>
        </div>
      </div>

      {pairs.length > 0 && (
        <div className="mt-4">
          <h3 className="text-lg font-semibold mb-2">DEX Pairs</h3>
          <div className="space-y-2">
            {pairs.map((pair) => (
              <div key={pair.address} className="bg-gray-800 p-4 rounded-lg">
                <div className="flex justify-between">
                  <span>{pair.baseToken}/{pair.quoteToken}</span>
                  <span>${formatNumber(pair.price)}</span>
                </div>
                <div className="text-sm text-gray-400">
                  Volume: ${formatNumber(pair.volume24h)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
} 