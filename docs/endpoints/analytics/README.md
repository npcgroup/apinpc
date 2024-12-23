# Analytics Data

## Overview

Access comprehensive blockchain analytics and market intelligence. Our unified API aggregates analytics from:

- DefiLlama Analytics
- Dune Analytics
- Bitquery
- Footprint Analytics
- Messari
- Token Terminal

## Endpoints

### Get Market Sentiment

```typescript
GET /v1/analytics/sentiment
```

Access market sentiment indicators:

#### Dune Analytics Implementation
```typescript
const client = new DuneClient(DUNE_API_KEY);

// Get market sentiment metrics
const sentiment = await client.query({
  queryId: "3682939",
  parameters: {
    timeframe: "7d"
  }
});

// Response includes:
// - Fear & Greed Index
// - Social sentiment
// - Trading indicators
// - Whale activity
```

#### Bitquery Implementation
```graphql
query {
  ethereum {
    dexTrades(
      options: {desc: "count", limit: 100}
      date: {since: "2024-01-01"}
    ) {
      sentiment: count(uniq: buyers)
      volumeUSD: tradeAmount(in: USD)
      count
      whaleCount: count(
        if: {trade: {amount: {gt: "100000"}}}
      )
    }
  }
}
```

### Get Market Correlation

```typescript
GET /v1/analytics/correlation
```

Analyze asset correlations:

#### Token Terminal Implementation
```typescript
// Get correlation data
const response = await fetch('https://api.tokenterminal.com/v2/metrics/correlation', {
  headers: { 'Authorization': `Bearer ${TOKEN_TERMINAL_KEY}` }
});

// Response format
{
  correlations: [{
    asset1: string,
    asset2: string,
    correlation: number,
    timeframe: string,
    confidence: number
  }]
}
```

### Get Risk Metrics

```typescript
GET /v1/analytics/risk/{token}
```

Access comprehensive risk analytics:

#### DefiLlama Implementation
```typescript
// Get risk metrics
const response = await fetch(`https://api.llama.fi/protocol/${protocol}/risk`);

// Response includes:
// - Volatility metrics
// - Liquidity depth
// - Concentration risk
// - Smart contract risk
```

### Get Market Trends

```typescript
GET /v1/analytics/trends
```

Track emerging market trends:

#### Footprint Analytics Implementation
```typescript
// Get trend analysis
const trends = await client.query({
  endpoint: 'trends',
  parameters: {
    timeframe: '30d',
    categories: ['defi', 'nft', 'gaming']
  }
});

// Response includes:
// - Trending protocols
// - Growing sectors
// - Volume patterns
// - User adoption
```

### Get Whale Activity

```typescript
GET /v1/analytics/whales
```

Monitor large holder behavior:

#### Bitquery Implementation
```graphql
query {
  ethereum {
    transfers(
      amount: {gt: "1000000"}
      options: {desc: "block.timestamp.time", limit: 100}
    ) {
      block {
        timestamp {
          time(format: "%Y-%m-%d %H:%M:%S")
        }
      }
      sender {
        address
        annotation
      }
      receiver {
        address
        annotation
      }
      amount
      currency {
        symbol
      }
    }
  }
}
```

## Common Parameters

| Parameter | Type | Description | Default | Required |
|-----------|------|-------------|---------|----------|
| `timeframe` | string | Analysis period | 24h | No |
| `confidence` | number | Minimum confidence score | 0.8 | No |
| `limit` | number | Number of results | 100 | No |
| `category` | string | Market category | all | No |

## Response Format

```typescript
{
  status: 200,
  data: {
    analytics: {
      sentiment: {
        score: number,
        indicators: {
          fearGreedIndex: number,
          socialSentiment: number,
          tradingActivity: number
        }
      },
      trends: [{
        category: string,
        growth: number,
        volume: number,
        users: number
      }],
      risks: {
        marketRisk: number,
        technicalRisk: number,
        regulatoryRisk: number
      },
      whales: {
        activeCount: number,
        netFlow: number,
        largestTransfers: [{
          amount: number,
          token: string,
          timestamp: number
        }]
      }
    },
    metadata: {
      timestamp: number,
      provider: string,
      confidence: number
    }
  }
}
```

## WebSocket Subscriptions

Subscribe to real-time analytics:

```typescript
// Bitquery WebSocket
const ws = new WebSocket('wss://streaming.bitquery.io/graphql');

ws.send(JSON.stringify({
  type: 'start',
  id: 'market_analytics',
  payload: {
    query: `subscription {
      MarketAnalytics {
        Sentiment {
          Score
          Change
        }
        WhaleActivity {
          Transfers {
            Amount
            Token
          }
        }
        TrendingProtocols {
          Name
          Volume
          Users
        }
      }
    }`
  }
}));
```

## Rate Limits & Caching

| Provider | Cache Duration | Rate Limit |
|----------|---------------|------------|
| DefiLlama | 5 minutes | 300/5min |
| Token Terminal | 1 minute | 200/min |
| Bitquery | 1 minute | 100/day |
| Dune | 30 minutes | 100/day |
| Footprint | 5 minutes | 1000/day |

## Error Handling

```typescript
class AnalyticsProvider {
  async getMarketSentiment(): Promise<number> {
    try {
      // Try primary source
      const sentiment = await this.dune.getSentiment();
      return sentiment;
    } catch (error) {
      // Fall back to secondary source
      try {
        const backup = await this.bitquery.getSentiment();
        return backup;
      } catch (backupError) {
        // Fall back to tertiary source
        return this.footprint.getSentiment();
      }
    }
  }
}
```

## Best Practices

1. **Data Quality**
   - Validate data sources
   - Cross-reference metrics
   - Handle outliers

2. **Performance**
   - Cache analytics results
   - Batch related queries
   - Use incremental updates

3. **Accuracy**
   - Implement confidence scores
   - Version analytics models
   - Track prediction accuracy

4. **Scalability**
   - Distribute computation
   - Optimize storage
   - Handle large datasets

## Example Implementation

```typescript
import { DefiLlama, TokenTerminal, Bitquery } from '@blockchain/api';

class MarketAnalytics {
  private providers: {
    defillama: DefiLlama;
    tokenterminal: TokenTerminal;
    bitquery: Bitquery;
  };

  constructor(config: Config) {
    this.providers = {
      defillama: new DefiLlama(config.defillamaKey),
      tokenterminal: new TokenTerminal(config.terminalKey),
      bitquery: new Bitquery(config.bitqueryKey)
    };
  }

  async getMarketAnalytics() {
    const [sentiment, trends, risks] = await Promise.all([
      this.getMarketSentiment(),
      this.getMarketTrends(),
      this.getRiskMetrics()
    ]);

    return {
      sentiment,
      trends,
      risks
    };
  }

  async monitorWhales(callback: (activity: any) => void) {
    // Set up WebSocket monitoring
    const ws = new WebSocket('wss://streaming.bitquery.io/graphql');
    
    // Subscribe to whale activity
    ws.send(JSON.stringify({
      type: 'start',
      id: 'whale_activity',
      payload: {
        query: `subscription { ... }`
      }
    }));

    ws.onmessage = (event) => {
      callback(JSON.parse(event.data));
    };
  }
}
```

## Need Help?

- Check our [API Reference](../../api-reference/README.md)
- Join our [Discord](https://discord.gg/blockchain-api)
- Submit issues on [GitHub](https://github.com/blockchain-api/issues) 