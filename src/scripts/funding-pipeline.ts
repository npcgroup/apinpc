import { HyperLiquidAPI } from './hyperliquid-api';
import { FundingStorage } from './funding-storage';
import path from 'path';

export interface PipelineOptions {
    storageDir?: string;
    historyLimit?: number;
    minimumFundingThreshold?: number;
    updateInterval?: number; // in milliseconds
    logLevel?: 'minimal' | 'normal' | 'verbose';
}

export class FundingPipeline {
    private api: HyperLiquidAPI;
    private storage: FundingStorage;
    protected options: PipelineOptions;
    private isRunning: boolean = false;
    private intervalId?: NodeJS.Timeout;

    constructor(options: PipelineOptions = {}) {
        this.options = {
            storageDir: path.join(process.cwd(), 'data', 'funding-history'),
            historyLimit: 1000,
            minimumFundingThreshold: 0.0001, // 0.01%
            updateInterval: 300000, // 5 minutes
            logLevel: 'normal',
            ...options
        };

        this.api = new HyperLiquidAPI();
        this.storage = new FundingStorage({
            directory: this.options.storageDir || path.join(process.cwd(), 'data', 'funding-history'),
            maxHistoryItems: this.options.historyLimit
        });
    }

    protected log(message: string, level: 'minimal' | 'normal' | 'verbose') {
        if (
            level === 'minimal' ||
            (level === 'normal' && this.options.logLevel !== 'minimal') ||
            (level === 'verbose' && this.options.logLevel === 'verbose')
        ) {
            console.log(`[${new Date().toISOString()}] ${message}`);
        }
    }

    async runOnce() {
        throw new Error('runOnce must be implemented by subclass');
    }

    async start() {
        if (this.isRunning) {
            this.log('Pipeline is already running', 'minimal');
            return;
        }

        this.isRunning = true;
        this.log('Starting funding pipeline...', 'minimal');

        await this.runOnce();
        this.intervalId = setInterval(() => this.runOnce(), this.options.updateInterval);
    }

    stop() {
        this.isRunning = false;
        this.log('Stopping pipeline...', 'minimal');

        if (this.intervalId) {
            clearInterval(this.intervalId);
        }
    }

    async getLatestAnalysis() {
        return this.storage.getLatestAnalysis();
    }
}

// Example usage
if (require.main === module) {
    const pipeline = new FundingPipeline({
        logLevel: 'normal',
        updateInterval: 60000, // 1 minute
        minimumFundingThreshold: 0.0001 // 0.01%
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
} 