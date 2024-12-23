# API Reference

This comprehensive reference guide covers all available API endpoints, complete with real-world examples and implementation tips. We've organized it based on common use cases to help you find exactly what you need.

## Core Concepts

### Base URLs
```typescript
// Production endpoints
const MAINNET_URL = 'https://api.llama.fi'
const COINS_URL = 'https://coins.llama.fi'
const STABLECOINS_URL = 'https://stablecoins.llama.fi'
const YIELDS_URL = 'https://yields.llama.fi'

// WebSocket endpoints
const WS_URL = 'wss://stream.llama.fi'
```

### Authentication

Most endpoints are public, but for higher rate limits you'll need an API key:

```typescript
// REST requests
const headers = {
  'x-api-key': process.env.LLAMA_API_KEY,
  'Content-Type': 'application/json'
}

// WebSocket auth
ws.send(JSON.stringify({
  type: 'auth',
  apiKey: process.env.LLAMA_API_KEY
}))
```

## TVL Endpoints

### Get Protocol TVL
Returns current and historical TVL data for a specific protocol.

```typescript
// Get current TVL
GET /protocol/{protocol}

// Example request
const response = await fetch('https://api.llama.fi/protocol/aave')

// Example response
{
  "id": "1",
  "name": "Aave",
  "address": "0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9",
  "symbol": "AAVE", 
  "tvl": 3829481234.52,
  "chainTvls": {
    "ethereum": 2819374123.21,
    "polygon": 1010107111.31
  },
  "change_1h": 0.21,
  "change_1d": -1.52,
  "change_7d": 5.31
}

// Real-world usage example
async function monitorProtocolTVL(protocolName: string, threshold: number) {
  const tvlData = await fetch(`https://api.llama.fi/protocol/${protocolName}`)
  const { tvl, change_1d } = await tvlData.json()
  
  if (Math.abs(change_1d) > threshold) {
    notifyTeam(`${protocolName} TVL changed by ${change_1d}% in last 24h`)
  }
  
  return { tvl, change_1d }
}
```

### Historical TVL Data
Get TVL data points over time for trend analysis.

```typescript
// Get historical TVL
GET /protocol/{protocol}/history

// Example request with time range
const endTime = Math.floor(Date.now() / 1000)
const startTime = endTime - (30 * 24 * 60 * 60) // 30 days ago
const url = `https://api.llama.fi/protocol/uniswap/history?start=${startTime}&end=${endTime}`

// Example response
{
  "data": [
    {
      "date": "2024-01-01",
      "tvl": 3819374123.21,
      "tokensInUsd": {
        "ethereum:0x...": 1234567.89
      }
    },
    // ... more data points
  ]
}

// Real-world usage - TVL trend analysis
async function analyzeTVLTrend(protocol: string, days: number) {
  const history = await fetchTVLHistory(protocol, days)
  
  const trend = history.data.reduce((acc, day, i, arr) => {
    if (i === 0) return acc
    
    const dailyChange = ((day.tvl - arr[i-1].tvl) / arr[i-1].tvl) * 100
    acc.push({
      date: day.date,
      change: dailyChange
    })
    return acc
  }, [])

  return {
    averageChange: trend.reduce((sum, day) => sum + day.change, 0) / trend.length,
    volatility: calculateVolatility(trend.map(t => t.change)),
    trend
  }
}
```

### Chain Data
Get TVL and other metrics for specific blockchain networks.

```typescript
// Get chain TVL
GET /chain/{chain}

// Typescript interface
interface ChainTVL {
  tvl: number
  tokenSymbol: string
  tokenPrice: number
  bridgedAmount: number
  protocols: Protocol[]
}

// Example implementation - Chain comparison
async function compareChainMetrics(chains: string[]) {
  const results = await Promise.all(
    chains.map(async chain => {
      const data = await fetch(`https://api.llama.fi/chain/${chain}`)
      const metrics = await data.json()
      
      return {
        chain,
        tvl: metrics.tvl,
        dominance: calculateDominance(metrics),
        growth: calculateGrowthRate(metrics),
        protocolCount: metrics.protocols.length
      }
    })
  )

  return results.sort((a, b) => b.tvl - a.tvl)
}

// Usage example
const chainComparison = await compareChainMetrics([
  'ethereum',
  'bsc',
  'polygon',
  'arbitrum'
])
```

## Price Data

### Current Prices
Get current prices for multiple tokens in a single request.

```typescript
// Get current prices
GET /prices/current/{tokens}

// Example - Price monitoring system
class PriceMonitor {
  private priceCache = new Map<string, number>()
  private readonly PRICE_THRESHOLD = 0.05 // 5% change
  
  async checkPrices(tokens: string[]) {
    const prices = await fetch(`https://coins.llama.fi/prices/current/${tokens.join(',')}`)
    const { coins } = await prices.json()
    
    const alerts = []
    for (const [token, data] of Object.entries(coins)) {
      const prevPrice = this.priceCache.get(token)
      if (prevPrice) {
        const change = Math.abs((data.price - prevPrice) / prevPrice)
        if (change > this.PRICE_THRESHOLD) {
          alerts.push({
            token,
            change: change * 100,
            oldPrice: prevPrice,
            newPrice: data.price
          })
        }
      }
      this.priceCache.set(token, data.price)
    }
    
    return alerts
  }
}
```

### Historical Prices
Get historical price data for analysis and charting.

```typescript
// Get historical prices
GET /prices/historical/{timestamp}/{tokens}

// Example - Price correlation analysis
async function analyzePriceCorrelation(token1: string, token2: string, days: number) {
  const timestamps = generateDailyTimestamps(days)
  const prices = await Promise.all(
    timestamps.map(ts => 
      fetch(`https://coins.llama.fi/prices/historical/${ts}/${token1},${token2}`)
    )
  )
  
  const priceData = prices.map(p => p.json())
  return calculateCorrelation(priceData)
}

// Helper function for correlation calculation
function calculateCorrelation(prices) {
  // Pearson correlation implementation
  // Returns correlation coefficient between -1 and 1
}
```

## WebSocket Subscriptions

Real-time data streaming for live updates.

```typescript
// Example - Real-time TVL monitoring
class TVLMonitor {
  private ws: WebSocket
  private callbacks = new Map()
  
  constructor(protocols: string[]) {
    this.ws = new WebSocket('wss://stream.llama.fi')
    
    this.ws.on('open', () => {
      protocols.forEach(protocol => {
        this.subscribe(protocol)
      })
    })
    
    this.ws.on('message', (data) => {
      const update = JSON.parse(data)
      const callback = this.callbacks.get(update.protocol)
      if (callback) callback(update)
    })
  }
  
  subscribe(protocol: string) {
    this.ws.send(JSON.stringify({
      type: 'subscribe',
      protocol
    }))
  }
  
  onUpdate(protocol: string, callback: (update: any) => void) {
    this.callbacks.set(protocol, callback)
  }
}

// Usage
const monitor = new TVLMonitor(['aave', 'compound'])
monitor.onUpdate('aave', (update) => {
  console.log(`Aave TVL: $${update.tvl.toLocaleString()}`)
})
```

## Error Handling

Implement robust error handling for production use:

```typescript
class LlamaAPIClient {
  private readonly baseUrl: string
  private retryCount = 3
  
  async fetch<T>(endpoint: string): Promise<T> {
    let attempts = 0
    
    while (attempts < this.retryCount) {
      try {
        const response = await fetch(`${this.baseUrl}${endpoint}`)
        
        if (!response.ok) {
          if (response.status === 429) {
            const retryAfter = response.headers.get('Retry-After')
            await this.sleep(parseInt(retryAfter) * 1000)
            continue
          }
          
          throw new Error(`API Error: ${response.status}`)
        }
        
        return await response.json()
      } catch (error) {
        attempts++
        if (attempts === this.retryCount) throw error
        
        await this.sleep(Math.pow(2, attempts) * 1000)
      }
    }
  }
  
  private sleep(ms: number) {
    return new Promise(resolve => setTimeout(resolve, ms))
  }
}
```

## Rate Limiting

Implement rate limiting for production applications:

```typescript
class RateLimiter {
  private queue: Array<() => Promise<any>> = []
  private processing = false
  private readonly rateLimit: number
  private readonly interval: number
  
  constructor(requestsPerSecond: number) {
    this.rateLimit = requestsPerSecond
    this.interval = 1000 / requestsPerSecond
  }
  
  async add<T>(fn: () => Promise<T>): Promise<T> {
    return new Promise((resolve, reject) => {
      this.queue.push(async () => {
        try {
          const result = await fn()
          resolve(result)
        } catch (error) {
          reject(error)
        }
      })
      
      if (!this.processing) this.process()
    })
  }
  
  private async process() {
    this.processing = true
    
    while (this.queue.length > 0) {
      const fn = this.queue.shift()
      await fn()
      await new Promise(resolve => setTimeout(resolve, this.interval))
    }
    
    this.processing = false
  }
}
```

## Need Help?

- Join our [Discord](https://discord.gg/defillama) for real-time support
- Check out our [Example Projects](../examples/projects/README.md)
- Read our [Troubleshooting Guide](../troubleshooting/README.md)
- Submit issues on [GitHub](https://github.com/DefiLlama/DefiLlama-Adapters/issues) 