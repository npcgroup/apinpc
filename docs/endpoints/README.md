# API Endpoints

## Overview

Our API endpoints are organized into logical categories to provide structured access to blockchain data. Each category contains endpoints from multiple providers that can be used to access similar data types.

## Categories

### 1. Protocol Data (`/v1/protocols`)

Access protocol-level metrics and analytics:

```typescript
// Get protocol TVL
GET /v1/protocols/{protocol_id}/tvl

// Get protocol statistics
GET /v1/protocols/{protocol_id}/stats

// Get protocol revenue
GET /v1/protocols/{protocol_id}/revenue

// Get protocol users
GET /v1/protocols/{protocol_id}/users

// Get protocol transactions
GET /v1/protocols/{protocol_id}/transactions
```

### 2. Token Data (`/v1/tokens`)

Comprehensive token metrics and market data:

```typescript
// Get token prices
GET /v1/tokens/prices?symbols=ETH,BTC

// Get token holders
GET /v1/tokens/{token_address}/holders

// Get token transfers
GET /v1/tokens/{token_address}/transfers

// Get token metadata
GET /v1/tokens/{token_address}/metadata

// Get token historical prices
GET /v1/tokens/{token_address}/history
```

### 3. DEX Data (`/v1/dex`)

Decentralized exchange analytics and trading data:

```typescript
// Get pair data
GET /v1/dex/pairs/{chain}

// Get OHLCV data
GET /v1/dex/ohlc/{token}/{chain}

// Get liquidity pools
GET /v1/dex/pools/{protocol}

// Get DEX trades
GET /v1/dex/trades/{pair}

// Get DEX volume
GET /v1/dex/volume/{protocol}
```

### 4. Chain Metrics (`/v1/metrics`)

Network-level statistics and analytics:

```typescript
// Get chain metrics
GET /v1/metrics/{chain}/stats

// Get gas analytics
GET /v1/metrics/{chain}/gas

// Get validator data
GET /v1/metrics/{chain}/validators

// Get block data
GET /v1/metrics/{chain}/blocks

// Get network health
GET /v1/metrics/{chain}/health
```

### 5. NFT Data (`/v1/nfts`)

NFT market data and analytics:

```typescript
// Get collection stats
GET /v1/nfts/collections/{collection_id}/stats

// Get NFT trades
GET /v1/nfts/trades

// Get NFT metadata
GET /v1/nfts/{token_id}/metadata

// Get NFT holders
GET /v1/nfts/{collection_id}/holders

// Get floor prices
GET /v1/nfts/collections/{collection_id}/floor
```

### 6. DeFi Lending (`/v1/lending`)

DeFi lending pool and rate data:

```typescript
// Get lending pools
GET /v1/lending/pools/{protocol}

// Get borrowing rates
GET /v1/lending/rates/{token}

// Get collateral data
GET /v1/lending/collateral/{protocol}

// Get liquidation data
GET /v1/lending/liquidations

// Get lending positions
GET /v1/lending/positions/{address}
```

### 7. Derivatives (`/v1/derivatives`)

Derivative market data and analytics:

```typescript
// Get futures data
GET /v1/derivatives/futures/{market}

// Get options data
GET /v1/derivatives/options/{underlying}

// Get open interest
GET /v1/derivatives/open-interest/{market}

// Get funding rates
GET /v1/derivatives/funding-rates/{market}

// Get liquidations
GET /v1/derivatives/liquidations
```

### 8. Governance (`/v1/governance`)

Governance data and analytics:

```typescript
// Get proposals
GET /v1/governance/{protocol}/proposals

// Get votes
GET /v1/governance/{protocol}/votes

// Get delegate info
GET /v1/governance/{protocol}/delegates

// Get voting power
GET /v1/governance/{protocol}/power/{address}

// Get execution status
GET /v1/governance/{protocol}/execution/{proposal_id}
```

### 9. Cross-Chain (`/v1/bridges`)

Cross-chain bridge data and analytics:

```typescript
// Get bridge transfers
GET /v1/bridges/transfers

// Get bridge TVL
GET /v1/bridges/tvl

// Get bridge stats
GET /v1/bridges/{bridge_id}/stats

// Get bridge tokens
GET /v1/bridges/{bridge_id}/tokens

// Get bridge security
GET /v1/bridges/{bridge_id}/security
```

### 10. Analytics (`/v1/analytics`)

Market sentiment, correlation, risk, and trend data:

```typescript
// Get market sentiment
GET /v1/analytics/sentiment

// Get correlation data
GET /v1/analytics/correlation

// Get risk metrics
GET /v1/analytics/risk/{token}

// Get market trends
GET /v1/analytics/trends

// Get whale activity
GET /v1/analytics/whales
```

Each category includes detailed documentation on:
- Request parameters
- Response formats
- Rate limits
- Example responses
- Error codes
- WebSocket support

See individual category documentation for complete details:
- [Protocol Data Documentation](./protocols/README.md)
- [Token Data Documentation](./tokens/README.md)
- [DEX Data Documentation](./dex/README.md)
- [Chain Metrics Documentation](./metrics/README.md)
- [NFT Data Documentation](./nfts/README.md)
- [DeFi Lending Documentation](./lending/README.md)
- [Derivatives Documentation](./derivatives/README.md)
- [Governance Documentation](./governance/README.md)
- [Cross-Chain Documentation](./bridges/README.md)
- [Analytics Documentation](./analytics/README.md)

## Common Parameters

All endpoints support these standard parameters:

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `network` | string | Blockchain network identifier | `ethereum`, `bsc` |
| `from` | timestamp | Start time for time-series data | `1677649200` |
| `to` | timestamp | End time for time-series data | `1677735600` |
| `limit` | integer | Number of results to return | `100` |
| `offset` | integer | Pagination offset | `0` |
| `format` | string | Response format | `json`, `csv` |

## Response Format

All endpoints return data in a consistent format:

```typescript
{
  status: 200,
  data: {
    // Response data
  },
  metadata: {
    timestamp: 1677735600,
    latency: 120,
    cache: "hit"|"miss"
  }
}
```

## Rate Limits

| Plan | Requests/Min | Burst | Websocket Connections |
|------|-------------|-------|----------------------|
| Free | 60 | 100 | 1 |
| Pro | 300 | 500 | 5 |
| Enterprise | Custom | Custom | Custom |

## Best Practices

1. **Caching**
   - Cache frequently accessed data
   - Respect cache-control headers
   - Implement stale-while-revalidate

2. **Rate Limiting**
   - Implement exponential backoff
   - Use bulk endpoints where available
   - Monitor rate limit headers

3. **Error Handling**
   - Handle HTTP status codes
   - Implement retry logic
   - Log detailed errors

4. **Performance**
   - Use compression
   - Batch requests when possible
   - Filter responses server-side

## WebSocket Support

Most endpoints also support real-time updates via WebSocket:

```typescript
// Connect to WebSocket
const ws = new WebSocket('wss://api.example.com/v1/ws');

// Subscribe to updates
ws.send(JSON.stringify({
  type: 'subscribe',
  channel: 'dex.trades',
  params: {
    pair: 'ETH/USDC',
    protocol: 'uniswap-v3'
  }
}));
```

## SDK Support

All endpoints are accessible through our official SDKs:

```typescript
// JavaScript/TypeScript
import { BlockchainAPI } from '@blockchain/api';

// Initialize client
const client = new BlockchainAPI({
  apiKey: 'your_api_key'
});

// Make requests
const tvl = await client.protocols.getTVL('aave');
```

## Need Help?

- Check our [API Reference](../api-reference/README.md)
- Join our [Discord](https://discord.gg/blockchain-api)
- Submit issues on [GitHub](https://github.com/blockchain-api/issues)