# DeFi Lending Data

## Overview

Access comprehensive DeFi lending protocol data and analytics. Our unified API aggregates lending data from:

- DefiLlama Lending API
- Dune Analytics
- Bitquery
- The Graph
- Aave Subgraphs
- Compound Analytics

## Endpoints

### Get Lending Pools

```typescript
GET /v1/lending/pools/{protocol}
```

Access lending pool metrics:

#### DefiLlama Implementation
```typescript
// Get lending pool data
const response = await fetch('https://api.llama.fi/protocol/aave/pools');

// Response format
{
  pools: [{
    id: string,
    name: string,
    tvl: number,
    borrowed: number,
    supplied: number,
    utilization: number,
    reserves: [{
      token: string,
      totalSupply: number,
      totalBorrow: number,
      supplyApy: number,
      borrowApy: number
    }]
  }]
}
```

#### The Graph Implementation
```graphql
query {
  lendingPools(
    first: 100,
    orderBy: totalValueLockedUSD,
    orderDirection: desc
  ) {
    id
    name
    totalValueLockedUSD
    totalBorrowsUSD
    inputTokens {
      id
      symbol
      decimals
    }
    outputToken {
      id
      symbol
      decimals
    }
    rewardTokens {
      id
      symbol
      decimals
    }
    rates {
      side
      rate
      duration
    }
  }
}
```

### Get Borrowing Rates

```typescript
GET /v1/lending/rates/{token}
```

Track lending and borrowing rates:

#### Aave Implementation
```typescript
// Get token rates
const response = await fetch('https://api.aave.com/data/rates', {
  headers: { 'Authorization': `Bearer ${AAVE_KEY}` }
});

// Response includes:
// - Supply APY
// - Borrow APY/APR
// - Incentive rates
// - Historical rates
```

### Get Liquidation Data

```typescript
GET /v1/lending/liquidations
```

Monitor liquidation events and risks:

#### Dune Analytics Implementation
```typescript
// Get liquidation metrics
const liquidations = await client.query({
  queryId: "3685928",
  parameters: {
    protocol: "compound",
    timeframe: "7d"
  }
});

// Response includes:
// - Liquidation events
// - At-risk positions
// - Liquidation thresholds
// - Historical data
```

### Get Lending Positions

```typescript
GET /v1/lending/positions/{address}
```

Access user lending positions:

#### Compound Implementation
```typescript
// Get user positions
const response = await fetch(`https://api.compound.finance/api/v2/account?addresses[]=${address}`);

// Response format
{
  accounts: [{
    address: string,
    tokens: [{
      symbol: string,
      supplyBalance: number,
      supplyBalanceUSD: number,
      borrowBalance: number,
      borrowBalanceUSD: number,
      supplyRate: number,
      borrowRate: number
    }],
    health: number,
    totalBorrowValueInUSD: number,
    totalCollateralValueInUSD: number
  }]
}
```

## Common Parameters

| Parameter | Type | Description | Default | Required |
|-----------|------|-------------|---------|----------|
| `protocol` | string | Lending protocol | - | Yes |
| `token` | string | Asset address | - | No |
| `timeframe` | string | Data period | 24h | No |
| `network` | string | Blockchain network | ethereum | No |

## Response Format

```typescript
{
  status: 200,
  data: {
    lending: {
      protocol: {
        id: string,
        name: string,
        tvl: number,
        borrowed: number
      },
      pools: [{
        id: string,
        name: string,
        assets: [{
          token: string,
          symbol: string,
          supplied: number,
          borrowed: number,
          utilization: number,
          rates: {
            supply: number,
            borrow: number,
            stable: number
          }
        }],
        metrics: {
          tvl: number,
          borrowed: number,
          supplied: number,
          utilization: number
        }
      }],
      positions: [{
        user: string,
        collateral: [{
          token: string,
          amount: number,
          valueUSD: number
        }],
        debt: [{
          token: string,
          amount: number,
          valueUSD: number
        }],
        health: number
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

Subscribe to real-time lending updates:

```typescript
// Bitquery WebSocket
const ws = new WebSocket('wss://streaming.bitquery.io/graphql');

ws.send(JSON.stringify({
  type: 'start',
  id: 'lending_metrics',
  payload: {
    query: `subscription {
      LendingMetrics(protocol: "aave") {
        Pool {
          Id
          Name
          TVL
          Borrowed
        }
        Rates {
          Token
          SupplyAPY
          BorrowAPY
        }
        Liquidations {
          User
          Collateral
          Debt
          LiquidationPrice
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
| Aave | 1 minute | 500/min |
| Compound | 15 seconds | 100/min |
| The Graph | 15 seconds | 1000/day |
| Dune | 30 minutes | 100/day |

## Error Handling

```typescript
class LendingDataProvider {
  async getLendingPoolData(protocol: string, poolId: string): Promise<any> {
    try {
      // Try primary source
      const data = await this.defillama.getPool(protocol, poolId);
      return data;
    } catch (error) {
      // Fall back to secondary source
      try {
        const backup = await this.thegraph.getPool(protocol, poolId);
        return backup;
      } catch (backupError) {
        // Fall back to tertiary source
        return this.dune.getPool(protocol, poolId);
      }
    }
  }
}
```

## Best Practices

1. **Risk Management**
   - Monitor health factors
   - Track liquidation risks
   - Validate collateral values

2. **Data Accuracy**
   - Cross-reference rates
   - Verify token prices
   - Handle decimal precision

3. **Performance**
   - Cache stable metrics
   - Batch position updates
   - Use WebSocket for monitoring

4. **Security**
   - Validate user inputs
   - Monitor for exploits
   - Track protocol upgrades

## Example Implementation

```typescript
import { DefiLlama, Aave, Compound } from '@blockchain/api';

class LendingDataAggregator {
  private providers: {
    defillama: DefiLlama;
    aave: Aave;
    compound: Compound;
  };

  constructor(config: Config) {
    this.providers = {
      defillama: new DefiLlama(config.defillamaKey),
      aave: new Aave(config.aaveKey),
      compound: new Compound(config.compoundKey)
    };
  }

  async getLendingData(protocol: string) {
    const [pools, rates, positions] = await Promise.all([
      this.getLendingPools(protocol),
      this.getBorrowingRates(protocol),
      this.getLendingPositions(protocol)
    ]);

    return {
      pools,
      rates,
      positions
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