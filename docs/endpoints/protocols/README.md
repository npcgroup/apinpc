# Protocol Data

## Overview

Access comprehensive protocol-level data and analytics across DeFi, NFTs, and other blockchain protocols. Our unified API aggregates data from:

- DefiLlama Protocol API
- Dune Analytics
- Bitquery
- The Graph
- Footprint Analytics
- Messari Subgraphs

## Endpoints

### Get Protocol TVL

```typescript
GET /v1/protocols/{protocol_id}/tvl
```

Get Total Value Locked (TVL) metrics:

#### DefiLlama Implementation
```typescript
// Get current TVL
const current = await fetch('https://api.llama.fi/tvl/{protocol}');

// Get historical TVL
const history = await fetch('https://api.llama.fi/protocol/{protocol}');

// Response format
{
  tvl: number,
  tvlPrev24h: number,
  tvlChange24h: number,
  tvlHistory: [{
    date: number,
    tvl: number
  }]
}
```

#### The Graph Implementation
```graphql
query {
  protocol(id: "{protocol}") {
    totalValueLockedUSD
    totalValueLockedETH
    totalValueLockedBTC
    dailySnapshots(
      first: 30,
      orderBy: timestamp,
      orderDirection: desc
    ) {
      timestamp
      totalValueLockedUSD
    }
  }
}
```

### Get Protocol Statistics

```typescript
GET /v1/protocols/{protocol_id}/stats
```

Access comprehensive protocol metrics:

#### Dune Analytics Implementation
```typescript
const client = new DuneClient(DUNE_API_KEY);

// Get protocol stats
const stats = await client.query({
  queryId: "3568055", // Protocol stats query
  parameters: {
    protocol: "uniswap"
  }
});

// Response includes:
// - Daily/weekly/monthly active users
// - Transaction counts
// - Fee revenue
// - Volume metrics
```

#### Bitquery Implementation
```graphql
query {
  ethereum {
    dexTrades(
      exchangeName: {is: "Uniswap"}
      time: {since: "2024-01-01"}
    ) {
      count
      tradeAmount(in: USD)
      trades: count
      traders: countDistinct(field: transaction_from)
      protocols: countDistinct(field: smart_contract_address)
    }
  }
}
```

### Get Protocol Revenue

```typescript
GET /v1/protocols/{protocol_id}/revenue
```

Track protocol revenue and fee data:

#### DefiLlama Implementation
```typescript
// Get fees and revenue
const response = await fetch('https://api.llama.fi/overview/fees/{protocol}');

// Response format
{
  total24h: number,
  total7d: number,
  total30d: number,
  breakdown: {
    supply: number,
    trading: number,
    borrow: number,
    other: number
  }
}
```

### Get Protocol Users

```typescript
GET /v1/protocols/{protocol_id}/users
```

Access user analytics and growth metrics:

#### Dune Analytics Implementation
```typescript
// Get user metrics
const users = await client.query({
  queryId: "3567562",
  parameters: {
    protocol: "aave",
    timeframe: "30d"
  }
});

// Response includes:
// - Daily/monthly active users
// - New vs returning users
// - User retention metrics
// - User behavior analysis
```

## Common Parameters

| Parameter | Type | Description | Default | Required |
|-----------|------|-------------|---------|----------|
| `timeframe` | string | Time period for data | 24h | No |
| `chain` | string | Blockchain network | all | No |
| `metric` | string | Specific metric to query | all | No |
| `currency` | string | Currency for amounts | USD | No |

## Response Format

```typescript
{
  status: 200,
  data: {
    protocol: {
      id: string,
      name: string,
      category: string,
      chains: string[],
      metrics: {
        tvl: {
          current: number,
          change24h: number,
          history: Array<{timestamp: number, value: number}>
        },
        users: {
          total: number,
          active24h: number,
          active7d: number
        },
        revenue: {
          total24h: number,
          breakdown: {
            [category: string]: number
          }
        }
      }
    },
    metadata: {
      timestamp: number,
      provider: string
    }
  }
}
```

## WebSocket Subscriptions

Subscribe to real-time protocol updates:

```typescript
// Bitquery WebSocket
const ws = new WebSocket('wss://streaming.bitquery.io/graphql');

ws.send(JSON.stringify({
  type: 'start',
  id: 'protocol_metrics',
  payload: {
    query: `subscription {
      ProtocolMetrics(
        protocol: "uniswap"
      ) {
        TVL
        Volume24h
        Fees24h
        ActiveUsers24h
        TransactionCount24h
      }
    }`
  }
}));
```

## Rate Limits & Caching

| Provider | Cache Duration | Rate Limit |
|----------|---------------|------------|
| DefiLlama | 5 minutes | 300/5min |
| Dune | 30 minutes | 100/day |
| The Graph | 15 seconds | 1000/day |
| Bitquery | 1 minute | 100/day |
| Messari | 5 minutes | 500/day |

## Error Handling

```typescript
class ProtocolDataProvider {
  async getProtocolTVL(protocol: string): Promise<number> {
    try {
      // Try primary source
      const tvl = await this.defiLlama.getTVL(protocol);
      return tvl;
    } catch (error) {
      // Fall back to secondary source
      try {
        const backup = await this.theGraph.getTVL(protocol);
        return backup;
      } catch (backupError) {
        // Fall back to tertiary source
        return this.dune.getTVL(protocol);
      }
    }
  }
}
```

## Best Practices

1. **Data Consistency**
   - Cross-reference metrics across sources
   - Handle chain-specific nuances
   - Validate historical data

2. **Performance**
   - Cache protocol metadata
   - Batch related requests
   - Use GraphQL for precise data

3. **Reliability**
   - Implement multiple data sources
   - Handle protocol upgrades
   - Monitor for anomalies

4. **Security**
   - Verify protocol contracts
   - Monitor for exploits
   - Track governance changes

## Example Implementation

```typescript
import { DefiLlama, Dune, TheGraph } from '@blockchain/api';

class ProtocolDataAggregator {
  private providers: {
    defillama: DefiLlama;
    dune: Dune;
    thegraph: TheGraph;
  };

  constructor(config: Config) {
    this.providers = {
      defillama: new DefiLlama(config.defillamaKey),
      dune: new Dune(config.duneKey),
      thegraph: new TheGraph(config.graphKey)
    };
  }

  async getProtocolData(protocol: string) {
    const [tvl, stats, revenue] = await Promise.all([
      this.getProtocolTVL(protocol),
      this.getProtocolStats(protocol),
      this.getProtocolRevenue(protocol)
    ]);

    return {
      tvl,
      stats,
      revenue
    };
  }
}
```

## Need Help?

- Check our [API Reference](../../api-reference/README.md)
- Join our [Discord](https://discord.gg/blockchain-api)
- Submit issues on [GitHub](https://github.com/blockchain-api/issues) 