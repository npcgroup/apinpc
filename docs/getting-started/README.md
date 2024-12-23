# Getting Started

This guide will help you begin integrating with our blockchain data APIs. We'll cover the essential concepts and walk through basic examples.

## Prerequisites

- Basic understanding of blockchain concepts
- Familiarity with REST APIs and GraphQL
- Node.js installed (for running example code)
- Git (for accessing example repositories)

## Quick Start

1. Choose your integration method:
```bash
# Using NPM package
npm install @defillama/sdk

# Or clone example repository
git clone https://github.com/DefiLlama/DefiLlama-Adapters
```

2. Get API credentials:
```javascript
// Store in .env file
DUNE_API_KEY=your_key_here
BITQUERY_API_KEY=your_key_here
FOOTPRINT_API_KEY=your_key_here
```

3. Make your first query:
```javascript
const sdk = require('@defillama/sdk');

async function getProtocolTVL() {
  const tvl = await sdk.getTvl('uniswap');
  console.log('Uniswap TVL:', tvl);
}
```

## Data Source Selection Guide

Choose the appropriate data source based on your needs:

### 1. On-Chain Data (DefiLlama Adapters)
Best for:
- Direct blockchain state queries
- TVL calculations
- Token balances and transfers
- Smart contract interactions

Example:
```javascript
const { getTokenBalance } = require('@defillama/sdk');

async function getBalance() {
  return await getTokenBalance(
    tokenAddress,
    holderAddress,
    'ethereum',
    blockNumber
  );
}
```

### 2. Indexed Data (Subgraphs)
Best for:
- Historical data analysis
- Complex relationship queries
- Event aggregations
- Time-series data

Example:
```graphql
query {
  pairs(first: 5, orderBy: reserveUSD, orderDirection: desc) {
    token0 {
      symbol
    }
    token1 {
      symbol
    }
    reserveUSD
  }
}
```

### 3. Real-time Data (Streaming)
Best for:
- Live price updates
- Trading activity monitoring
- MEV tracking
- Liquidity changes

Example:
```javascript
const ws = new WebSocket('wss://stream.bitquery.io/graphql');

ws.on('open', () => {
  ws.send(JSON.stringify({
    type: 'subscribe',
    query: `subscription {
      EVM(network: ethereum) {
        DEXTrades {
          Block {
            Number
          }
          Trade {
            Amount
            Price
          }
        }
      }
    }`
  }));
});
```

## Common Integration Patterns

### 1. TVL Tracking
```javascript
const { getTvl, getHistoricalTvl } = require('@defillama/sdk');

// Get current TVL
const currentTvl = await getTvl('protocol-name');

// Get historical TVL
const historicalTvl = await getHistoricalTvl('protocol-name', timestamp);
```

### 2. Price Feeds
```javascript
const { getPrices, getHistoricalPrices } = require('@defillama/sdk');

// Get current prices
const prices = await getPrices(['ethereum:0x...', 'bsc:0x...']);

// Get historical prices
const historicalPrices = await getHistoricalPrices(
  ['ethereum:0x...'],
  timestamp
);
```

### 3. Protocol Analytics
```javascript
const { getProtocolData } = require('@defillama/sdk');

const data = await getProtocolData('uniswap', {
  metrics: ['volume', 'fees', 'tvl'],
  timeframe: '24h'
});
```

## Best Practices for Getting Started

1. **Start Small**
   - Begin with simple queries
   - Test thoroughly in development
   - Use public endpoints first

2. **Error Handling**
```javascript
try {
  const result = await sdk.getTvl('protocol');
} catch (e) {
  if (e.response?.status === 429) {
    // Handle rate limit
    await sleep(1000);
  } else {
    // Handle other errors
    console.error('Error:', e);
  }
}
```

3. **Rate Limiting**
```javascript
const rateLimit = require('axios-rate-limit');
const http = rateLimit(axios.create(), { 
  maxRequests: 10,
  perMilliseconds: 1000
});
```

4. **Caching**
```javascript
const cache = new Map();
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

async function getCachedData(key) {
  const cached = cache.get(key);
  if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
    return cached.data;
  }
  const data = await fetchFreshData(key);
  cache.set(key, { data, timestamp: Date.now() });
  return data;
}
```

## Next Steps

- Explore [Advanced Features](../advanced/README.md)
- Learn about [Rate Limits](../rate-limits/README.md)
- Check out [Example Code](../examples/README.md)
- Join our [Discord Community](https://discord.gg/defillama)

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| Rate Limits | Implement caching and backoff |
| Missing Data | Check alternative endpoints |
| Timeout Errors | Reduce query complexity |
| WebSocket Drops | Implement reconnection logic |

## Additional Resources

- [API Reference](../api-reference/README.md)
- [SDK Documentation](../sdk/README.md)
- [Example Projects](../examples/projects/README.md)
- [Troubleshooting Guide](../troubleshooting/README.md) 