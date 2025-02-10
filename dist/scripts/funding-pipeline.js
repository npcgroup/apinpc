"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.FundingPipeline = void 0;
const hyperliquid_api_1 = require("./hyperliquid-api");
const funding_storage_1 = require("./funding-storage");
const path_1 = __importDefault(require("path"));
class FundingPipeline {
    constructor(options = {}) {
        this.isRunning = false;
        this.options = {
            storageDir: path_1.default.join(process.cwd(), 'data', 'funding-history'),
            historyLimit: 1000,
            minimumFundingThreshold: 0.0001, // 0.01%
            updateInterval: 300000, // 5 minutes
            logLevel: 'normal',
            ...options
        };
        this.api = new hyperliquid_api_1.HyperLiquidAPI();
        this.storage = new funding_storage_1.FundingStorage({
            directory: this.options.storageDir || path_1.default.join(process.cwd(), 'data', 'funding-history'),
            maxHistoryItems: this.options.historyLimit
        });
    }
    log(message, level) {
        if (level === 'minimal' ||
            (level === 'normal' && this.options.logLevel !== 'minimal') ||
            (level === 'verbose' && this.options.logLevel === 'verbose')) {
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
exports.FundingPipeline = FundingPipeline;
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
