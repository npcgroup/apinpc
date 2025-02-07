import { HyperLiquidAPI } from './hyperliquid-api';
import { FundingStorage } from './funding-storage';
import path from 'path';

interface PipelineOptions {
    storageDir?: string;
    historyLimit?: number;
    minimumFundingThreshold?: number;
    updateInterval?: number; // in milliseconds
    logLevel?: 'minimal' | 'normal' | 'verbose';
}

class FundingPipeline {
    private api: HyperLiquidAPI;
    private storage: FundingStorage;
    private options: Required<PipelineOptions>;
    private isRunning: boolean = false;

    constructor(options: PipelineOptions = {}) {
        this.options = {
            storageDir: path.join(process.cwd(), 'data', 'funding-history'),
            historyLimit: 1000,
            minimumFundingThreshold: 0.0001, // 0.01%
            updateInterval: 60000, // 1 minute
            logLevel: 'normal',
            ...options
        };

        this.api = new HyperLiquidAPI();
        this.storage = new FundingStorage({
            directory: this.options.storageDir,
            maxHistoryItems: this.options.historyLimit
        });
    }

    protected log(message: string, level: 'minimal' | 'normal' | 'verbose' = 'normal') {
        const levels = {
            minimal: 1,
            normal: 2,
            verbose: 3
        };

        if (levels[level] <= levels[this.options.logLevel]) {
            const timestamp = new Date().toISOString();
            console.log(`[${timestamp}] ${message}`);
        }
    }

    async runOnce() {
        try {
            // 1. Fetch latest data
            this.log('Fetching latest funding rates...', 'normal');
            const rates = await this.api.getPredictedFundingRates();

            // 2. Analyze the data
            this.log('Analyzing funding rates...', 'verbose');
            const analysis = this.api.analyzeFundingRates(rates);

            // 3. Store the results
            this.log('Storing analysis results...', 'verbose');
            await this.storage.saveAnalysis(analysis);

            // 4. Display significant opportunities
            const significantOpps = analysis.topOpportunities.filter(
                opp => Math.abs(opp.predicted) >= this.options.minimumFundingThreshold
            );

            if (significantOpps.length > 0) {
                this.log('\nSignificant Funding Opportunities:', 'minimal');
                this.log('----------------------------------------', 'minimal');
                significantOpps.forEach((rate, index) => {
                    this.log(`${index + 1}. ${this.api.formatFundingRate(rate)}`, 'minimal');
                });
            }

            // 5. Display statistics
            const stats = analysis.statistics;
            this.log('\nMarket Overview:', 'normal');
            this.log('----------------------------------------', 'normal');
            this.log(`Active pairs: ${stats.pairsWithFunding}/${stats.totalPairs}`, 'normal');
            this.log(`Average funding rate: ${(stats.averageRate * 100).toFixed(6)}%`, 'normal');
            this.log(`Positive/Negative split: ${stats.positiveRates}/${stats.negativeRates}`, 'normal');

            return analysis;

        } catch (error) {
            this.log(`Error in pipeline: ${error instanceof Error ? error.message : String(error)}`, 'minimal');
            throw error;
        }
    }

    async start() {
        if (this.isRunning) {
            this.log('Pipeline is already running', 'minimal');
            return;
        }

        this.isRunning = true;
        this.log('Starting funding pipeline...', 'minimal');

        while (this.isRunning) {
            try {
                await this.runOnce();
                this.log(`Next update in ${this.options.updateInterval / 1000} seconds...`, 'verbose');
                await new Promise(resolve => setTimeout(resolve, this.options.updateInterval));
            } catch (error) {
                this.log(`Pipeline error: ${error instanceof Error ? error.message : String(error)}`, 'minimal');
                await new Promise(resolve => setTimeout(resolve, 5000)); // Wait 5s before retrying
            }
        }
    }

    stop() {
        this.isRunning = false;
        this.log('Stopping pipeline...', 'minimal');
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

export { FundingPipeline, type PipelineOptions }; 