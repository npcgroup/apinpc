# Chain Metrics

## Overview

Access comprehensive blockchain network metrics and analytics. Our unified API aggregates chain data from:

- Dune Analytics
- Bitquery
- Footprint Analytics
- The Graph
- Etherscan APIs
- Blockchain RPC Nodes

## Endpoints

### Get Chain Statistics

```typescript
GET /v1/metrics/{chain}/stats
```

Get comprehensive chain-level statistics:

#### Bitquery Implementation
```graphql
query {
  ethereum {
    blocks(options: {limit: 100, desc: "timestamp"}) {
      count
      blockTime: average(of: timestamp, window: {in: blocks, num: 100})
      gasUsed
      gasLimit
      difficulty
      size
    }
    transactions(options: {limit: 100, desc: "block.timestamp"}) {
      count
      gasPrice
      gas
      txCount: count
      uniqueAddresses: countDistinct(field: address)
    }
  }
}
```

#### Dune Analytics Implementation
```typescript
const client = new DuneClient(DUNE_API_KEY);

// Get chain metrics
const metrics = await client.query({
  queryId: "3575084", // Chain metrics query
  parameters: {
    chain: "ethereum",
    timeframe: "24h"
  }
});

// Response includes:
// - Block time/size/count
// - Transaction count/volume
// - Gas metrics
// - Network health
```

### Get Gas Analytics

```typescript
GET /v1/metrics/{chain}/gas
```

Access detailed gas price and usage metrics:

#### Etherscan Implementation
```typescript
// Get gas oracle data
const response = await fetch(
  `https://api.etherscan.io/api?module=gastracker&action=gasoracle&apikey=${ETHERSCAN_KEY}`
);

// Response format
{
  SafeGasPrice: string,
  ProposeGasPrice: string,
  FastGasPrice: string,
  suggestBaseFee: string,
  gasUsedRatio: string
}
```

#### The Graph Implementation
```graphql
query {
  gasMetrics(
    first: 100,
    orderBy: timestamp,
    orderDirection: desc
  ) {
    timestamp
    avgGasPrice
    avgGasLimit
    avgGasUsed
    maxGasPrice
    minGasPrice
    totalGasUsed
    totalTransactions
  }
}
```

### Get Network Health

```typescript
GET /v1/metrics/{chain}/health
```

Monitor network performance and health metrics:

#### RPC Node Implementation
```typescript
// Get network health metrics
const provider = new ethers.providers.JsonRpcProvider(RPC_URL);

const health = await Promise.all([
  provider.getBlockNumber(),
  provider.getGasPrice(),
  provider.getNetwork(),
  provider.ready
]);

// Response includes:
// - Node sync status
// - Network congestion
// - Peer count
// - Block propagation
```

### Get Validator Data

```typescript
GET /v1/metrics/{chain}/validators
```

Access validator and staking metrics:

#### Dune Analytics Implementation
```typescript
// Get validator metrics
const validators = await client.query({
  queryId: "3633434",
  parameters: {
    network: "ethereum",
    status: "active"
  }
});

// Response includes:
// - Active validators
// - Staking metrics
// - Validator performance
// - Rewards data
```

## Common Parameters

| Parameter | Type | Description | Default | Required |
|-----------|------|-------------|---------|----------|
| `timeframe` | string | Time period for data | 24h | No |
| `resolution` | string | Data point interval | 1h | No |
| `metric` | string | Specific metric to query | all | No |
| `format` | string | Response format | json | No |

## Response Format

```typescript
{
  status: 200,
  data: {
    chain: {
      id: string,
      name: string,
      metrics: {
        blocks: {
          count: number,
          time: number,
          size: number
        },
        transactions: {
          count: number,
          volume: number,
          uniqueAddresses: number
        },
        gas: {
          average: number,
          median: number,
          max: number,
          used: number
        },
        network: {
          peers: number,
          nodes: number,
          latency: number
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

Subscribe to real-time chain metrics:

```typescript
// Bitquery WebSocket
const ws = new WebSocket('wss://streaming.bitquery.io/graphql');

ws.send(JSON.stringify({
  type: 'start',
  id: 'chain_metrics',
  payload: {
    query: `subscription {
      ChainMetrics(network: ethereum) {
        Blocks {
          Number
          Time
          Size
          GasUsed
          GasLimit
        }
        Transactions {
          Count
          UniqueAddresses
          Volume
        }
        Network {
          PeerCount
          Latency
        }
      }
    }`
  }
}));
```

## Rate Limits & Caching

| Provider | Cache Duration | Rate Limit |
|----------|---------------|------------|
| Etherscan | 5 seconds | 100/min |
| Dune | 30 minutes | 100/day |
| Bitquery | 1 minute | 100/day |
| RPC Node | Real-time | Varies |
| The Graph | 15 seconds | 1000/day |

## Error Handling

```typescript
class ChainMetricsProvider {
  async getGasPrice(chain: string): Promise<number> {
    try {
      // Try primary source
      const price = await this.etherscan.getGasPrice(chain);
      return price;
    } catch (error) {
      // Fall back to secondary source
      try {
        const backup = await this.rpcNode.getGasPrice(chain);
        return backup;
      } catch (backupError) {
        // Fall back to tertiary source
        return this.bitquery.getGasPrice(chain);
      }
    }
  }
}
```

## Best Practices

1. **Data Reliability**
   - Cross-reference multiple nodes
   - Handle reorgs gracefully
   - Validate block finality

2. **Performance**
   - Cache static metrics
   - Batch RPC requests
   - Use WebSocket for real-time data

3. **Cost Optimization**
   - Use archive nodes selectively
   - Implement request batching
   - Cache historical data

4. **Monitoring**
   - Track node health
   - Monitor sync status
   - Alert on anomalies

## Example Implementation

```typescript
import { Etherscan, Bitquery, RPCNode } from '@blockchain/api';

class ChainMetricsAggregator {
  private providers: {
    etherscan: Etherscan;
    bitquery: Bitquery;
    rpcNode: RPCNode;
  };

  constructor(config: Config) {
    this.providers = {
      etherscan: new Etherscan(config.etherscanKey),
      bitquery: new Bitquery(config.bitqueryKey),
      rpcNode: new RPCNode(config.rpcUrl)
    };
  }

  async getChainMetrics(chain: string) {
    const [blocks, transactions, gas, health] = await Promise.all([
      this.getBlockMetrics(chain),
      this.getTransactionMetrics(chain),
      this.getGasMetrics(chain),
      this.getNetworkHealth(chain)
    ]);

    return {
      blocks,
      transactions,
      gas,
      health
    };
  }
}
```

## Need Help?

- Check our [API Reference](../../api-reference/README.md)
- Join our [Discord](https://discord.gg/blockchain-api)
- Submit issues on [GitHub](https://github.com/blockchain-api/issues)