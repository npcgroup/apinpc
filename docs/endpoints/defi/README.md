# Additional DeFi Categories

## Overview

Access comprehensive data for specialized DeFi protocols. Our unified API aggregates data from:

- DefiLlama
- Dune Analytics
- Bitquery
- The Graph
- Token Terminal
- Messari

## Categories

### 1. Derivatives

```typescript
GET /v1/derivatives/markets
```

Access derivatives market data:

#### DefiLlama Implementation
```typescript
// Get derivatives data
const response = await fetch('https://api.llama.fi/derivatives');

// Response format
{
  markets: [{
    protocol: string,
    market: string,
    asset: string,
    openInterest: number,
    volume24h: number,
    trades24h: number,
    fundingRate: number,
    longLiquidations24h: number,
    shortLiquidations24h: number
  }]
}
```

#### Dune Analytics Implementation
```typescript
// Get derivatives metrics
const derivatives = await client.query({
  queryId: "3693850",
  parameters: {
    protocol: "gmx",
    timeframe: "7d"
  }
});

// Response includes:
// - Trading volume
// - Open interest
// - Liquidations
// - PnL metrics
```

### 2. Options

```typescript
GET /v1/options/markets
```

Track options markets and Greeks:

#### The Graph Implementation
```graphql
query {
  optionMarkets(
    first: 100,
    orderBy: volume,
    orderDirection: desc
  ) {
    id
    underlying
    strike
    expiry
    type
    volume
    openInterest
    impliedVolatility
    delta
    gamma
    theta
    vega
  }
}
```

### 3. Insurance

```typescript
GET /v1/insurance/coverage
```

Access DeFi insurance metrics:

#### Bitquery Implementation
```graphql
query {
  ethereum {
    insuranceProtocols(
      options: {desc: "tvl", limit: 100}
    ) {
      protocol {
        name
        address
      }
      tvl: smartContractCalls {
        sum(of: value)
      }
      coverage {
        asset
        amount
        premium
      }
      claims {
        count
        paid
        rejected
      }
    }
  }
}
```

### 4. Yield Aggregators

```typescript
GET /v1/yield/vaults
```

Track yield aggregator performance:

#### DefiLlama Implementation
```typescript
// Get vault data
const response = await fetch('https://yields.llama.fi/pools');

// Response format
{
  data: [{
    pool: string,
    project: string,
    chain: string,
    tvlUsd: number,
    apy: number,
    apyBase: number,
    apyReward: number,
    rewardTokens: string[],
    il7d: number,
    status: string
  }]
}
```

### 5. Structured Products

```typescript
GET /v1/structured/products
```

Access structured DeFi products:

#### Dune Analytics Implementation
```typescript
// Get product metrics
const products = await client.query({
  queryId: "3685760",
  parameters: {
    category: "structured",
    status: "active"
  }
});

// Response includes:
// - Product types
// - Performance metrics
// - Risk parameters
// - User positions
```

## Common Parameters

| Parameter | Type | Description | Default | Required |
|-----------|------|-------------|---------|----------|
| `protocol` | string | Protocol name | - | Yes |
| `asset` | string | Underlying asset | - | No |
| `timeframe` | string | Data period | 24h | No |
| `status` | string | Product status | active | No |

## Response Format

```typescript
{
  status: 200,
  data: {
    derivatives: {
      markets: [{
        name: string,
        type: string,
        underlying: string,
        metrics: {
          openInterest: number,
          volume24h: number,
          fundingRate: number
        }
      }],
      options: [{
        strike: number,
        expiry: number,
        type: string,
        greeks: {
          delta: number,
          gamma: number,
          theta: number,
          vega: number
        }
      }],
      insurance: [{
        protocol: string,
        coverage: number,
        premium: number,
        claims: {
          total: number,
          paid: number
        }
      }]
    },
    metadata: {
      timestamp: number,
      provider: string
    }
  }
}
```

## WebSocket Subscriptions

Subscribe to real-time DeFi updates:

```typescript
// Bitquery WebSocket
const ws = new WebSocket('wss://streaming.bitquery.io/graphql');

ws.send(JSON.stringify({
  type: 'start',
  id: 'defi_metrics',
  payload: {
    query: `subscription {
      DerivativesMarkets {
        Market {
          Name
          OpenInterest
          Volume
          FundingRate
        }
        Options {
          Strike
          IV
          Greeks
        }
        Insurance {
          Coverage
          Claims
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
| The Graph | 15 seconds | 1000/day |
| Dune | 30 minutes | 100/day |
| Bitquery | 1 minute | 100/day |
| Token Terminal | 5 minutes | 500/day |

## Best Practices

1. **Risk Management**
   - Monitor liquidation risks
   - Track collateral health
   - Validate oracle prices

2. **Performance**
   - Cache static data
   - Batch related requests
   - Use WebSocket for real-time

3. **Accuracy**
   - Cross-reference prices
   - Verify settlement data
   - Handle precision

4. **Monitoring**
   - Track funding rates
   - Monitor liquidations
   - Alert on anomalies

## Example Implementation

```typescript
import { DefiLlama, TheGraph, Dune } from '@blockchain/api';

class DefiDataAggregator {
  private providers: {
    defillama: DefiLlama;
    thegraph: TheGraph;
    dune: Dune;
  };

  constructor(config: Config) {
    this.providers = {
      defillama: new DefiLlama(config.defillamaKey),
      thegraph: new TheGraph(config.graphKey),
      dune: new Dune(config.duneKey)
    };
  }

  async getDerivativesData(protocol: string) {
    const [markets, options, insurance] = await Promise.all([
      this.getMarketsData(protocol),
      this.getOptionsData(protocol),
      this.getInsuranceData(protocol)
    ]);

    return {
      markets,
      options,
      insurance
    };
  }

  async monitorMarkets(callback: (event: any) => void) {
    // Set up WebSocket monitoring
    const ws = new WebSocket('wss://streaming.bitquery.io/graphql');
    
    // Subscribe to market events
    ws.send(JSON.stringify({
      type: 'start',
      id: 'market_events',
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