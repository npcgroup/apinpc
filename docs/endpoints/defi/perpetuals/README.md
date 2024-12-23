# Perpetual Futures

## Overview

Access comprehensive perpetual futures trading data. Our unified API aggregates data from:

- DefiLlama Derivatives API
- Dune Analytics
- The Graph
- Token Terminal
- Bitquery
- GMX Analytics

## Endpoints

### Get Perpetual Markets

```typescript
GET /v1/perpetuals/markets
```

Access perpetual market metrics:

#### DefiLlama Implementation
```typescript
// Get perpetuals data
const response = await fetch('https://api.llama.fi/derivatives/perpetuals');

// Response format
{
  markets: [{
    protocol: string,
    pair: string,
    longOpenInterest: number,
    shortOpenInterest: number,
    fundingRate: number,
    volume24h: number,
    liquidations24h: number,
    averageLeverage: number,
    maxLeverage: number,
    indexPrice: number,
    markPrice: number
  }]
}
```

### Get Position Data

```typescript
GET /v1/perpetuals/positions/{protocol}
```

Track open positions and leverage:

#### The Graph Implementation
```graphql
query {
  perpetualPositions(
    first: 100,
    orderBy: size,
    orderDirection: desc
  ) {
    id
    trader
    market
    isLong
    leverage
    entryPrice
    liquidationPrice
    size
    margin
    unrealizedPnl
    lastUpdateTimestamp
    collateral {
      token
      amount
    }
  }
}
```

### Get Funding Rates

```typescript
GET /v1/perpetuals/funding/{market}
```

Access funding rate history:

#### Dune Analytics Implementation
```typescript
// Get funding metrics
const funding = await client.query({
  queryId: "3693850",
  parameters: {
    protocol: "gmx",
    market: "ETH-USD"
  }
});

// Response includes:
// - Historical rates
// - Payment flows
// - Rate volatility
// - Market imbalance
```

### Get Liquidation Data

```typescript
GET /v1/perpetuals/liquidations
```

Monitor liquidation events:

#### Bitquery Implementation
```graphql
query {
  ethereum {
    perpetualLiquidations: smartContractCalls(
      smartContractAddress: {in: ["0x perpetual addresses..."]}
      options: {desc: "block.timestamp.time", limit: 100}
    ) {
      transaction {
        hash
      }
      block {
        timestamp {
          time(format: "%Y-%m-%d %H:%M:%S")
        }
      }
      arguments {
        position {
          trader
          market
          size
          liquidationPrice
        }
        liquidationFee
        liquidator
      }
    }
  }
}
```

## Common Parameters

| Parameter | Type | Description | Default | Required |
|-----------|------|-------------|---------|----------|
| `protocol` | string | Trading protocol | - | Yes |
| `market` | string | Trading pair | - | No |
| `timeframe` | string | Data period | 24h | No |
| `trader` | string | Trader address | - | No |

## Response Format

```typescript
{
  status: 200,
  data: {
    perpetuals: {
      protocol: {
        name: string,
        volume24h: number,
        openInterest: number
      },
      markets: [{
        pair: string,
        metrics: {
          longOI: number,
          shortOI: number,
          fundingRate: number,
          volume: number
        },
        prices: {
          index: number,
          mark: number,
          impact: number
        },
        risk: {
          maxLeverage: number,
          maintenanceMargin: number,
          liquidationThreshold: number
        }
      }],
      positions: [{
        trader: string,
        market: string,
        side: string,
        size: number,
        leverage: number,
        pnl: number
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

Subscribe to real-time perpetuals data:

```typescript
// Bitquery WebSocket
const ws = new WebSocket('wss://streaming.bitquery.io/graphql');

ws.send(JSON.stringify({
  type: 'start',
  id: 'perpetuals_data',
  payload: {
    query: `subscription {
      PerpetualMarkets {
        Market {
          Pair
          OpenInterest
          FundingRate
        }
        Trades {
          Size
          Price
          Leverage
        }
        Liquidations {
          Position
          Price
          Size
        }
      }
    }`
  }
}));
```

## Best Practices

1. **Risk Management**
   - Monitor leverage levels
   - Track liquidation risks
   - Validate margin requirements

2. **Market Monitoring**
   - Track funding rates
   - Monitor price impact
   - Alert on large positions

3. **Performance**
   - Cache market data
   - Batch position updates
   - Stream price feeds

4. **Position Tracking**
   - Monitor PnL
   - Track margin levels
   - Alert on liquidations

## Example Implementation

```typescript
import { DefiLlama, TheGraph, Bitquery } from '@blockchain/api';

class PerpetualsDataAggregator {
  private providers: {
    defillama: DefiLlama;
    thegraph: TheGraph;
    bitquery: Bitquery;
  };

  constructor(config: Config) {
    this.providers = {
      defillama: new DefiLlama(config.defillamaKey),
      thegraph: new TheGraph(config.graphKey),
      bitquery: new Bitquery(config.bitqueryKey)
    };
  }

  async getPerpetualsData(protocol: string) {
    const [markets, positions, funding] = await Promise.all([
      this.getMarketMetrics(protocol),
      this.getPositionData(protocol),
      this.getFundingData(protocol)
    ]);

    return {
      markets,
      positions,
      funding
    };
  }

  async monitorLiquidations(callback: (event: any) => void) {
    // Set up WebSocket monitoring
    const ws = new WebSocket('wss://streaming.bitquery.io/graphql');
    
    // Subscribe to liquidation events
    ws.send(JSON.stringify({
      type: 'start',
      id: 'liquidation_events',
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