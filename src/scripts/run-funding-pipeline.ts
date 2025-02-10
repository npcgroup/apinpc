import { SupabaseFundingPipeline } from './funding-pipeline-supabase';

const pipeline = new SupabaseFundingPipeline({
    logLevel: 'verbose',
    updateInterval: 210000  // 3.5 minutes
});

// Handle graceful shutdown
process.on('SIGINT', () => {
    console.log('\nReceived SIGINT. Shutting down gracefully...');
    pipeline.stop();
});

process.on('SIGTERM', () => {
    console.log('\nReceived SIGTERM. Shutting down gracefully...');
    pipeline.stop();
});

// Start the pipeline
pipeline.start().catch(error => {
    console.error('Fatal pipeline error:', error);
    process.exit(1);
}); 