# Integration Guide

This comprehensive guide covers integration patterns across multiple blockchain data platforms and APIs.

## Overview

This documentation consolidates integration patterns from:

- DefiLlama Adapters
- Dune Analytics 
- Bitquery Streaming Platform
- Footprint Analytics
- The Graph Subgraphs
- GraphQL IDE

## Core Integration Patterns

### 1. Direct API Access

```typescript
// REST API example
const response = await fetch('https://api.llama.fi/protocol/aave', {
  headers: {
    'Authorization': `Bearer ${API_KEY}`
  }
});

// GraphQL example 
const query = `{
  protocols {
    name
    tvl
  }
}`;

const response = await request(GRAPHQL_ENDPOINT, query);
```

### 2. SDK Integration

```typescript
import { DuneClient } from '@duneanalytics/client';
import { BitqueryClient } from '@bitquery/client';

// Initialize clients
const duneClient = new DuneClient(DUNE_API_KEY);
const bitqueryClient = new BitqueryClient(BITQUERY_API_KEY);

// Execute queries
const duneResult = await duneClient.query(QUERY_ID);
const bitqueryResult = await bitqueryClient.query(GRAPHQL_QUERY);
```

### 3. Subgraph Deployment

```yaml
specVersion: 0.0.4
schema:
  file: ./schema.graphql
dataSources:
  - kind: ethereum/contract
    name: Protocol
    network: mainnet
    source:
      address: "0x..."
      abi: Protocol
    mapping:
      kind: ethereum/events
      apiVersion: 0.0.6
      language: wasm/assemblyscript
      entities:
        - Protocol
      abis:
        - name: Protocol
          file: ./abis/Protocol.json
      eventHandlers:
        - event: NewProtocol(address,string)
          handler: handleNewProtocol
```

## Authentication Methods

Each platform has its own authentication approach:

- **DefiLlama**: Public endpoints + API key for higher rate limits
- **Dune**: OAuth2 token-based auth
- **Bitquery**: API key in headers
- **Footprint**: API key + JWT tokens
- **The Graph**: Public endpoints + API keys for hosted service

## Best Practices

### Rate Limiting

```typescript
class RateLimiter {
  private queue: Array<() => Promise<any>> = [];
  private processing = false;
  
  async add<T>(fn: () => Promise<T>): Promise<T> {
    return new Promise((resolve, reject) => {
      this.queue.push(async () => {
        try {
          const result = await fn();
          resolve(result);
        } catch (error) {
          reject(error); 
        }
      });
      
      if (!this.processing) this.process();
    });
  }

  private async process() {
    // Rate limiting implementation
  }
}
```

### Caching

```typescript
const cache = new Map();
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

async function getCachedData(key: string) {
  const cached = cache.get(key);
  if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
    return cached.data;
  }
  const data = await fetchFreshData(key);
  cache.set(key, { data, timestamp: Date.now() });
  return data;
}
```

### Error Handling

```typescript
async function fetchWithRetry(url: string, options: any, retries = 3) {
  try {
    const response = await fetch(url, options);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    if (retries > 0) {
      await sleep(Math.pow(2, 4-retries) * 1000);
      return fetchWithRetry(url, options, retries - 1);
    }
    throw error;
  }
}
```

## Platform-Specific Guides

- [DefiLlama Integration Guide](../defillama/README.md)
- [Dune Analytics Guide](../dune/README.md) 
- [Bitquery Streaming Guide](../bitquery/README.md)
- [Footprint Analytics Guide](../footprint/README.md)
- [The Graph Development Guide](../thegraph/README.md)

## Support & Resources

- [Discord Communities](../support/discord.md)
- [GitHub Repositories](../support/github.md)
- [Documentation Updates](../support/docs.md)

## Contributing

We welcome contributions! Please see our [contribution guidelines](../contributing.md) for:

- Code style and standards
- Testing requirements 
- Documentation format
- Review process 