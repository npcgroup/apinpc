# Token Data

## Overview

Access comprehensive token data across multiple chains and protocols. Our unified API aggregates token data from:

- DefiLlama Price API
- Dune Analytics
- Bitquery
- The Graph
- Footprint Analytics
- CoinGecko Integration

## Endpoints

### Get Token Prices

```typescript
GET /v1/tokens/prices
```

Get current and historical token prices across multiple sources:

#### DefiLlama Implementation
```typescript
// Get current prices
const response = await fetch('https://coins.llama.fi/prices/current/ethereum:0x...,bsc:0x...');

// Get historical prices
const history = await fetch('https://coins.llama.fi/chart/ethereum:0x...?start=1640995200&span=1');

// Response format
{
  coins: {
    "ethereum:0x...": {
      price: number,
      timestamp: number,
      confidence: number
    }
  }
}
```

#### Bitquery Implementation
```graphql
query {
  ethereum {
    dexTrades(
      options: {desc: "block.timestamp.time", limit: 1}
      baseCurrency: {is: "0x..."}
      quoteCurrency: {is: "0x..."}
    ) {
      block {
        timestamp {
          time(format: "%Y-%m-%d %H:%M:%S")
        }
      }
      quotePrice
      tradeAmount(in: USD)
    }
  }
}
```

### Get Token Holders

```typescript
GET /v1/tokens/{token_address}/holders
```

Access token holder data and distribution metrics:

#### Dune Analytics Implementation
```typescript
const client = new DuneClient(DUNE_API_KEY);
const result = await client.query({
  queryId: "3685760",
  parameters: {
    token_address: "0x..."
  }
});
```

#### The Graph Implementation
```graphql
query {
  token(id: "0x...") {
    totalSupply
    holders {
      id
      balance
      lastTransferTimestamp
    }
    transferCount
    txCount
  }
}
```

### Get Token Transfers

```typescript
GET /v1/tokens/{token_address}/transfers
```

Track token transfer activity:

#### Bitquery Implementation
```graphql
query {
  ethereum {
    transfers(
      currency: {is: "0x..."}
      options: {desc: "block.timestamp.time", limit: 100}
    ) {
      block {
        timestamp {
          time(format: "%Y-%m-%d %H:%M:%S")
        }
      }
      sender {
        address
      }
      receiver {
        address
      }
      amount
      transaction {
        hash
      }
    }
  }
}
```

### Get Token Metadata

```typescript
GET /v1/tokens/{token_address}/metadata
```

Access comprehensive token information:

#### DefiLlama Implementation
```typescript
// Get token info
const response = await fetch('https://api.llama.fi/token/ethereum:0x...');

// Response format
{
  symbol: string,
  name: string,
  decimals: number,
  chains: string[],
  totalSupply: number,
  addresses: {[chain: string]: string},
  coingeckoId: string
}
```

## Common Parameters

| Parameter | Type | Description | Default | Required |
|-----------|------|-------------|---------|----------|
| `chain` | string | Blockchain network | ethereum | Yes |
| `address` | string | Token contract address | - | Yes |
| `from` | timestamp | Start time | -24h | No |
| `to` | timestamp | End time | now | No |
| `limit` | number | Results per page | 100 | No |
| `offset` | number | Pagination offset | 0 | No |

## Response Format

```typescript
{
  status: 200,
  data: {
    token: {
      address: string,
      symbol: string,
      name: string,
      decimals: number,
      totalSupply: string,
      holders: number,
      transfers: number,
      price: {
        usd: number,
        usd_24h_change: number,
        last_updated_at: number
      },
      market_data: {
        market_cap: number,
        volume_24h: number,
        fdv: number
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

Subscribe to real-time token updates:

```typescript
// Bitquery WebSocket
const ws = new WebSocket('wss://streaming.bitquery.io/graphql');

ws.send(JSON.stringify({
  type: 'start',
  id: 'token_transfers',
  payload: {
    query: `subscription {
      EVM(network: eth) {
        TokenTransfers(
          where: {Token: {Address: {is: "0x..."}}}
        ) {
          Transaction {
            Hash
            From
            To
          }
          Amount
          Token {
            Symbol
            Name
          }
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
| Bitquery | 1 minute | 100/day |
| The Graph | 15 seconds | 1000/day |
| Dune | 30 minutes | 100/day |
| CoinGecko | 1 minute | 50/min |

## Error Handling

```typescript
class TokenDataProvider {
  async getTokenPrice(address: string): Promise<number> {
    try {
      // Try primary source
      const price = await this.defiLlama.getPrice(address);
      return price;
    } catch (error) {
      // Fall back to secondary source
      try {
        const backup = await this.bitquery.getPrice(address);
        return backup;
      } catch (backupError) {
        // Fall back to tertiary source
        return this.coingecko.getPrice(address);
      }
    }
  }
}
```

## Best Practices

1. **Data Consistency**
   - Cross-reference prices across sources
   - Implement confidence thresholds
   - Handle decimal precision correctly

2. **Performance**
   - Cache frequently accessed metadata
   - Batch token requests
   - Use GraphQL for precise data fetching

3. **Reliability**
   - Implement multiple data sources
   - Handle network-specific quirks
   - Validate token contracts

4. **Security**
   - Verify token contracts
   - Check for honeypot tokens
   - Monitor for unusual activity

## Example Implementation

```typescript
import { DefiLlama, Bitquery, TheGraph } from '@blockchain/api';

class TokenDataAggregator {
  private providers: {
    defillama: DefiLlama;
    bitquery: Bitquery;
    thegraph: TheGraph;
  };

  constructor(config: Config) {
    this.providers = {
      defillama: new DefiLlama(config.defillamaKey),
      bitquery: new Bitquery(config.bitqueryKey),
      thegraph: new TheGraph(config.graphKey)
    };
  }

  async getTokenData(chain: string, address: string) {
    const [price, metadata, holders] = await Promise.all([
      this.getTokenPrice(chain, address),
      this.getTokenMetadata(chain, address),
      this.getTokenHolders(chain, address)
    ]);

    return {
      price,
      metadata,
      holders
    };
  }
}
```

## Need Help?

- Check our [API Reference](../../api-reference/README.md)
- Join our [Discord](https://discord.gg/blockchain-api)
- Submit issues on [GitHub](https://github.com/blockchain-api/issues)