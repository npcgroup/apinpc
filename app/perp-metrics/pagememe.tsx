'use client'

import React, { useEffect, useState } from 'react'
import { createClient } from '@supabase/supabase-js'
import type { Database } from '@/types/supabase'
import { XAxis, YAxis, Tooltip, ResponsiveContainer, Area, AreaChart, CartesianGrid } from 'recharts'
import { format, parseISO } from 'date-fns'

// Update interfaces for our new data structure
interface FundingSnapshot {
  timestamp: string;
  token: string;
  current_funding_rate: number;
  predicted_funding_rate: number;
  mark_price: number;
  open_interest: number;
  notional_open_interest: number;
  volume_24h: number;
  avg_24h_funding_rate: number;
  exchange: string;
  metadata: {
    funding_difference: number;
  };
}

interface MarketMetrics {
  token: string;
  latest_snapshot: FundingSnapshot;
  historical_data: FundingSnapshot[];
}

// Create Supabase client
const supabase = createClient<Database>(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_KEY!
)

export default function PerpMetricsPage() {
  const [markets, setMarkets] = useState<MarketMetrics[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchMarketData() {
      try {
        setLoading(true)
        
        // Get the latest snapshot for each token
        const { data: latestSnapshots, error: snapshotError } = await supabase
          .from('funding_rate_snapshots')
          .select('*')
          .order('timestamp', { ascending: false })
          .limit(1000) // Adjust based on your needs

        if (snapshotError) throw snapshotError

        // Group by token and get latest data
        const tokenGroups = latestSnapshots.reduce((acc: { [key: string]: FundingSnapshot[] }, snapshot) => {
          if (!acc[snapshot.token]) {
            acc[snapshot.token] = []
          }
          acc[snapshot.token].push(snapshot)
          return acc
        }, {})

        // Get historical data for each token (last 24 hours)
        const marketMetrics: MarketMetrics[] = await Promise.all(
          Object.entries(tokenGroups).map(async ([token, snapshots]) => {
            const { data: historicalData, error: historyError } = await supabase
              .from('funding_rate_snapshots')
              .select('*')
              .eq('token', token)
              .gte('timestamp', new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString())
              .order('timestamp', { ascending: true })

            if (historyError) throw historyError

            return {
              token,
              latest_snapshot: snapshots[0],
              historical_data: historicalData
            }
          })
        )

        // Sort markets by notional open interest
        const sortedMarkets = marketMetrics.sort((a, b) => 
          (b.latest_snapshot.notional_open_interest || 0) - (a.latest_snapshot.notional_open_interest || 0)
        )

        setMarkets(sortedMarkets)
        setLoading(false)
      } catch (err) {
        console.error('Error fetching market data:', err)
        setError(err instanceof Error ? err.message : 'Failed to fetch market data')
        setLoading(false)
      }
    }

    fetchMarketData()
  }, [])

  if (loading) return <div className="p-4">Loading market data...</div>
  if (error) return <div className="p-4 text-red-500">Error: {error}</div>

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Perpetual Markets Overview</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {markets.map((market) => (
          <div key={market.token} className="bg-gray-800 rounded-lg p-4">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">{market.token}</h2>
              <span className="text-sm text-gray-400">
                {format(parseISO(market.latest_snapshot.timestamp), 'MMM d, HH:mm')}
              </span>
            </div>

            {/* Price Chart */}
            <div className="h-32 mb-4">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={market.historical_data}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="timestamp"
                    tickFormatter={(timestamp) => format(parseISO(timestamp), 'HH:mm')}
                  />
                  <YAxis />
                  <Tooltip 
                    labelFormatter={(timestamp) => format(parseISO(timestamp as string), 'MMM d, HH:mm')}
                    formatter={(value: number) => [`$${value.toFixed(4)}`, 'Price']}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="mark_price" 
                    stroke="#8884d8" 
                    fill="#8884d8" 
                    fillOpacity={0.3}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            {/* Market Metrics */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <h3 className="text-sm font-semibold text-purple-400 mb-2">Market Overview</h3>
                <div className="grid grid-cols-2 gap-2">
                  <span className="text-gray-400">Mark Price</span>
                  <span className="text-right font-mono">
                    ${market.latest_snapshot.mark_price.toFixed(4)}
                  </span>
                  <span className="text-gray-400">Funding Rate</span>
                  <span className="text-right font-mono">
                    {(market.latest_snapshot.current_funding_rate * 100).toFixed(4)}%
                  </span>
                  <span className="text-gray-400">Predicted Rate</span>
                  <span className="text-right font-mono">
                    {(market.latest_snapshot.predicted_funding_rate * 100).toFixed(4)}%
                  </span>
                </div>
              </div>

              <div>
                <h3 className="text-sm font-semibold text-purple-400 mb-2">Volume & OI</h3>
                <div className="grid grid-cols-2 gap-2">
                  <span className="text-gray-400">24h Volume</span>
                  <span className="text-right font-mono">
                    ${(market.latest_snapshot.volume_24h/1e6).toFixed(2)}M
                  </span>
                  <span className="text-gray-400">Open Interest</span>
                  <span className="text-right font-mono">
                    ${(market.latest_snapshot.notional_open_interest/1e6).toFixed(2)}M
                  </span>
                  <span className="text-gray-400">Avg 24h Rate</span>
                  <span className="text-right font-mono">
                    {(market.latest_snapshot.avg_24h_funding_rate * 100).toFixed(4)}%
                  </span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
} 