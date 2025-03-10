import { MarketDataPipeline } from './market-data-pipeline';
import { setupMarketMetricsTable } from './setup-market-metrics-table';

async function main() {
    try {
        // First, ensure the table exists
        await setupMarketMetricsTable();
        
        // Create and start the pipeline
        const pipeline = new MarketDataPipeline({
            logLevel: 'verbose',
            updateInterval: 300000, // 5 minutes
            exchanges: ['hyperliquid', 'binance'],
            assets: [] // Empty array means all assets
        });
        
        // Handle graceful shutdown
        process.on('SIGINT', () => {
            console.log('\nReceived SIGINT. Shutting down gracefully...');
            pipeline.stop();
            process.exit(0);
        });
        
        process.on('SIGTERM', () => {
            console.log('\nReceived SIGTERM. Shutting down gracefully...');
            pipeline.stop();
            process.exit(0);
        });
        
        // Start the pipeline
        await pipeline.start();
        console.log('Market data pipeline is running. Press Ctrl+C to stop.');
    } catch (error) {
        console.error('Failed to start market data pipeline:', error);
        process.exit(1);
    }
}

// Run the main function
if (require.main === module) {
    main().catch(error => {
        console.error('Unhandled error:', error);
        process.exit(1);
    });
} 