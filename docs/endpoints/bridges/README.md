# Cross-Chain Data

## Overview

Access comprehensive cross-chain bridge and transfer data. Our unified API aggregates data from:

- DefiLlama Bridge API
- Dune Analytics
- Bitquery
- The Graph
- L2Beat
- Footprint Analytics

## Endpoints

### Get Bridge TVL

```typescript
GET /v1/bridges/tvl
```

Get Total Value Locked across bridges:

#### DefiLlama Implementation
```typescript
// Get bridge TVL
const response = await fetch('https://api.llama.fi/bridges');

// Response format
{
  bridges: [{
    name: string,
    chainMapping: Record<string, string>,
    chains: string[],
    tvl: number,
    lastHour: {
      deposits: number,
      withdrawals: number
    },
    lastDay: {
      deposits: number,
      withdrawals: number
    }
  }]
}
```

#### L2Beat Implementation
```typescript
// Get L2 bridge data
const response = await fetch('https://api.l2beat.com/api/bridges');

// Response format
{
  bridges: [{
    id: string,
    name: string,
    tvl: {
      usd: number,
      eth: number,
      tokens: [{
        symbol: string,
        amount: number,
        usdValue: number
      }]
    }
  }]
}
```

### Get Bridge Transfers

```typescript
GET /v1/bridges/transfers
```

Track cross-chain bridge transfers:

#### Bitquery Implementation
```graphql
query {
  ethereum {
    bridgeTransfers: smartContractCalls(
      smartContractAddress: {in: ["0x bridge addresses..."]}
      options: {desc: "block.timestamp.time", limit: 100}
    ) {
      transaction {
        hash
        from
        to
        value
      }
      block {
        timestamp {
          time(format: "%Y-%m-%d %H:%M:%S")
        }
      }
      smartContract {
        address {
          address
        }
      }
      arguments {
        value
        argtype
      }
    }
  }
}
```

### Get Bridge Security

```typescript
GET /v1/bridges/{bridge_id}/security
```

Access bridge security metrics:

#### L2Beat Implementation
```typescript
// Get bridge security info
const response = await fetch('https://api.l2beat.com/api/bridges/risk-data');

// Response includes:
// - Security model
// - Upgrade delays
// - Validation methods
// - Risk parameters
```

### Get Bridge Tokens

```typescript
GET /v1/bridges/{bridge_id}/tokens
```

List supported tokens and volumes:

#### Dune Analytics Implementation
```typescript
// Get bridge token data
const tokens = await client.query({
  queryId: "3693850",
  parameters: {
    bridge_address: "0x..."
  }
});

// Response includes:
// - Supported tokens
// - Token volumes
// - Token limits
// - Historical data
```

## Common Parameters

| Parameter | Type | Description | Default | Required |
|-----------|------|-------------|---------|----------|
| `bridge_id` | string | Bridge identifier | - | Yes |
| `chain_from` | string | Source chain | - | No |
| `chain_to` | string | Destination chain | - | No |
| `timeframe` | string | Time period | 24h | No |
| `token` | string | Token address | - | No |

## Response Format

```typescript
{
  status: 200,
  data: {
    bridge: {
      id: string,
      name: string,
      chains: string[],
      metrics: {
        tvl: {
          total: number,
          byChain: {
            [chain: string]: number
          },
          byToken: {
            [token: string]: number
          }
        },
        volume: {
          total24h: number,
          inflow24h: number,
          outflow24h: number
        },
        security: {
          riskLevel: string,
          securityModel: string,
          validationPeriod: number
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

Subscribe to real-time bridge events:

```typescript
// Bitquery WebSocket
const ws = new WebSocket('wss://streaming.bitquery.io/graphql');

ws.send(JSON.stringify({
  type: 'start',
  id: 'bridge_transfers',
  payload: {
    query: `subscription {
      BridgeTransfers {
        Transaction {
          Hash
          From
          To
          Value
        }
        SourceChain
        DestinationChain
        Token {
          Symbol
          Amount
        }
        Status
      }
    }`
  }
}));
```

## Rate Limits & Caching

| Provider | Cache Duration | Rate Limit |
|----------|---------------|------------|
| DefiLlama | 5 minutes | 300/5min |
| L2Beat | 1 minute | 100/min |
| Bitquery | 1 minute | 100/day |
| The Graph | 15 seconds | 1000/day |
| Dune | 30 minutes | 100/day |

## Error Handling

```typescript
class BridgeDataProvider {
  async getBridgeTVL(bridgeId: string): Promise<number> {
    try {
      // Try primary source
      const tvl = await this.defillama.getBridgeTVL(bridgeId);
      return tvl;
    } catch (error) {
      // Fall back to secondary source
      try {
        const backup = await this.l2beat.getBridgeTVL(bridgeId);
        return backup;
      } catch (backupError) {
        // Fall back to tertiary source
        return this.dune.getBridgeTVL(bridgeId);
      }
    }
  }
}
```

## Best Practices

1. **Security First**
   - Validate bridge addresses
   - Monitor for exploits
   - Track security parameters

2. **Data Consistency**
   - Cross-reference volumes
   - Verify token mappings
   - Handle chain IDs properly

3. **Performance**
   - Cache bridge metadata
   - Batch transfer queries
   - Use WebSocket for monitoring

4. **Reliability**
   - Implement fallback providers
   - Handle network outages
   - Monitor bridge status

## Example Implementation

```typescript
import { DefiLlama, L2Beat, Bitquery } from '@blockchain/api';

class BridgeDataAggregator {
  private providers: {
    defillama: DefiLlama;
    l2beat: L2Beat;
    bitquery: Bitquery;
  };

  constructor(config: Config) {
    this.providers = {
      defillama: new DefiLlama(config.defillamaKey),
      l2beat: new L2Beat(config.l2beatKey),
      bitquery: new Bitquery(config.bitqueryKey)
    };
  }

  async getBridgeData(bridgeId: string) {
    const [tvl, transfers, security] = await Promise.all([
      this.getBridgeTVL(bridgeId),
      this.getBridgeTransfers(bridgeId),
      this.getBridgeSecurity(bridgeId)
    ]);

    return {
      tvl,
      transfers,
      security
    };
  }

  async monitorBridge(bridgeId: string, callback: (event: any) => void) {
    // Set up WebSocket monitoring
    const ws = new WebSocket('wss://streaming.bitquery.io/graphql');
    
    // Subscribe to bridge events
    ws.send(JSON.stringify({
      type: 'start',
      id: `bridge_${bridgeId}`,
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