# NFT Data

## Overview

Access comprehensive NFT market data and analytics. Our unified API aggregates NFT data from:

- DefiLlama NFT API
- Dune Analytics
- The Graph
- NFTScan
- Bitquery
- Reservoir

## Endpoints

### Get Collection Stats

```typescript
GET /v1/nfts/collections/{collection_id}/stats
```

Access collection-level metrics:

#### NFTScan Implementation
```typescript
// Get collection stats
const response = await fetch(`https://api.nftscan.com/api/v2/statistics/collection/${collection_id}`, {
  headers: { 'X-API-KEY': NFTSCAN_KEY }
});

// Response format
{
  collection: {
    name: string,
    symbol: string,
    floorPrice: number,
    volume24h: number,
    volumeTotal: number,
    holders: number,
    items: number,
    sales24h: number,
    averagePrice24h: number,
    marketCap: number
  }
}
```

### Get NFT Trades

```typescript
GET /v1/nfts/trades
```

Track NFT trading activity:

#### Reservoir Implementation
```typescript
// Get trading activity
const trades = await fetch('https://api.reservoir.tools/sales/v4', {
  headers: { 'x-api-key': RESERVOIR_KEY }
});

// Response includes:
// - Sale price
// - Token ID
// - Buyer/Seller
// - Marketplace
// - Transaction details
```

### Get Token Metadata

```typescript
GET /v1/nfts/{token_id}/metadata
```

Access NFT metadata and attributes:

#### The Graph Implementation
```graphql
query {
  token(id: $tokenId) {
    id
    tokenID
    owner {
      id
    }
    metadata {
      name
      description
      image
      attributes {
        traitType
        value
        rarity
      }
    }
    transfers {
      from
      to
      timestamp
      transactionHash
    }
  }
}
```

### Get Market Activity

```typescript
GET /v1/nfts/activity
```

Monitor marketplace activity:

#### Dune Analytics Implementation
```typescript
// Get market metrics
const activity = await client.query({
  queryId: "3682939",
  parameters: {
    marketplace: "opensea",
    timeframe: "7d"
  }
});

// Response includes:
// - Trading volume
// - Active users
// - Listings data
// - Price trends
```

### Get Rarity Rankings

```typescript
GET /v1/nfts/collections/{collection_id}/rarity
```

Access rarity scores and rankings:

#### Bitquery Implementation
```graphql
query {
  ethereum {
    nftTokens(
      collection: {is: "collection_address"}
      options: {desc: "rarity", limit: 100}
    ) {
      tokenId
      rarity
      attributes {
        type
        value
        frequency
        score
      }
      rank
      sales {
        price
        timestamp
      }
    }
  }
}
```

## Common Parameters

| Parameter | Type | Description | Default | Required |
|-----------|------|-------------|---------|----------|
| `collection_id` | string | Collection address | - | Yes |
| `token_id` | string | Token ID | - | No |
| `marketplace` | string | Marketplace name | all | No |
| `timeframe` | string | Data period | 24h | No |

## Response Format

```typescript
{
  status: 200,
  data: {
    nft: {
      collection: {
        id: string,
        name: string,
        metrics: {
          floor: number,
          volume: number,
          holders: number
        }
      },
      tokens: [{
        id: string,
        metadata: {
          name: string,
          image: string,
          attributes: [{
            type: string,
            value: string,
            rarity: number
          }]
        },
        market: {
          lastSale: number,
          highestBid: number,
          lowestAsk: number
        }
      }],
      activity: {
        trades: number,
        volume: number,
        users: number
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

Subscribe to real-time NFT updates:

```typescript
// Bitquery WebSocket
const ws = new WebSocket('wss://streaming.bitquery.io/graphql');

ws.send(JSON.stringify({
  type: 'start',
  id: 'nft_activity',
  payload: {
    query: `subscription {
      NFTActivity {
        Collection {
          Address
          FloorPrice
          Volume
        }
        Trades {
          TokenId
          Price
          Buyer
          Seller
        }
        Listings {
          TokenId
          Price
          Seller
        }
      }
    }`
  }
}));
```

## Best Practices

1. **Data Consistency**
   - Validate metadata
   - Cross-reference prices
   - Handle missing attributes

2. **Performance**
   - Cache collection data
   - Batch token requests
   - Stream market activity

3. **Market Analysis**
   - Track price trends
   - Monitor wash trading
   - Analyze rarity impact

4. **User Experience**
   - Handle image loading
   - Cache metadata
   - Implement search

## Example Implementation

```typescript
import { NFTScan, Reservoir, TheGraph } from '@blockchain/api';

class NFTDataAggregator {
  private providers: {
    nftscan: NFTScan;
    reservoir: Reservoir;
    thegraph: TheGraph;
  };

  constructor(config: Config) {
    this.providers = {
      nftscan: new NFTScan(config.nftscanKey),
      reservoir: new Reservoir(config.reservoirKey),
      thegraph: new TheGraph(config.graphKey)
    };
  }

  async getNFTData(collection: string) {
    const [stats, trades, metadata] = await Promise.all([
      this.getCollectionStats(collection),
      this.getTradeHistory(collection),
      this.getTokenMetadata(collection)
    ]);

    return {
      stats,
      trades,
      metadata
    };
  }

  async monitorMarket(collection: string, callback: (event: any) => void) {
    // Set up WebSocket monitoring
    const ws = new WebSocket('wss://streaming.bitquery.io/graphql');
    
    // Subscribe to market events
    ws.send(JSON.stringify({
      type: 'start',
      id: `market_${collection}`,
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