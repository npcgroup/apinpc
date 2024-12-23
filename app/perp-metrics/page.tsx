'use client'

import { useEffect, useState } from 'react'
import { createClient } from '@supabase/supabase-js'
import type { Database } from '@/types/supabase'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Area, AreaChart, CartesianGrid } from 'recharts'
import { format, parseISO } from 'date-fns'

// Define types for our metrics
interface PerpMetric {
  id: number
  symbol: string
  timestamp: string
  funding_rate: number
  perp_volume_24h: number
  open_interest: number
  mark_price: number
  spot_price: number
  spot_volume_24h: number
  liquidity: number
  market_cap: number
  total_supply: number
  price_change_24h: number
  txns_24h: number
  holder_count: number
}

// Add this type for our chart metrics
type MetricType = 'spot_price' | 'spot_volume_24h' | 'liquidity' | 'mark_price' | 'funding_rate' | 'open_interest' | 'market_cap' | 'txns_24h';

interface MetricOption {
  value: MetricType;
  label: string;
  format: (value: number) => string;
  color: string;
}

const metricOptions: MetricOption[] = [
  { 
    value: 'spot_price', 
    label: 'Price', 
    format: (v) => `$${v.toFixed(4)}`,
    color: '#8B5CF6' // Purple
  },
  { 
    value: 'spot_volume_24h', 
    label: 'Volume 24h', 
    format: (v) => `$${(v/1e6).toFixed(2)}M`,
    color: '#10B981' // Green
  },
  { 
    value: 'liquidity', 
    label: 'Liquidity', 
    format: (v) => `$${(v/1e6).toFixed(2)}M`,
    color: '#3B82F6' // Blue
  },
  { 
    value: 'mark_price', 
    label: 'Mark Price', 
    format: (v) => `$${v.toFixed(4)}`,
    color: '#EC4899' // Pink
  },
  { 
    value: 'funding_rate', 
    label: 'Funding Rate', 
    format: (v) => `${(v * 100).toFixed(4)}%`,
    color: '#F59E0B' // Yellow
  },
  { 
    value: 'open_interest', 
    label: 'Open Interest', 
    format: (v) => `$${(v/1e6).toFixed(2)}M`,
    color: '#6366F1' // Indigo
  },
  { 
    value: 'market_cap', 
    label: 'Market Cap', 
    format: (v) => `$${(v/1e6).toFixed(2)}M`,
    color: '#14B8A6' // Teal
  },
  { 
    value: 'txns_24h', 
    label: 'Transactions', 
    format: (v) => v.toLocaleString(),
    color: '#F472B6' // Pink
  }
];

const supabase = createClient<Database>(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_KEY!
)

// Add TimeRange type at the top with other type definitions
type TimeRange = '1H' | '4H' | '12H' | '24H';

export default function PerpMetricsPage() {
  const [metrics, setMetrics] = useState<PerpMetric[]>([])
  const [historicalData, setHistoricalData] = useState<PerpMetric[]>([])
  const [loading, setLoading] = useState(true)
  const [nextUpdate, setNextUpdate] = useState<Date>()
  const [timeToUpdate, setTimeToUpdate] = useState('')
  const [selectedToken, setSelectedToken] = useState<string>('')
  const [selectedMetric, setSelectedMetric] = useState<MetricType>('spot_price')
  const [timeRange, setTimeRange] = useState<TimeRange>('24H')

  useEffect(() => {
    fetchMetrics()
    const interval = setInterval(fetchMetrics, 60000) // Refresh every minute
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    // Calculate next update time (next 15-minute mark)
    const now = new Date()
    const next = new Date(now)
    const minutes = next.getMinutes()
    const nextQuarter = Math.ceil(minutes / 15) * 15
    next.setMinutes(nextQuarter)
    next.setSeconds(0)
    setNextUpdate(next)

    // Update countdown timer every second
    const timer = setInterval(() => {
      const now = new Date()
      const diff = next.getTime() - now.getTime()
      const minutes = Math.floor(diff / 60000)
      const seconds = Math.floor((diff % 60000) / 1000)
      setTimeToUpdate(`${minutes}m ${seconds}s`)
    }, 1000)

    return () => clearInterval(timer)
  }, [metrics])

  async function fetchMetrics() {
    try {
      const { data: latest, error: latestError } = await supabase
        .from('perpetual_metrics')
        .select('*')
        .order('timestamp', { ascending: false })

      if (latestError) throw latestError

      if (latest) {
        // Group by symbol and get latest for each
        const latestBySymbol = latest.reduce<Record<string, PerpMetric>>((acc, curr) => {
          if (!acc[curr.symbol] || new Date(curr.timestamp) > new Date(acc[curr.symbol].timestamp)) {
            acc[curr.symbol] = curr as PerpMetric;
          }
          return acc;
        }, {});

        // Convert to array and sort by market cap, handle inactive tokens
        const activeTokens = Object.values(latestBySymbol)
          .sort((a: PerpMetric, b: PerpMetric) => {
            // Put tokens with no market cap at the end
            if (!a.market_cap && !b.market_cap) return 0;
            if (!a.market_cap) return 1;
            if (!b.market_cap) return -1;
            return b.market_cap - a.market_cap;
          });

        setMetrics(activeTokens);
        
        // Set initial selected token if none selected
        if (!selectedToken && activeTokens.length > 0) {
          // Select first token with price data
          const firstActiveToken = activeTokens.find(t => t.spot_price > 0);
          if (firstActiveToken) {
            setSelectedToken(firstActiveToken.symbol);
          }
        }
      }

      // Fetch historical data if we have a selected token
      if (selectedToken) {
        const twentyFourHoursAgo = new Date();
        twentyFourHoursAgo.setHours(twentyFourHoursAgo.getHours() - 24);

        const { data: historical, error: historicalError } = await supabase
          .from('perpetual_metrics')
          .select('*')
          .eq('symbol', selectedToken)
          .gte('timestamp', twentyFourHoursAgo.toISOString())
          .order('timestamp', { ascending: true });

        if (historicalError) throw historicalError;

        if (historical) {
          // Filter out duplicate timestamps and ensure data is properly sorted
          const uniqueHistorical = historical.reduce<Record<number, PerpMetric>>((acc, curr) => {
            const timestamp = new Date(curr.timestamp).getTime();
            if (!acc[timestamp] || curr.id > acc[timestamp].id) {
              acc[timestamp] = curr as PerpMetric;
            }
            return acc;
          }, {});

          const sortedHistorical = Object.values(uniqueHistorical)
            .sort((a: PerpMetric, b: PerpMetric) => 
              new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
            );

          setHistoricalData(sortedHistorical);
        }
      }
    } catch (error) {
      console.error('Error fetching metrics:', error);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (selectedToken) {
      fetchMetrics()
    }
  }, [selectedToken])

  // Get the current metric option
  const currentMetric = metricOptions.find(m => m.value === selectedMetric)!;

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 text-white p-8">
        <div className="animate-pulse text-center">Loading metrics...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">Perpetual Metrics Dashboard</h1>
        <div className="text-right">
          <div className="text-sm text-gray-400">Next update in</div>
          <div className="text-xl font-mono text-purple-400">{timeToUpdate}</div>
        </div>
      </div>

      {/* Historical Chart */}
      <div className="mb-8 bg-gray-800/50 backdrop-blur-sm p-6 rounded-lg shadow-lg">
        <div className="flex justify-between items-center mb-6">
          <div className="flex items-center gap-4">
            <h2 className="text-xl font-bold text-purple-400">
              {selectedToken} - {currentMetric.label} History
            </h2>
            <select 
              value={selectedMetric}
              onChange={(e) => setSelectedMetric(e.target.value as MetricType)}
              className="bg-gray-700/50 text-white rounded-lg px-4 py-2 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-purple-500"
            >
              {metricOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
          <select 
            value={selectedToken}
            onChange={(e) => setSelectedToken(e.target.value)}
            className="bg-gray-700/50 text-white rounded-lg px-4 py-2 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-purple-500"
          >
            {metrics.map((m) => (
              <option key={m.symbol} value={m.symbol}>{m.symbol}</option>
            ))}
          </select>
        </div>
        
        <div className="h-[400px]">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={historicalData}>
              <defs>
                <linearGradient id="colorGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={currentMetric.color} stopOpacity={0.3}/>
                  <stop offset="95%" stopColor={currentMetric.color} stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid 
                strokeDasharray="3 3" 
                vertical={false}
                stroke="#374151"
              />
              <XAxis 
                dataKey="timestamp" 
                tickFormatter={(time: string) => format(parseISO(time), 'HH:mm')}
                stroke="#9CA3AF"
                tick={{ fill: '#9CA3AF' }}
                axisLine={{ stroke: '#4B5563' }}
                tickLine={{ stroke: '#4B5563' }}
              />
              <YAxis 
                domain={['auto', 'auto']}
                stroke="#9CA3AF"
                tick={{ fill: '#9CA3AF' }}
                axisLine={{ stroke: '#4B5563' }}
                tickLine={{ stroke: '#4B5563' }}
                tickFormatter={(value) => {
                  if (selectedMetric === 'funding_rate') {
                    return `${(value * 100).toFixed(2)}%`
                  }
                  if (['spot_volume_24h', 'liquidity', 'open_interest', 'market_cap'].includes(selectedMetric)) {
                    return `$${(value/1e6).toFixed(1)}M`
                  }
                  if (selectedMetric === 'txns_24h') {
                    return value.toLocaleString()
                  }
                  return `$${value.toFixed(4)}`
                }}
              />
              <Tooltip
                content={({ active, payload, label }) => {
                  if (active && payload && payload.length && payload[0].value != null) {
                    return (
                      <div className="bg-gray-800 border border-gray-700 p-4 rounded-lg shadow-lg">
                        <p className="text-gray-400 mb-2">
                          {format(parseISO(label), 'MMM dd, HH:mm')}
                        </p>
                        <p className="text-white font-medium">
                          {currentMetric.label}: {currentMetric.format(Number(payload[0].value))}
                        </p>
                      </div>
                    )
                  }
                  return null
                }}
              />
              <Area 
                type="monotone" 
                dataKey={selectedMetric}
                stroke={currentMetric.color}
                strokeWidth={2}
                fill="url(#colorGradient)"
                dot={false}
                activeDot={{
                  r: 6,
                  stroke: currentMetric.color,
                  strokeWidth: 2,
                  fill: '#1F2937'
                }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
        
        {/* Add time range selector */}
        <div className="flex justify-center gap-4 mt-4">
          {(['1H', '4H', '12H', '24H'] as const).map((range) => (
            <button
              key={range}
              className={`px-4 py-2 rounded-lg transition-all ${
                timeRange === range 
                  ? 'bg-purple-600 text-white' 
                  : 'bg-gray-700/50 text-gray-400 hover:bg-gray-700'
              }`}
              onClick={() => setTimeRange(range)}
            >
              {range}
            </button>
          ))}
        </div>
      </div>

      {/* Current Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {metrics.map((metric) => (
          <div 
            key={metric.symbol} 
            className={`bg-gray-800 rounded-lg p-6 shadow-lg hover:shadow-xl transition-all ${
              (metric.spot_price === 0 && metric.symbol !== 'BRETT') ? 'opacity-70' : ''
            } ${selectedToken === metric.symbol ? 'ring-2 ring-purple-500' : ''}`}
            onClick={() => (metric.spot_price > 0 || metric.symbol === 'BRETT') && setSelectedToken(metric.symbol)}
            role="button"
            tabIndex={0}
          >
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-2xl font-bold text-purple-400">{metric.symbol}</h2>
              {metric.price_change_24h !== 0 || metric.symbol === 'BRETT' ? (
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                  metric.price_change_24h > 0 ? 'bg-green-500/20 text-green-400' :
                  metric.price_change_24h < 0 ? 'bg-red-500/20 text-red-400' :
                  'bg-gray-500/20 text-gray-400'
                }`}>
                  {metric.price_change_24h > 0 ? '↑' : '↓'} 
                  {Math.abs(metric.price_change_24h).toFixed(2)}%
                </span>
              ) : (
                <span className="px-3 py-1 rounded-full text-sm font-medium bg-gray-500/20 text-gray-400">
                  Inactive
                </span>
              )}
            </div>

            <div className="space-y-6">
              {/* Spot Market */}
              <div>
                <h3 className="text-sm font-semibold text-purple-400 mb-2">Spot Market</h3>
                <div className="grid grid-cols-2 gap-2">
                  <span className="text-gray-400">Price</span>
                  <span className="text-right font-mono">
                    {metric.spot_price > 0 ? `$${metric.spot_price.toFixed(4)}` : '-'}
                  </span>
                  <span className="text-gray-400">Volume 24h</span>
                  <span className="text-right font-mono">
                    {metric.spot_volume_24h > 0 ? `$${(metric.spot_volume_24h/1e6).toFixed(2)}M` : '-'}
                  </span>
                  <span className="text-gray-400">Liquidity</span>
                  <span className="text-right font-mono">
                    {metric.liquidity > 0 ? `$${(metric.liquidity/1e6).toFixed(2)}M` : '-'}
                  </span>
                </div>
              </div>

              {/* Perpetual Market */}
              <div>
                <h3 className="text-sm font-semibold text-purple-400 mb-2">Perpetual Market</h3>
                <div className="grid grid-cols-2 gap-2">
                  <span className="text-gray-400">Mark Price</span>
                  <span className="text-right font-mono">${metric.mark_price.toFixed(4)}</span>
                  <span className="text-gray-400">Funding Rate</span>
                  <span className="text-right font-mono">{(metric.funding_rate * 100).toFixed(4)}%</span>
                  <span className="text-gray-400">Open Interest</span>
                  <span className="text-right font-mono">${(metric.open_interest/1e6).toFixed(2)}M</span>
                </div>
              </div>

              {/* Market Stats */}
              <div>
                <h3 className="text-sm font-semibold text-purple-400 mb-2">Market Stats</h3>
                <div className="grid grid-cols-2 gap-2">
                  <span className="text-gray-400">Market Cap</span>
                  <span className="text-right font-mono">${(metric.market_cap/1e6).toFixed(2)}M</span>
                  <span className="text-gray-400">24h Transactions</span>
                  <span className="text-right font-mono">{metric.txns_24h.toLocaleString()}</span>
                  <span className="text-gray-400">Holders</span>
                  <span className="text-right font-mono">
                    {metric.holder_count > 0 ? metric.holder_count.toLocaleString() : '-'}
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