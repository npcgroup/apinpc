# Synthetics

## Overview

Access comprehensive synthetic asset protocol data. Our unified API aggregates data from:

- DefiLlama Synthetics API
- Dune Analytics
- The Graph
- Token Terminal
- Bitquery

## Endpoints

### Get Synthetic Assets

```typescript
GET /v1/synthetics/assets
```

Access synthetic asset metrics:

#### DefiLlama Implementation
```typescript
// Get synthetic assets data
const response = await fetch('https://api.llama.fi/synthetics/assets');

// Response format
{
  assets: [{
    name: string,
    symbol: string,
    underlying: string,
    protocol: string,
    totalSupply: number,
    marketCap: number,
    collateralization: number,
    mintingFee: number,
    burningFee: number,
    volume24h: number
  }]
}
```

### Get Collateral Health

```typescript
GET /v1/synthetics/collateral/{protocol}
```

Monitor collateral ratios and health:

#### The Graph Implementation
```graphql
query {
  syntheticVaults(
    first: 100,
    orderBy: collateralRatio,
    orderDirection: desc
  ) {
    id
    collateralType
    totalCollateral
    totalDebt
    collateralRatio
    minimumRatio
    liquidationPenalty
    stabilityFee
    positions {
      owner
      collateralAmount
      debtAmount
      ratio
    }
  }
}
```

### Get Oracle Data

```typescript
GET /v1/synthetics/oracles/{protocol}
```

Access price feed and oracle data:

#### Dune Analytics Implementation
```typescript
// Get oracle metrics
const oracles = await client.query({
  queryId: "3685583",
  parameters: {
    protocol: "synthetix",
    timeframe: "24h"
  }
});

// Response includes:
// - Price updates
// - Oracle providers
// - Deviation metrics
// - Update frequency
```

### Get Market Activity

```typescript
GET /v1/synthetics/markets/{asset}
```

Track synthetic asset trading activity:

#### Bitquery Implementation
```graphql
query {
  ethereum {
    syntheticTrades: dexTrades(
      options: {desc: "block.timestamp.time", limit: 100}
      baseCurrency: {is: "synth_address"}
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
      sellAmount
      price
      side
      maker {
        address
      }
      taker {
        address
      }
    }
  }
}
```

## Common Parameters

| Parameter | Type | Description | Default | Required |
|-----------|------|-------------|---------|----------|
| `protocol` | string | Synthetic protocol | - | Yes |
| `asset` | string | Synthetic asset address | - | No |
| `timeframe` | string | Data period | 24h | No |
| `collateralType` | string | Collateral asset | - | No |

## Response Format

```typescript
{
  status: 200,
  data: {
    synthetics: {
      protocol: {
        name: string,
        tvl: number,
        volume24h: number
      },
      assets: [{
        symbol: string,
        underlying: string,
        metrics: {
          supply: number,
          marketCap: number,
          volume: number,
          collateralization: number
        },
        oracles: [{
          provider: string,
          price: number,
          lastUpdate: number
        }],
        trading: {
          volume24h: number,
          trades24h: number,
          openInterest: number
        }
      }],
      collateral: {
        totalLocked: number,
        healthRatio: number,
        liquidationRisk: number
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

Subscribe to real-time synthetic asset updates:

```typescript
// Bitquery WebSocket
const ws = new WebSocket('wss://streaming.bitquery.io/graphql');

ws.send(JSON.stringify({
  type: 'start',
  id: 'synthetic_metrics',
  payload: {
    query: `subscription {
      SyntheticAssets {
        Asset {
          Symbol
          Price
          Supply
        }
        Collateral {
          Ratio
          Health
        }
        Trading {
          Volume
          Trades
        }
        Oracles {
          Provider
          Price
          Update
        }
      }
    }`
  }
}));
```

## Best Practices

1. **Risk Management**
   - Monitor collateral ratios
   - Track liquidation risks
   - Validate oracle prices

2. **Oracle Security**
   - Verify price feeds
   - Monitor update frequency
   - Cross-reference sources

3. **Performance**
   - Cache asset metadata
   - Batch market queries
   - Stream price updates

4. **Market Monitoring**
   - Track trading volume
   - Monitor liquidity
   - Alert on large trades

## Example Implementation

```typescript
import { DefiLlama, TheGraph, Bitquery } from '@blockchain/api';

class SyntheticsDataAggregator {
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

  async getSyntheticsData(protocol: string) {
    const [assets, collateral, oracles] = await Promise.all([
      this.getAssetMetrics(protocol),
      this.getCollateralHealth(protocol),
      this.getOracleData(protocol)
    ]);

    return {
      assets,
      collateral,
      oracles
    };
  }

  async monitorMarkets(asset: string, callback: (event: any) => void) {
    // Set up WebSocket monitoring
    const ws = new WebSocket('wss://streaming.bitquery.io/graphql');
    
    // Subscribe to market events
    ws.send(JSON.stringify({
      type: 'start',
      id: `markets_${asset}`,
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