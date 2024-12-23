export const API_EXAMPLES = {
  defillama: {
    protocols: {
      title: 'Get All Protocols',
      code: 'curl https://api.llama.fi/protocols',
      language: 'bash',
      response: `[
  {
    "id": "1",
    "name": "Uniswap",
    "address": "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984",
    "symbol": "UNI",
    "url": "https://uniswap.org",
    "description": "Decentralized protocol for automated token exchange",
    "chain": "Ethereum",
    "logo": "https://assets.coingecko.com/coins/images/12504/large/uniswap-uni.png",
    "tvl": 5240560789.34,
    "change_1h": 0.12,
    "change_24h": -2.34,
    "change_7d": 5.67
  }
]`
    },
    tvl: {
      title: 'Get Protocol TVL History',
      code: 'curl https://api.llama.fi/protocol/uniswap',
      language: 'bash',
      response: `{
  "tvl": [
    {
      "date": "2023-01-01",
      "totalLiquidityUSD": 3245678901.23
    }
  ],
  "tokensInUsd": {
    "ethereum": 2345678901.23,
    "polygon": 900000000.00
  }
}`
    },
    stablecoins: {
      title: 'Get Stablecoin Data',
      code: 'curl https://api.llama.fi/stablecoins',
      language: 'bash',
      response: `[
  {
    "id": "1",
    "name": "USDT",
    "symbol": "USDT",
    "circulating": 83147480916,
    "price": 1.001,
    "chains": ["Ethereum", "BSC", "Polygon"]
  }
]`
    },
    dexs: {
      title: 'Get DEX Volume Data',
      code: 'curl https://api.llama.fi/overview/dexs',
      language: 'bash',
      response: `{
  "totalVolume24h": 12345678901.23,
  "protocols": [
    {
      "name": "Uniswap",
      "volume24h": 2345678901.23,
      "chains": ["Ethereum", "Polygon"]
    }
  ]
}`
    },
    yields: {
      title: 'Get Yield Pool Data',
      code: 'curl https://api.llama.fi/pools',
      language: 'bash',
      response: `[
  {
    "pool": "Aave USDC",
    "chain": "Ethereum",
    "project": "Aave",
    "symbol": "USDC",
    "tvlUsd": 1234567890.12,
    "apy": 4.52
  }
]`
    }
  },
  dune: {
    query: {
      title: 'Execute Custom Query',
      code: `curl -X POST https://api.dune.com/api/v1/query/execute \\
-H "x-dune-api-key: YOUR_API_KEY" \\
-d '{
  "query_id": "1234567",
  "params": {
    "network": "ethereum",
    "from_date": "2024-01-01",
    "to_date": "2024-03-14"
  }
}'`,
      language: 'bash',
      response: `{
  "execution_id": "01H...",
  "state": "QUERY_STATE_EXECUTING"
}`
    },
    nftSales: {
      title: 'Get Top NFT Sales',
      code: `SELECT 
  nft_sales.block_time,
  nft_sales.token_id,
  nft_sales.collection,
  nft_sales.amount_usd as sale_amount,
  nft_sales.buyer,
  nft_sales.seller
FROM ethereum.nft_sales
WHERE block_time >= NOW() - INTERVAL '24 hours'
ORDER BY amount_usd DESC
LIMIT 10;`,
      language: 'sql'
    },
    defi: {
      title: 'Get DeFi Protocol Metrics',
      code: `SELECT 
  protocol_name,
  SUM(tvl_usd) as total_tvl,
  COUNT(DISTINCT user_address) as unique_users,
  SUM(volume_usd) as total_volume
FROM dune.defi.protocol_metrics
WHERE block_date >= CURRENT_DATE - 30
GROUP BY protocol_name
ORDER BY total_tvl DESC
LIMIT 10;`,
      language: 'sql'
    },
    eigenlayer: {
      title: 'Query EigenLayer Operators',
      code: `SELECT
  operator_address,
  SUM(staked_amount) as total_staked,
  COUNT(DISTINCT delegator) as delegator_count,
  AVG(commission_rate) as avg_commission
FROM eigenlayer.operator_metrics
GROUP BY operator_address
HAVING total_staked > 100
ORDER BY total_staked DESC;`,
      language: 'sql'
    }
  },
  flipside: {
    query: {
      title: 'Execute Flipside Query',
      code: `curl -X POST https://api.flipsidecrypto.com/api/v2/queries \\
-H "x-api-key: YOUR_API_KEY" \\
-d '{
  "sql": "SELECT * FROM ethereum.core.fact_transactions LIMIT 10",
  "ttlMinutes": 15
}'`,
      language: 'bash',
      response: `{
  "queryId": "123-456-789",
  "status": "running",
  "results": null
}`
    },
    eth: {
      title: 'Get ETH Transfers',
      code: `SELECT 
  block_timestamp,
  from_address,
  to_address,
  amount_usd,
  tx_hash
FROM ethereum.core.fact_token_transfers
WHERE token_address = '0x0000000000000000000000000000000000000000'
  AND block_timestamp >= CURRENT_DATE - 1
ORDER BY amount_usd DESC
LIMIT 100;`,
      language: 'sql'
    },
    defi_metrics: {
      title: 'Get DeFi Protocol Metrics',
      code: `SELECT 
  DATE_TRUNC('day', block_timestamp) as date,
  protocol_name,
  SUM(amount_usd) as tvl,
  COUNT(DISTINCT user_address) as users,
  SUM(CASE WHEN action = 'swap' THEN amount_usd ELSE 0 END) as swap_volume
FROM flipside_prod_db.defi.core_metrics
WHERE block_timestamp >= CURRENT_DATE - 7
GROUP BY 1, 2
ORDER BY 1 DESC, 3 DESC;`,
      language: 'sql'
    },
    nft_marketplace: {
      title: 'NFT Marketplace Analysis',
      code: `SELECT 
  marketplace_name,
  COUNT(*) as total_sales,
  SUM(price_usd) as volume_usd,
  AVG(price_usd) as avg_price,
  COUNT(DISTINCT buyer_address) as unique_buyers
FROM flipside_prod_db.ethereum.nft_sales
WHERE block_timestamp >= CURRENT_DATE - 30
GROUP BY marketplace_name
ORDER BY volume_usd DESC;`,
      language: 'sql'
    }
  },
  subgraph: {
    uniswap: {
      title: 'Query Uniswap V3 Pools',
      code: `{
  pools(
    first: 5
    orderBy: totalValueLockedUSD
    orderDirection: desc
  ) {
    id
    token0 {
      symbol
      decimals
    }
    token1 {
      symbol
      decimals
    }
    totalValueLockedUSD
    volumeUSD
  }
}`,
      language: 'graphql',
      response: `{
  "data": {
    "pools": [
      {
        "id": "0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8",
        "token0": {
          "symbol": "USDC",
          "decimals": "6"
        },
        "token1": {
          "symbol": "ETH",
          "decimals": "18"
        },
        "totalValueLockedUSD": "123456789.12",
        "volumeUSD": "987654321.98"
      }
    ]
  }
}`
    },
    aave: {
      title: 'Query Aave V3 Markets',
      code: `{
  markets(
    first: 10
    orderBy: totalValueLockedUSD
    orderDirection: desc
  ) {
    id
    name
    inputToken {
      id
      symbol
      decimals
    }
    totalValueLockedUSD
    totalBorrowed
    depositAPY
    borrowAPY
  }
}`,
      language: 'graphql'
    },
    curve: {
      title: 'Query Curve Pools',
      code: `{
  pools(
    where: { 
      totalValueLockedUSD_gt: "1000000" 
    }
  ) {
    id
    name
    coins
    baseAPY
    volume24h
    totalValueLockedUSD
    gaugeAddress
  }
}`,
      language: 'graphql'
    }
  }
};

export const DOCUMENTATION_SECTIONS = {
  gettingStarted: {
    title: 'Getting Started',
    content: `# Getting Started with Blockchain Data APIs

This guide will help you get started with accessing blockchain data through our unified API interface.

## Prerequisites
- API keys for the services you want to use
- Basic understanding of REST APIs and GraphQL
- Familiarity with blockchain concepts

## Quick Start
1. Get your API keys
2. Choose your data source
3. Make your first query
4. Process and analyze the data`
  },
  authentication: {
    title: 'Authentication',
    content: `# Authentication

Each data provider requires its own authentication method:

## Dune Analytics
- Requires API key in header: \`x-dune-api-key\`
- Rate limits apply based on plan

## Flipside Crypto
- Requires API key in header: \`x-api-key\`
- Different rate limits per tier

## The Graph
- Optional authentication for higher rate limits
- Uses Bearer token authentication`
  },
  flipsideGuides: {
    title: 'Flipside Query Guide',
    content: `# Flipside Crypto Query Guide

## Available Datasets
- ethereum.core.fact_transactions
- ethereum.core.fact_token_transfers
- ethereum.core.dim_labels
- ethereum.defi.fact_events

## Query Best Practices
1. Use appropriate time ranges
2. Include WHERE clauses for performance
3. Leverage common table expressions (CTEs)
4. Use appropriate aggregations

## Example Workflow
1. Start with basic metrics
2. Add dimensions and filters
3. Create complex aggregations
4. Optimize performance`
  },
  duneAnalytics: {
    title: 'Dune Analytics Guide',
    content: `# Dune Analytics Documentation

## Query Engine
- PostgreSQL compatible
- Supports window functions
- Custom blockchain-specific functions

## Available Datasets
- ethereum.transactions
- ethereum.traces
- ethereum.logs
- dune.defi.*
- dune.nft.*

## Best Practices
1. Use appropriate indexes
2. Leverage materialized views
3. Optimize join operations
4. Use appropriate data types`
  },
  subgraphDevelopment: {
    title: 'Subgraph Development',
    content: `# The Graph Protocol Development Guide

## Creating Subgraphs
1. Define schema
2. Write mappings
3. Deploy subgraph
4. Query data

## Best Practices
- Efficient entity relationships
- Proper indexing strategies
- Optimized query patterns
- Event handling`
  }
};

export const API_REFERENCE = {
  defillama: {
    baseUrl: 'https://api.llama.fi',
    description: 'Real-time DeFi TVL and analytics data',
    authentication: 'No authentication required',
    rateLimits: '30 requests per minute',
    endpoints: [
      {
        path: '/protocols',
        method: 'GET',
        description: 'Get all protocols with TVL data',
        parameters: [],
        response: {
          type: 'array',
          items: {
            id: 'string',
            name: 'string',
            tvl: 'number',
            chains: 'string[]'
          }
        }
      },
      {
        path: '/protocol/{name}',
        method: 'GET',
        description: 'Get detailed protocol information',
        parameters: [
          {
            name: 'name',
            type: 'string',
            required: true,
            description: 'Protocol name or slug'
          }
        ]
      },
      {
        path: '/stablecoins',
        method: 'GET',
        description: 'Get stablecoin circulating amounts and prices',
        parameters: [],
        response: {
          type: 'array',
          items: {
            name: 'string',
            symbol: 'string',
            circulating: 'number',
            price: 'number'
          }
        }
      },
      {
        path: '/yields',
        method: 'GET',
        description: 'Get yield pool APYs and TVL',
        parameters: [
          {
            name: 'project',
            type: 'string',
            required: false,
            description: 'Filter by project name'
          }
        ]
      }
    ]
  },
  dune: {
    baseUrl: 'https://api.dune.com/api/v1',
    description: 'SQL-based blockchain analytics platform',
    authentication: 'API key required in x-dune-api-key header',
    rateLimits: {
      free: '10 queries per day',
      standard: '100 queries per day',
      enterprise: 'Custom limits'
    },
    endpoints: [
      {
        path: '/query/execute',
        method: 'POST',
        description: 'Execute a SQL query',
        parameters: [
          {
            name: 'query_id',
            type: 'string',
            required: true,
            description: 'Dune query ID'
          },
          {
            name: 'params',
            type: 'object',
            required: false,
            description: 'Query parameters'
          }
        ]
      },
      {
        path: '/query/{query_id}/results',
        method: 'GET',
        description: 'Get query results',
        parameters: [
          {
            name: 'query_id',
            type: 'string',
            required: true,
            description: 'Query ID to fetch results for'
          }
        ]
      }
    ],
    tables: {
      ethereum: [
        'ethereum.transactions',
        'ethereum.traces',
        'ethereum.logs',
        'ethereum.nft_trades',
        'ethereum.token_transfers'
      ],
      defi: [
        'dune.defi.protocol_metrics',
        'dune.defi.lending_deposits',
        'dune.defi.dex_trades'
      ],
      nft: [
        'dune.nft.trades',
        'dune.nft.mints',
        'dune.nft.transfers'
      ]
    }
  },
  flipside: {
    baseUrl: 'https://api.flipsidecrypto.com/api/v2',
    description: 'Comprehensive blockchain data analytics',
    authentication: 'API key required in x-api-key header',
    rateLimits: {
      free: '100 queries per day',
      pro: '1000 queries per day'
    },
    endpoints: [
      {
        path: '/queries',
        method: 'POST',
        description: 'Execute SQL query',
        parameters: [
          {
            name: 'sql',
            type: 'string',
            required: true,
            description: 'SQL query to execute'
          },
          {
            name: 'ttlMinutes',
            type: 'number',
            required: false,
            description: 'Cache duration in minutes'
          }
        ]
      },
      {
        path: '/queries/{query_id}/results',
        method: 'GET',
        description: 'Get query results',
        parameters: [
          {
            name: 'query_id',
            type: 'string',
            required: true,
            description: 'Query ID to fetch results for'
          }
        ]
      }
    ],
    schemas: {
      ethereum: {
        core: [
          'ethereum.core.fact_transactions',
          'ethereum.core.fact_token_transfers',
          'ethereum.core.dim_labels'
        ],
        defi: [
          'ethereum.defi.fact_events',
          'ethereum.defi.lending_borrows',
          'ethereum.defi.dex_swaps'
        ],
        nft: [
          'ethereum.nft.fact_nft_sales',
          'ethereum.nft.fact_nft_mints'
        ]
      }
    }
  },
  subgraphs: {
    baseUrl: 'https://api.thegraph.com/subgraphs/name',
    description: 'GraphQL APIs for blockchain data',
    authentication: 'Optional Bearer token for higher rate limits',
    rateLimits: {
      free: '1000 queries per day',
      authenticated: '10000 queries per day'
    },
    endpoints: [
      {
        path: '/{subgraph_name}',
        method: 'POST',
        description: 'Query subgraph data',
        parameters: [
          {
            name: 'query',
            type: 'string',
            required: true,
            description: 'GraphQL query'
          }
        ]
      }
    ],
    popularSubgraphs: [
      {
        name: 'uniswap-v3',
        description: 'Uniswap V3 protocol data',
        entities: ['pools', 'tokens', 'positions', 'swaps']
      },
      {
        name: 'aave-v3',
        description: 'Aave V3 lending protocol data',
        entities: ['markets', 'reserves', 'users', 'borrows']
      }
    ]
  }
}; 