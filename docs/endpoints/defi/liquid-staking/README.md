# Liquid Staking

## Overview

Access comprehensive liquid staking protocol data. Our unified API aggregates data from:

- DefiLlama Staking API
- Dune Analytics
- The Graph
- Etherscan
- Beaconcha.in

## Endpoints

### Get Staking Protocols

```typescript
GET /v1/staking/protocols
```

Access liquid staking protocol metrics:

#### DefiLlama Implementation
```typescript
// Get staking data
const response = await fetch('https://api.llama.fi/staking');

// Response format
{
  protocols: [{
    name: string,
    symbol: string,
    tvl: number,
    stakingRatio: number,
    apr: number,
    validators: number,
    totalStaked: {
      eth: number,
      usd: number
    },
    marketShare: number
  }]
}
```

### Get Validator Performance

```typescript
GET /v1/staking/validators/{protocol}
```

Track validator metrics:

#### Beaconcha.in Implementation
```typescript
// Get validator metrics
const response = await fetch(`https://beaconcha.in/api/v1/validator/${validatorIndex}`, {
  headers: { 'apikey': BEACONCHAIN_KEY }
});

// Response includes:
// - Attestation effectiveness
// - Proposal performance
// - Rewards earned
// - Uptime statistics
```

### Get Staking Rewards

```typescript
GET /v1/staking/rewards/{protocol}
```

Access staking rewards data:

#### The Graph Implementation
```graphql
query {
  stakingRewards(
    first: 100,
    orderBy: timestamp,
    orderDirection: desc
  ) {
    protocol
    epoch
    totalRewards
    rewardRate
    apr
    validatorRewards
    userRewards
    rewardToken {
      id
      symbol
    }
  }
}
```

### Get Protocol Health

```typescript
GET /v1/staking/health/{protocol}
```

Monitor protocol health metrics:

#### Dune Analytics Implementation
```typescript
// Get health metrics
const health = await client.query({
  queryId: "3682939",
  parameters: {
    protocol: "lido",
    timeframe: "30d"
  }
});

// Response includes:
// - Node operator distribution
// - Oracle performance
// - Slashing events
// - Protocol parameters
```

## Common Parameters

| Parameter | Type | Description | Default | Required |
|-----------|------|-------------|---------|----------|
| `protocol` | string | Staking protocol | - | Yes |
| `network` | string | Network name | ethereum | No |
| `timeframe` | string | Data period | 24h | No |
| `validator` | string | Validator address | - | No |

## Response Format

```typescript
{
  status: 200,
  data: {
    staking: {
      protocol: {
        name: string,
        tvl: number,
        apr: number
      },
      metrics: {
        validators: {
          total: number,
          active: number,
          performance: number
        },
        rewards: {
          total: number,
          apr: number,
          distributed: number
        },
        health: {
          nodeDistribution: number,
          oracleResponses: number,
          slashingEvents: number
        }
      },
      tokens: {
        staked: {
          amount: number,
          value: number
        },
        liquid: {
          amount: number,
          value: number
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

Subscribe to real-time staking updates:

```typescript
// Bitquery WebSocket
const ws = new WebSocket('wss://streaming.bitquery.io/graphql');

ws.send(JSON.stringify({
  type: 'start',
  id: 'staking_metrics',
  payload: {
    query: `subscription {
      StakingMetrics(protocol: "lido") {
        Validators {
          Active
          Performance
        }
        Rewards {
          Amount
          APR
        }
        Health {
          NodeDistribution
          OracleStatus
        }
      }
    }`
  }
}));
```

## Best Practices

1. **Validator Management**
   - Monitor performance
   - Track slashing risks
   - Validate rewards

2. **Protocol Security**
   - Monitor node distribution
   - Track oracle responses
   - Validate consensus

3. **Performance**
   - Cache validator sets
   - Batch reward queries
   - Stream large datasets

4. **Risk Management**
   - Monitor slashing events
   - Track withdrawal queues
   - Validate node operators

## Example Implementation

```typescript
import { DefiLlama, BeaconChain, TheGraph } from '@blockchain/api';

class StakingDataAggregator {
  private providers: {
    defillama: DefiLlama;
    beaconchain: BeaconChain;
    thegraph: TheGraph;
  };

  constructor(config: Config) {
    this.providers = {
      defillama: new DefiLlama(config.defillamaKey),
      beaconchain: new BeaconChain(config.beaconchainKey),
      thegraph: new TheGraph(config.graphKey)
    };
  }

  async getStakingData(protocol: string) {
    const [metrics, validators, rewards] = await Promise.all([
      this.getProtocolMetrics(protocol),
      this.getValidatorMetrics(protocol),
      this.getRewardsData(protocol)
    ]);

    return {
      metrics,
      validators,
      rewards
    };
  }

  async monitorValidators(protocol: string, callback: (event: any) => void) {
    // Set up WebSocket monitoring
    const ws = new WebSocket('wss://streaming.bitquery.io/graphql');
    
    // Subscribe to validator events
    ws.send(JSON.stringify({
      type: 'start',
      id: `validators_${protocol}`,
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