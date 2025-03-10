# Market Data Pipeline

This module provides a comprehensive market data collection pipeline for cryptocurrency exchanges. It collects various market metrics such as price, volume, funding rates, open interest, and more across multiple exchanges.

## Features

- Collects market data from multiple exchanges (currently supports Hyperliquid and Binance)
- Extensible architecture to easily add more exchanges
- Configurable update intervals
- Automatic data storage in Supabase
- Configurable asset filtering
- Comprehensive logging

## Market Metrics Collected

The pipeline collects the following metrics (when available):

- **Price**: Current trading price
- **Volume (24h)**: Trading volume over the last 24 hours
- **Open Interest**: Total open positions
- **Funding Rate**: Current funding rate for perpetual contracts
- **Mark Price**: Settlement price for derivatives
- **Index Price**: Reference price for the underlying asset
- **Bid/Ask Prices**: Current best bid and ask prices
- **Spread**: Difference between bid and ask prices
- **Liquidity**: Available liquidity in the order book
- **Volatility (24h)**: Price volatility over the last 24 hours
- **Price Change (24h)**: Percentage price change over the last 24 hours

## Setup

1. Ensure you have the necessary environment variables set:
   - `NEXT_PUBLIC_SUPABASE_URL`: Your Supabase project URL
   - `SUPABASE_SERVICE_ROLE_KEY` or `NEXT_PUBLIC_SUPABASE_ANON_KEY`: Your Supabase API key

2. Run the setup script to create the required database table:
   ```bash
   npx ts-node src/scripts/setup-market-metrics-table.ts
   ```

3. Install dependencies:
   ```bash
   npm install axios @supabase/supabase-js dotenv
   ```

## Usage

### Running the Pipeline

To start the market data pipeline:

```bash
npx ts-node src/scripts/run-market-pipeline.ts
```

### Configuration Options

When creating a new instance of `MarketDataPipeline`, you can provide the following options:

```typescript
const pipeline = new MarketDataPipeline({
    // Directory to store any local data (default: './data/market-data')
    storageDir: './custom-data-dir',
    
    // Maximum number of historical items to keep (default: 1000)
    historyLimit: 2000,
    
    // Update interval in milliseconds (default: 300000 - 5 minutes)
    updateInterval: 600000,
    
    // Log level: 'minimal', 'normal', or 'verbose' (default: 'normal')
    logLevel: 'verbose',
    
    // Exchanges to collect data from (default: ['hyperliquid', 'binance'])
    exchanges: ['hyperliquid', 'binance', 'bybit'],
    
    // Assets to collect data for - empty array means all assets (default: [])
    assets: ['BTC', 'ETH', 'SOL']
});
```

### Programmatic Usage

You can also use the pipeline programmatically in your own code:

```typescript
import { MarketDataPipeline } from './market-data-pipeline';

async function main() {
    const pipeline = new MarketDataPipeline({
        logLevel: 'verbose',
        updateInterval: 300000 // 5 minutes
    });
    
    // Start the pipeline
    await pipeline.start();
    
    // Later, stop the pipeline
    pipeline.stop();
}
```

## Database Schema

The pipeline stores data in a Supabase table called `market_metrics` with the following schema:

```sql
CREATE TABLE public.market_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMPTZ NOT NULL,
    asset TEXT NOT NULL,
    exchange TEXT NOT NULL,
    price NUMERIC NOT NULL,
    volume_24h NUMERIC NOT NULL,
    open_interest NUMERIC,
    funding_rate NUMERIC,
    mark_price NUMERIC,
    index_price NUMERIC,
    bid_price NUMERIC,
    ask_price NUMERIC,
    mid_price NUMERIC,
    spread NUMERIC,
    liquidity NUMERIC,
    volatility_24h NUMERIC,
    price_change_24h NUMERIC,
    created_at TIMESTAMPTZ NOT NULL,
    UNIQUE(timestamp, asset, exchange)
);
```

## Extending the Pipeline

### Adding a New Exchange

To add support for a new exchange, follow these steps:

1. Add the exchange name to the `supportedExchanges` array in the `MarketDataPipeline` class.

2. Create a new method to fetch data from the exchange:
   ```typescript
   private async fetchNewExchangeData(): Promise<MarketMetrics[]> {
       // Implementation here
   }
   ```

3. Add a case for the new exchange in the `runOnce` method:
   ```typescript
   switch (exchange) {
       // Existing cases...
       case 'newexchange':
           exchangeMetrics = await this.fetchNewExchangeData();
           break;
   }
   ```

## Troubleshooting

- **API Rate Limits**: If you encounter rate limit issues, consider increasing the `updateInterval` value.
- **Missing Data**: Some exchanges may not provide all metrics. The pipeline handles this gracefully by only storing available data.
- **Database Errors**: Ensure your Supabase credentials are correct and that the `market_metrics` table exists.

## License

This project is licensed under the MIT License. 