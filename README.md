## Features

- Real-time funding data collection from multiple exchanges (Hyperliquid, Binance)
- Supabase integration for efficient data storage and retrieval
- Dynamic strategy parameter adjustment based on funding rates
- Comprehensive logging and monitoring
- Backtesting capabilities
- Error handling and retry mechanisms

## System Architecture

```mermaid
graph TD
    %% Core Data Sources
    subgraph DataSources["External Data Sources"]
        CCXT[CCXT Integration]
        HL[HyperLiquid API]
        DL[DefiLlama API]
        DU[Dune Analytics]
        FL[Flipside API]
        HE[Helius API]
        JU[Dune API]
    end

    %% Core Schema Structure
    subgraph CoreSchema["Core Database Schema"]
        direction TB
        FRS[("Metric Base
        metric_base.sql")]
        AS[("Assets
        assets.sql")]
        LPM[("LP Metrics
        lp_metrics.sql")]
        MES[("Market Stats
        market_stats.sql")]
        PEM[("Perpetual Metrics
        perpetuals_schema.sql")]
        DQM[("Data Quality Metrics
        blockchain_analytics.sql")]
        
    end

    %% Data Flow
    DataSources --> |Real-time Sync| CoreSchema
    
    %% Detailed Tables
    subgraph DetailedSchema["Detailed Schema Structure"]
        direction LR
        
        MetricBase["Metric Base
        (The foundational table that all metric-specific tables inherit from. Contains common fields for)"]
        
        Assets["Assets
        (Core asset tracking table)"]
        
        Lp_metrics["lP Metrics
        (Core asset tracking table)"]
        
        MarketStats["Market Statistics
        (Spot market and network stats on leading protocols)"]
        
        PerpMetrics["Perpetual Metrics
        (Relevant perp metrics for leading exchanges)"]
        
        QualityTracking["Quality Tracking
        (Trans. Edges)"]
    end

    %% Relationships and Indexes
    subgraph Optimization["Performance Optimization"]
    
        IDX["Index Optimization
        (Time-Series Optimized Indexes Partitioning Strategy)"]
    
        QP["Query Optimization
        (Materialized Views)"]
    
        BRIN["BRIN Indexes
        (Block Range Index)"]
        
        Constraints["Data Constraints
        (Validation Rules)"]
        
        DataQuality["Quality Checks
        (Memory Config)"]
        
        VS["Vacuum Strategy
        (Scale Factors Analysis Thresholds)"]
    end

    classDef core fill:#f9f,stroke:#333,stroke-width:2px
    class FRS,PEM,DQM,LPM,AS,MES core

    %% Data Processing Layer
    subgraph Processing["Processing Layer"]
        FRC[Metrics Collector]
        NRM[Data Normalizer]
        VAL[Validator]
    end

    %% Storage Layer
    subgraph Storage["PostgreSQL Schema"]
        direction TB
        MB[Metric Base]
        LP[LP Metrics]
        TM[Token Metrics]
        PM[Protocol Metrics]
        MS[Market Snapshots]
        ASS[Assets]
        PM[Perpetual Metrics]
        DQ[Data Quality]
        ST[Statistics]
    end

    %% Analytics Layer
    subgraph Analytics["Analytics Engine"]
        direction LR
        ARB[Arbitrage Detection]
        VOL[Volatility Analysis]
        PRED[Rate Prediction]
        CEF[Cross-Exchange Efficiency]
        LS[Liquidation Surface Analysis]
        FLW[Flow Toxicity Analysis]
    end

    %% Relationships
    DataSources --> Processing
    Processing --> Storage
    Storage --> Analytics

    %% Detailed Table Structure
    MS --> |Contains| TM
    MS --> |Contains| LP
    MS --> |Tracks| PM
    ST --> |Validates| DQ
    MS --> |Aggregates| ST
    MB --> |Contains| LP
    MB --> |Contains| PM
    MB --> |Tracks| ST
    MB --> |Tracks| ASS
    MS --> |Validates| MB
    ST --> |Aggregates| MB
    MB --> |Aggregates| MS

    %% Table Specifications
    classDef tableSpec fill:#f9f,stroke:#333,stroke-width:2px
    class MS,FR,PM,DQ,ST,MB,ASS,TM,LP tableSpec

    %% Table Details
    MS -.- MSDetails[["Market Snapshots
        - id: BIGSERIAL
        - timestamp: TIMESTAMPTZ
        - environment: environment
        - source_id: BIGINT
        - raw_data: JSONB"]]

    MB -.- MBDetails[["Metrics Base
        - id: BIGSERIAL
        - timestamp: TIMESTAMPTZ
        - environment: VARCHAR(20)
        - source_id: BIGINT
        - confidence_score: DECIMAL(5,2)
        - raw_data: JSONB"]]

    ASS -.- ATDetails[["Assets
        - id: BIGSERIAL
        - symbol: VARCHAR(20)
        - name: VARCHAR(100)
        - type: asset_type
        - chain: chain_name
        - protocol_id: BIGINT
        - contract_address: TEXT
        - metadata: JSONB"]]

    TM -.- TMDetails[["Token Metrics
        - asset_id: BIGINT
        - price: DECIMAL(24,8)
        - volume_24h: DECIMAL(24,8)
        - market_cap: DECIMAL(24,8)
        - total_supply: DECIMAL(24,8)
        - holder_count: INTEGER"]]

    PM -.- PMDetails[["Perpetual Metrics
        - asset_id: BIGINT
        - funding_rate: DECIMAL(18,8)
        - predicted_rate: DECIMAL(18,8)
        - open_interest: DECIMAL(24,8)
        - long_positions: DECIMAL(24,8)
        - short_positions: DECIMAL(24,8)
        - liquidations_24h: DECIMAL(24,8)
        - mark_price: DECIMAL(24,8)
        - index_price: DECIMAL(24,8)"]]

    LP -.- LMDetails[["LP Metrics
        - pool_address: VARCHAR(44)
        - token_a_id: BIGINT
        - token_b_id: BIGINT
        - Pair_name:VARCHAR(44))
        - tvl_usd: DECIMAL(24,8)
        - volume_24h: DECIMAL(24,8)
        - fee_apr: DECIMAL(10,4)
        - il_24h: DECIMAL(10,4)
        - reserves_a: DECIMAL(24,8)
        - reserves_b: DECIMAL(24,8)"]]

   ST -.- Insights[["Stats Insights
        - name: VARCHAR(44)
        - type: BIGINT
        - tvl_usd: BIGINT
        - volume_avg: DECIMAL(24,8)
        - volume_score: DECIMAL(24,8)
        - fee_apr: DECIMAL(10,4)
        - sentiment_score: DECIMAL(10,4)
        - risk_score: DECIMAL(24,8)
        - health_score: DECIMAL(24,8)"]]

    DQ -.- DQDetails[["Data Quality
        - id: BIGSERIAL
        - metric_table: VARCHAR(50)
        - metric_id: BIGINT
        - completeness_score: DECIMAL(5,2)
        - accuracy_score: DECIMAL(5,2)
        - timeliness_score: DECIMAL(5,2)
        - consistency_score: DECIMAL(5,2)
        - validation_errors: JSONB"]]

```

## Features

### Data Collection & Processing
- **Multi-Source Integration**
  - DeFi Llama: Protocol TVL and metrics
  - Dune Analytics: On-chain analytics
  - Bitquery: Cross-chain data
  - Hyperliquid: Perpetual markets
  - CCXT: OHLCV and Rate metrics
  - The Graph: Protocol-specific metrics
  - Footprint Analytics: NFT and GameFi data

- **Real-Time Processing**
  - WebSocket streaming for market data
  - Redis-based caching layer
  - Efficient data normalization pipeline

### Analytics & Insights
- **Market Analysis**
  - Funding rate arbitrage detection
  - Liquidity imbalance monitoring
  - Cross-exchange opportunities
  - Volume profile analysis

- **Data Quality**
  - Automated validation pipelines
  - Cross-source verification
  - Anomaly detection
  - Data completeness scoring

### Infrastructure
- **Storage & Database**
  - Supabase for structured data
  - Time-series optimized tables
  - Efficient indexing strategies
  - Version-controlled schemas

- **Performance**
  - High-throughput ingestion
  - Sub-second query response
  - Horizontal scalability
  - Automated failover

## 🚀 Quick Start

```mermaid

graph TD
    A[Test Ingestion] --> B1[Birdeye API]
    A --> B2[CCXT API]
    A --> B3[HyperLiquid API]
    B1 & B2 & B3 --> C[Combine Data]
    C --> D[Supabase DB]
    D --> E[Page Component]
    E --> F[Display Data]

```

```bash
# Install dependencies
yarn install

# Set up environment variables
cp .env.example .env

# Run development server
yarn dev

# Start data ingestion
yarn ingest

# Run tests
yarn test
```

## 📊 Data Models

### Core Metrics
```typescript
interface TokenMetrics {
  price: number;
  volume_24h: number;
  market_cap: number;
  holder_count: number;
  // ... more fields
}

interface PerpetualMetrics {
  funding_rate: number;
  open_interest: number;
  volume_24h: number;
  long_positions: number;
  // ... more fields
}
```

## 🔧 Configuration

### Environment Variables
```env
# API Keys
DEFILLAMA_API_KEY=your_key
DUNE_API_KEY=your_key
BITQUERY_API_KEY=your_key

# Database
SUPABASE_URL=your_url
SUPABASE_KEY=your_key

# Cache
REDIS_URL=your_url
```

## 📈 Usage Examples

### Token Analytics
```typescript
import { BlockchainAnalyticsService } from 'blockchain-analytics';

const analytics = new BlockchainAnalyticsService({
  supabaseUrl: process.env.SUPABASE_URL,
  supabaseKey: process.env.SUPABASE_KEY
});

// Fetch token metrics
const metrics = await analytics.ingestTokenMetrics({
  symbol: 'ETH',
  chain: 'ethereum'
});
```

### Real-Time Data Streaming
```typescript
import { WebSocketService } from 'blockchain-analytics';

const ws = new WebSocketService(cache);

ws.on('data', ({ provider, data }) => {
  console.log(`New data from ${provider}:`, data);
});

await ws.connect(DataProvider.HYPERLIQUID);
```

## 🏗️ Architecture

### Data Flow
1. Multi-source data ingestion
2. Real-time processing & validation
3. Quality scoring & normalization
4. Storage & indexing
5. API exposure & streaming

### Components
- Data Ingestion Services
- WebSocket Streaming
- Redis Cache Layer
- Supabase Database
- Analytics Engine
- API Layer

## 🧪 Testing

```bash
# Run unit tests
yarn test

# Run integration tests
yarn test:integration

# Test data ingestion
yarn test-ingest
```
<!--
## 📚 Documentation

- [API Reference](./docs/API.md)
- [Schema Documentation](./docs/SCHEMA.md)
- [Development Guide](./docs/DEVELOPMENT.md)
- [Deployment Guide](./docs/DEPLOYMENT.md)
-->
## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Run tests and linting
4. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) for details

<!--
## 🔗 Related Projects

- [Trading Strategies](https://github.com/yourusername/trading-strategies)
- [Market Making Bot](https://github.com/yourusername/market-maker)
- [Analytics Dashboard](https://github.com/yourusername/analytics-dashboard)
-->

## 📊 Performance Metrics

- Data freshness: < 1 second
- Query response time: < 100ms
- Data accuracy: > 99.9%
- System uptime: > 99.99%

## 🌟 Roadmap

- [ ] Machine Learning Models
- [ ] Advanced Analytics Dashboard
- [ ] Cross-Chain Arbitrage
- [ ] Automated Trading Strategies

# Funding Rate Analysis App

## Setup
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Create `.env` file with required variables:
   ```
   NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
   NEXT_PUBLIC_SUPABASE_KEY=your_supabase_key
   ```
4. Run the app: `streamlit run scripts/funding_streamlit_app.py`

## Deployment
- Follow platform-specific deployment instructions
- Ensure environment variables are set
- Use the Procfile for Heroku-like platforms
