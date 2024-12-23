# DEX (Decentralized Exchange) Data

## Overview

Access comprehensive DEX data across multiple platforms including Uniswap, SushiSwap, PancakeSwap and other major DEXes through our unified API. Data is aggregated from:

- DefiLlama
- Dune Analytics
- Bitquery
- Footprint Analytics
- The Graph
- Messari

## Endpoints

### Get Pair Data

```typescript
GET /v1/dex/pairs/{chain}
```

Access trading pair information across different platforms:

#### DefiLlama Implementation
```typescript
// Get pair TVL and volume
const response = await fetch('https://api.llama.fi/protocol/uniswap/pairs');

// Response format
{
  data: {
    tvl: number,
    volume24h: number,
    feesUSD: number
  }
}
```

#### Dune Analytics Implementation
```typescript
// Using Dune SDK
const client = new DuneClient(DUNE_API_KEY);
const result = await client.refresh({
  queryId: 1234567,
  parameters: {
    pair_address: '0x...'
  }
});
```

#### Bitquery Implementation
```graphql
query {
  ethereum {
    dexTrades(
      options: {desc: "block.timestamp.time", limit: 10}
      date: {since: "2024-01-01"}
      exchangeName: {in: ["Uniswap", "Sushiswap"]}
    ) {
      transaction {
        hash
      }
      block {
        timestamp {
          time(format: "%Y-%m-%d %H:%M:%S")
        }
      }
      buyAmount
      buyAmountInUSD: buyAmount(in: USD)
      buyCurrency {
        symbol
        address
      }
      sellAmount
      sellAmountInUSD: sellAmount(in: USD)
      sellCurrency {
        symbol
        address
      }
    }
  }
}
```

### Get OHLCV Data

```typescript
GET /v1/dex/ohlc/{token}/{chain}
```

Get candlestick data for trading pairs:

#### DefiLlama Implementation
```typescript
const response = await fetch('https://coins.llama.fi/chart/ethereum:0x...');
```

#### Bitquery Implementation
```graphql
query {
  ethereum {
    dexTrades(
      options: {asc: "timeInterval.minute"}
      time: {since: "2024-01-01"}
      exchangeName: {is: "Uniswap"}
    ) {
      timeInterval {
        minute(count: 15)
      }
      baseCurrency {
        symbol
      }
      quoteCurrency {
        symbol
      }
      tradeAmount(in: USD)
      maximum_price: quotePrice(calculate: maximum)
      minimum_price: quotePrice(calculate: minimum)
      open_price: minimum(of: block, get: quote_price)
      close_price: maximum(of: block, get: quote_price)
    }
  }
}
```

### Get Liquidity Pools

```typescript
GET /v1/dex/pools/{protocol}
```

Access liquidity pool data:

#### The Graph Implementation
```graphql
query {
  pools(first: 100, orderBy: totalValueLockedUSD, orderDirection: desc) {
    id
    token0 {
      id
      symbol
    }
    token1 {
      id
      symbol  
    }
    totalValueLockedUSD
    volumeUSD
    feesUSD
  }
}
```

#### Footprint Implementation
```sql
SELECT 
  pool_address,
  token0_symbol,
  token1_symbol,
  tvl_usd,
  volume_24h_usd
FROM footprint_dex.pool_stats
WHERE protocol = 'uniswap_v3'
ORDER BY tvl_usd DESC
LIMIT 100
```

## Common Parameters

| Parameter | Type | Description | Default | Required |
|-----------|------|-------------|---------|----------|
| `chain` | string | Blockchain network | ethereum | Yes |
| `protocol` | string | DEX protocol name | - | No |
| `pair` | string | Trading pair address | - | No |
| `timeframe` | string | Candlestick timeframe | 1d | No |
| `from` | timestamp | Start time | -7d | No |
| `to` | timestamp | End time | now | No |

## Response Format

```typescript
{
  status: 200,
  data: {
    pairs: [{
      address: string,
      token0: {
        address: string,
        symbol: string,
        decimals: number
      },
      token1: {
        address: string,
        symbol: string,
        decimals: number
      },
      tvlUSD: number,
      volumeUSD24h: number,
      feesUSD24h: number,
      apr: number
    }],
    metadata: {
      timestamp: number,
      provider: string
    }
  }
}
```

## WebSocket Subscriptions

Subscribe to real-time DEX updates:

```typescript
// Bitquery WebSocket
const ws = new WebSocket('wss://streaming.bitquery.io/graphql');

ws.send(JSON.stringify({
  type: 'start',
  id: 'dex_trades',
  payload: {
    query: `subscription {
      EVM(network: eth) {
        DEXTrades {
          Block {
            Number
            Time
          }
          Trade {
            Buy {
              Amount
              Currency {
                Symbol
              }
            }
            Sell {
              Amount  
              Currency {
                Symbol
              }
            }
          }
        }
      }
    }`
  }
}));
```

## Rate Limits

Rate limits vary by provider:

| Provider | Free Tier | Pro Tier | Enterprise |
|----------|-----------|-----------|------------|
| DefiLlama | 300/5min | 1000/5min | Custom |
| Dune | 100/day | 1000/day | Custom |
| Bitquery | 100/day | 10000/day | Custom |
| The Graph | 1000/day | 100000/day | Custom |
| Footprint | 1000/day | Unlimited | Custom |

## Error Codes

| Code | Description | Solution |
|------|-------------|----------|
| 429 | Rate limit exceeded | Implement backoff |
| 400 | Invalid parameters | Check request format |
| 403 | Unauthorized | Verify API key |
| 500 | Provider error | Retry with exponential backoff |

## Best Practices

1. **Data Freshness**
   - Use WebSocket for real-time data
   - Cache historical data
   - Implement TTL based on timeframe

2. **Cost Optimization** 
   - Batch requests where possible
   - Use GraphQL to minimize data transfer
   - Cache frequently accessed data

3. **Reliability**
   - Implement fallback providers
   - Handle rate limits gracefully
   - Validate response data

4. **Performance**
   - Use compression
   - Implement pagination
   - Filter data server-side

## Example Implementation

```typescript
import { DefiLlama, Bitquery, DuneAnalytics } from '@blockchain/api';

class DEXDataAggregator {
  private providers: {
    defillama: DefiLlama;
    bitquery: Bitquery;
    dune: DuneAnalytics;
  };

  constructor(config: Config) {
    this.providers = {
      defillama: new DefiLlama(config.defillamaKey),
      bitquery: new Bitquery(config.bitqueryKey),
      dune: new DuneAnalytics(config.duneKey)
    };
  }

  async getPairData(chain: string, pair: string) {
    try {
      // Try primary source
      const data = await this.providers.defillama.getPair(chain, pair);
      return data;
    } catch (error) {
      // Fallback to secondary source
      const backup = await this.providers.bitquery.getPair(chain, pair);
      return backup;
    }
  }
}
```

## Need Help?

- Check our [API Reference](../../api-reference/README.md)
- Join our [Discord](https://discord.gg/blockchain-api)
- Submit issues on [GitHub](https://github.com/blockchain-api/issues)