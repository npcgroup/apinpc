'use client'

import { useEffect, useState } from 'react'
import { format } from 'date-fns'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, BarChart, Bar } from 'recharts'
import Link from 'next/link'
import type { MarketUpdate } from '../../types/market'
import { formatNumber } from '../../src/utils/metrics'
import { ArrowUpIcon, ArrowDownIcon } from '@heroicons/react/24/outline'
import { useRouter } from 'next/navigation'

export default function MarketUpdatesPage() {
  const router = useRouter()
  const [marketData, setMarketData] = useState<MarketUpdate | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchMarketData() {
      try {
        // Fetch latest pipeline data
        const response = await fetch('/api/market-data/latest')
        if (!response.ok) throw new Error('Failed to fetch market data')
        
        const rawData = await response.json()
        
        // Process and validate the data
        const processedData: MarketUpdate = {
          timestamp: rawData.timestamp || new Date().toISOString(),
          metrics: {
            total_markets: Number(rawData.total_markets),
            total_volume: Number(rawData.total_volume),
            total_oi: Number(rawData.total_oi),
            avg_funding: Number(rawData.avg_funding_rate),
            volume_distribution: (rawData.volume_distribution || []).map((d: any) => ({
              timestamp: d.timestamp,
              volume: Number(d.volume)
            }))
          },
          opportunities: (rawData.markets || [])
            .filter((m: any) => 
              m.current_funding_rate != null && 
              m.predicted_funding_rate != null &&
              !isNaN(m.current_funding_rate) &&
              !isNaN(m.predicted_funding_rate)
            )
            .map((m: any) => ({
              token: m.symbol,
              current_funding_rate: Number(m.current_funding_rate),
              predicted_funding_rate: Number(m.predicted_funding_rate),
              notional_open_interest: Number(m.notional_open_interest),
              volume_24h: Number(m.volume_24h),
              mark_price: Number(m.mark_price)
            }))
            .sort((a, b) => 
              Math.abs(b.predicted_funding_rate - b.current_funding_rate) - 
              Math.abs(a.predicted_funding_rate - a.current_funding_rate)
            ),
          risk_metrics: {
            volume_concentration: Number(rawData.risk_metrics?.volume_concentration || 0),
            illiquid_markets: Number(rawData.risk_metrics?.illiquid_markets || 0),
            largest_drawdown: Number(rawData.risk_metrics?.largest_drawdown || 0),
            volatility_index: Number(rawData.risk_metrics?.volatility_index || 0),
            market_depth: (rawData.risk_metrics?.market_depth || []).map((d: any) => ({
              token: d.symbol,
              depth: Number(d.depth),
              utilization: Number(d.utilization)
            }))
          },
          market_data: {
            highest_funding: {
              token: rawData.highest_funding?.symbol || '',
              rate: Number(rawData.highest_funding?.rate || 0),
              volume: Number(rawData.highest_funding?.volume || 0)
            },
            most_active: {
              token: rawData.most_active?.symbol || '',
              volume: Number(rawData.most_active?.volume || 0),
              rate: Number(rawData.most_active?.funding_rate || 0)
            },
            largest_oi: {
              token: rawData.largest_oi?.symbol || '',
              oi: Number(rawData.largest_oi?.open_interest || 0),
              rate: Number(rawData.largest_oi?.funding_rate || 0)
            },
            volume_distribution: rawData.volume_distribution || []
          }
        }

        // Validate the processed data
        if (processedData.opportunities.length === 0) {
          throw new Error('No valid market opportunities found')
        }

        setMarketData(processedData)
      } catch (error) {
        console.error('Error fetching market data:', error)
        setError(error instanceof Error ? error.message : 'Failed to load market data')
      } finally {
        setLoading(false)
      }
    }

    fetchMarketData()
    const interval = setInterval(fetchMarketData, 30000) // Update every 30 seconds
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
        <div className="animate-pulse">Loading market updates...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-900 text-white flex flex-col items-center justify-center gap-4">
        <div className="text-red-400">{error}</div>
        <button 
          onClick={() => router.refresh()}
          className="px-4 py-2 bg-gray-800 rounded hover:bg-gray-700"
        >
          Retry
        </button>
      </div>
    )
  }

  return (
    <main className="min-h-screen bg-gray-900 text-white p-8">
      {/* Navigation Bar */}
      <nav className="max-w-7xl mx-auto mb-8 flex justify-between items-center">
        <Link 
          href="/"
          className="inline-flex items-center px-4 py-2 bg-gray-800 rounded-lg hover:bg-gray-700 transition-colors"
        >
          <span className="mr-2">←</span> Back to Terminal
        </Link>
        <Link
          href="/perp-metrics"
          className="px-4 py-2 bg-purple-600 rounded-lg hover:bg-purple-700 transition-colors"
        >
          View Detailed Metrics →
        </Link>
      </nav>

      {marketData && (
        <div className="max-w-7xl mx-auto space-y-8">
          {/* Existing content */}
          <div className="text-center">
            <h1 className="text-4xl font-bold mb-4">{marketData.title}</h1>
            <p className="text-gray-400">{marketData.summary}</p>
          </div>

          {/* Enhanced Metrics Grid */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-gray-800 rounded-lg p-6 hover:bg-gray-700 transition-colors">
              <h3 className="text-gray-400 mb-2">Total Markets</h3>
              <p className="text-3xl font-bold">{marketData.metrics.total_markets}</p>
            </div>
            <div className="bg-gray-800 rounded-lg p-6 hover:bg-gray-700 transition-colors">
              <h3 className="text-gray-400 mb-2">24h Volume</h3>
              <p className="text-3xl font-bold">${(marketData.metrics.total_volume / 1e6).toFixed(2)}M</p>
            </div>
            <div className="bg-gray-800 rounded-lg p-6 hover:bg-gray-700 transition-colors">
              <h3 className="text-gray-400 mb-2">Open Interest</h3>
              <p className="text-3xl font-bold">${(marketData.metrics.total_oi / 1e6).toFixed(2)}M</p>
            </div>
            <div className="bg-gray-800 rounded-lg p-6 hover:bg-gray-700 transition-colors">
              <h3 className="text-gray-400 mb-2">Avg Funding Rate</h3>
              <p className="text-3xl font-bold">{marketData.metrics.avg_funding.toFixed(4)}%</p>
            </div>
          </div>

          {/* Market Data Section */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            <div className="bg-indigo-900/20 rounded-lg p-6 border border-indigo-500/20">
              <h3 className="text-indigo-400 font-semibold mb-4">Highest Funding Rate</h3>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span>Token</span>
                  <span className="font-mono">{marketData.market_data.highest_funding.token}</span>
                </div>
                <div className="flex justify-between">
                  <span>Rate</span>
                  <span className="font-mono">{(marketData.market_data.highest_funding.rate * 100).toFixed(4)}%</span>
                </div>
                <div className="flex justify-between">
                  <span>Volume</span>
                  <span className="font-mono">${(marketData.market_data.highest_funding.volume / 1e6).toFixed(2)}M</span>
                </div>
              </div>
            </div>
            
            {/* Add similar cards for most_active and largest_oi */}
          </div>

          {/* Existing charts and highlights sections */}
        </div>
      )}
    </main>
  )
} 