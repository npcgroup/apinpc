'use client'

import React, { useEffect, useState, useMemo } from 'react'
import { createClient } from '@supabase/supabase-js'
import type { Database } from '@/types/supabase'
import { format } from 'date-fns'
import { MagnifyingGlassIcon } from '@heroicons/react/24/outline'

// Create Supabase client
const supabase = createClient<Database>(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_KEY!
)

interface Market {
  symbol: string
  mark_price: number
  funding_rate: number
  predicted_rate: number
  volume_24h: number
  open_interest: number
  next_funding_time: string
  timestamp: string
}

export default function PerpMetricsPage() {
  const [markets, setMarkets] = useState<Market[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [activeTab, setActiveTab] = useState<'open_interest' | 'volume' | 'current_funding' | 'predicted_funding' | 'opportunities'>('open_interest')

  // Fetch market data
  useEffect(() => {
    async function fetchMarketData() {
      try {
        setLoading(true)
        const { data, error } = await supabase
          .from('binance_market_data')
          .select('*')
          .order('timestamp', { ascending: false })

        if (error) throw error

        // Process and group the latest data by symbol
        const latestBySymbol = (data || []).reduce<Record<string, any>>((acc, curr) => {
          if (!acc[curr.symbol] || new Date(curr.timestamp) > new Date(acc[curr.symbol].timestamp)) {
            acc[curr.symbol] = curr
          }
          return acc
        }, {})

        const processedMarkets = Object.values(latestBySymbol).map(m => ({
          symbol: m.symbol.replace('USDT', ''),
          mark_price: parseFloat(m.mark_price),
          funding_rate: parseFloat(m.funding_rate),
          predicted_rate: parseFloat(m.predicted_rate || m.funding_rate),
          volume_24h: parseFloat(m.volume_24h),
          open_interest: parseFloat(m.open_interest),
          next_funding_time: m.next_funding_time,
          timestamp: m.timestamp
        }))

        // Sort based on active tab
        const sortedMarkets = processedMarkets.sort((a, b) => {
          switch (activeTab) {
            case 'open_interest':
              return b.open_interest - a.open_interest
            case 'volume':
              return b.volume_24h - a.volume_24h
            case 'current_funding':
              return Math.abs(b.funding_rate) - Math.abs(a.funding_rate)
            case 'predicted_funding':
              return Math.abs(b.predicted_rate) - Math.abs(a.predicted_rate)
            case 'opportunities':
              return Math.abs(b.predicted_rate - b.funding_rate) - Math.abs(a.predicted_rate - a.funding_rate)
            default:
              return 0
          }
        })

        setMarkets(sortedMarkets)
      } catch (err) {
        console.error('Error fetching market data:', err)
        setError(err instanceof Error ? err.message : 'Failed to fetch market data')
      } finally {
        setLoading(false)
      }
    }

    fetchMarketData()
    const interval = setInterval(fetchMarketData, 60000) // Update every minute
    return () => clearInterval(interval)
  }, [activeTab])

  const filteredMarkets = useMemo(() => {
    return markets.filter(market => 
      market.symbol.toLowerCase().includes(searchQuery.toLowerCase())
    )
  }, [markets, searchQuery])

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 text-white p-8">
        <div className="animate-pulse">Loading market data...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <h1 className="text-2xl font-bold mb-6">Perpetual Markets Overview</h1>
      
      {/* Search and Filters */}
      <div className="mb-6 flex gap-4 items-center">
        <div className="relative flex-1">
          <input
            type="text"
            placeholder="Search markets..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-gray-800 rounded-lg px-4 py-2 pl-10"
          />
          <MagnifyingGlassIcon className="absolute left-3 top-2.5 h-5 w-5 text-gray-400" />
        </div>
        
        {/* Filter Tabs */}
        <div className="flex gap-2">
          <button
            onClick={() => setActiveTab('open_interest')}
            className={`px-4 py-2 rounded ${activeTab === 'open_interest' ? 'bg-purple-600' : 'bg-gray-800'}`}
          >
            Open Interest
          </button>
          <button
            onClick={() => setActiveTab('volume')}
            className={`px-4 py-2 rounded ${activeTab === 'volume' ? 'bg-purple-600' : 'bg-gray-800'}`}
          >
            Volume
          </button>
          <button
            onClick={() => setActiveTab('current_funding')}
            className={`px-4 py-2 rounded ${activeTab === 'current_funding' ? 'bg-purple-600' : 'bg-gray-800'}`}
          >
            Current Funding
          </button>
          <button
            onClick={() => setActiveTab('predicted_funding')}
            className={`px-4 py-2 rounded ${activeTab === 'predicted_funding' ? 'bg-purple-600' : 'bg-gray-800'}`}
          >
            Predicted Funding
          </button>
        </div>
      </div>

      {/* Market Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredMarkets.map(market => (
          <div key={market.symbol} className="bg-gray-800 rounded-lg p-4">
            <div className="flex justify-between items-start mb-4">
              <h2 className="text-xl font-bold">{market.symbol}</h2>
              <span className="text-sm text-gray-400">
                {format(new Date(market.timestamp), 'MMM d, HH:mm')}
              </span>
            </div>
            
            <div className="grid grid-cols-2 gap-y-2">
              <span className="text-gray-400">Mark Price</span>
              <span className="text-right">${market.mark_price.toFixed(2)}</span>
              
              <span className="text-gray-400">Funding Rate</span>
              <span className={`text-right ${market.funding_rate > 0 ? 'text-green-400' : 'text-red-400'}`}>
                {(market.funding_rate * 100).toFixed(4)}%
              </span>
              
              <span className="text-gray-400">Predicted Rate</span>
              <span className={`text-right ${market.predicted_rate > 0 ? 'text-green-400' : 'text-red-400'}`}>
                {(market.predicted_rate * 100).toFixed(4)}%
              </span>
              
              <span className="text-gray-400">24h Volume</span>
              <span className="text-right">
                ${(market.volume_24h / 1e6).toFixed(2)}M
              </span>
              
              <span className="text-gray-400">Open Interest</span>
              <span className="text-right">
                ${(market.open_interest / 1e6).toFixed(2)}M
              </span>

              <span className="text-gray-400">Next Funding</span>
              <span className="text-right">
                {format(new Date(market.next_funding_time), 'HH:mm')}
              </span>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-4 text-gray-400 text-sm">
        Showing {filteredMarkets.length} of {markets.length} markets
      </div>
    </div>
  )
} 