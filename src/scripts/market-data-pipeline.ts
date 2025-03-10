import { createClient } from '@supabase/supabase-js';
import * as dotenv from 'dotenv';
import path from 'path';
import axios from 'axios';

// Load environment variables
dotenv.config();

// Define interfaces for market data
interface MarketMetrics {
    timestamp: string;
    asset: string;
    exchange: string;
    price: number;
    volume_24h: number;
    open_interest?: number;
    funding_rate?: number;
    mark_price?: number;
    index_price?: number;
    bid_price?: number;
    ask_price?: number;
    mid_price?: number;
    spread?: number;
    liquidity?: number;
    volatility_24h?: number;
    price_change_24h?: number;
    created_at: string;
}

export interface MarketPipelineOptions {
    storageDir?: string;
    historyLimit?: number;
    updateInterval?: number; // in milliseconds
    logLevel?: 'minimal' | 'normal' | 'verbose';
    exchanges?: string[];
    assets?: string[];
}

export class MarketDataPipeline {
    private supabase;
    protected options: MarketPipelineOptions;
    private isRunning: boolean = false;
    private intervalId?: NodeJS.Timeout;
    private supportedExchanges = ['hyperliquid', 'binance', 'bybit', 'okx', 'deribit'];

    constructor(options: MarketPipelineOptions = {}) {
        this.options = {
            storageDir: path.join(process.cwd(), 'data', 'market-data'),
            historyLimit: 1000,
            updateInterval: 300000, // 5 minutes
            logLevel: 'normal',
            exchanges: ['hyperliquid', 'binance'],
            assets: [],
            ...options
        };

        // Initialize Supabase client
        const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://llanxjeohlxpnndhqbdp.supabase.co';
        const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

        if (!supabaseKey) {
            throw new Error('Missing Supabase API key');
        }

        this.supabase = createClient(supabaseUrl, supabaseKey);
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

    private async insertMarketData(metrics: MarketMetrics[]) {
        this.log(`Inserting ${metrics.length} market metrics into Supabase...`, 'verbose');
        
        try {
            // Insert data into the market_metrics table
            const { data, error } = await this.supabase
                .from('market_metrics')
                .insert(metrics)
                .select();

            if (error) {
                this.log(`Supabase error: ${JSON.stringify(error)}`, 'minimal');
                throw new Error(`Failed to insert market metrics: ${error.message}`);
            }

            this.log(`Successfully inserted ${data?.length || 0} new market metrics`, 'normal');
            return data;
        } catch (error) {
            this.log(`Insert error: ${error instanceof Error ? error.message : JSON.stringify(error)}`, 'minimal');
            throw error;
        }
    }

    private async fetchHyperliquidData(): Promise<MarketMetrics[]> {
        this.log('Fetching data from Hyperliquid...', 'verbose');
        
        try {
            // Fetch market data
            const marketResponse = await axios.post('https://api.hyperliquid.xyz/info', {
                type: 'allMids'
            });
            
            // Fetch funding rates
            const fundingResponse = await axios.post('https://api.hyperliquid.xyz/info', {
                type: 'fundingHistory'
            });

            // Fetch open interest
            const openInterestResponse = await axios.post('https://api.hyperliquid.xyz/info', {
                type: 'openInterest'
            });

            const timestamp = new Date().toISOString();
            const created_at = timestamp;
            const metrics: MarketMetrics[] = [];

            // Process market data
            if (marketResponse.data && Array.isArray(marketResponse.data)) {
                for (const [asset, price] of marketResponse.data) {
                    // Skip if we have specific assets configured and this one isn't in the list
                    if (this.options.assets && this.options.assets.length > 0 && 
                        !this.options.assets.includes(asset)) {
                        continue;
                    }
                    
                    const metric: MarketMetrics = {
                        timestamp,
                        asset,
                        exchange: 'hyperliquid',
                        price: parseFloat(price),
                        volume_24h: 0, // Will be updated if available
                        created_at
                    };
                    
                    metrics.push(metric);
                }
            }

            // Add funding rate data
            if (fundingResponse.data && Array.isArray(fundingResponse.data)) {
                for (const fundingData of fundingResponse.data) {
                    const asset = fundingData.coin;
                    const existingMetric = metrics.find(m => m.asset === asset);
                    
                    if (existingMetric && fundingData.fundingRate) {
                        existingMetric.funding_rate = parseFloat(fundingData.fundingRate);
                    }
                }
            }

            // Add open interest data
            if (openInterestResponse.data && Array.isArray(openInterestResponse.data)) {
                for (const [asset, openInterest] of openInterestResponse.data) {
                    const existingMetric = metrics.find(m => m.asset === asset);
                    
                    if (existingMetric) {
                        existingMetric.open_interest = parseFloat(openInterest);
                    }
                }
            }

            this.log(`Processed ${metrics.length} Hyperliquid metrics`, 'normal');
            return metrics;
        } catch (error) {
            this.log(`Error fetching Hyperliquid data: ${error instanceof Error ? error.message : String(error)}`, 'minimal');
            return [];
        }
    }

    private async fetchBinanceData(): Promise<MarketMetrics[]> {
        this.log('Fetching data from Binance...', 'verbose');
        
        try {
            // Fetch 24hr ticker data for all symbols
            const tickerResponse = await axios.get('https://api.binance.com/api/v3/ticker/24hr');
            
            // Fetch funding rate data for futures
            const fundingResponse = await axios.get('https://fapi.binance.com/fapi/v1/premiumIndex');
            
            // Fetch open interest data
            const openInterestResponse = await axios.get('https://fapi.binance.com/fapi/v1/openInterest');

            const timestamp = new Date().toISOString();
            const created_at = timestamp;
            const metrics: MarketMetrics[] = [];

            // Process ticker data
            if (tickerResponse.data && Array.isArray(tickerResponse.data)) {
                for (const ticker of tickerResponse.data) {
                    // Extract base asset from symbol (e.g., BTCUSDT -> BTC)
                    const asset = ticker.symbol.replace(/USDT$|USD$|BUSD$/, '');
                    
                    // Skip if we have specific assets configured and this one isn't in the list
                    if (this.options.assets && this.options.assets.length > 0 && 
                        !this.options.assets.includes(asset)) {
                        continue;
                    }
                    
                    const metric: MarketMetrics = {
                        timestamp,
                        asset,
                        exchange: 'binance',
                        price: parseFloat(ticker.lastPrice),
                        volume_24h: parseFloat(ticker.volume),
                        price_change_24h: parseFloat(ticker.priceChangePercent),
                        bid_price: parseFloat(ticker.bidPrice),
                        ask_price: parseFloat(ticker.askPrice),
                        created_at
                    };
                    
                    // Calculate spread and mid price
                    if (metric.bid_price && metric.ask_price) {
                        metric.spread = metric.ask_price - metric.bid_price;
                        metric.mid_price = (metric.bid_price + metric.ask_price) / 2;
                    }
                    
                    metrics.push(metric);
                }
            }

            // Add funding rate data
            if (fundingResponse.data && Array.isArray(fundingResponse.data)) {
                for (const fundingData of fundingResponse.data) {
                    // Extract base asset from symbol
                    const asset = fundingData.symbol.replace(/USDT$|USD$|BUSD$/, '');
                    const existingMetric = metrics.find(m => m.asset === asset);
                    
                    if (existingMetric) {
                        existingMetric.funding_rate = parseFloat(fundingData.lastFundingRate);
                        existingMetric.mark_price = parseFloat(fundingData.markPrice);
                        existingMetric.index_price = parseFloat(fundingData.indexPrice);
                    }
                }
            }

            // Add open interest data
            if (openInterestResponse.data && Array.isArray(openInterestResponse.data)) {
                for (const oiData of openInterestResponse.data) {
                    // Extract base asset from symbol
                    const asset = oiData.symbol.replace(/USDT$|USD$|BUSD$/, '');
                    const existingMetric = metrics.find(m => m.asset === asset);
                    
                    if (existingMetric) {
                        existingMetric.open_interest = parseFloat(oiData.openInterest);
                    }
                }
            }

            this.log(`Processed ${metrics.length} Binance metrics`, 'normal');
            return metrics;
        } catch (error) {
            this.log(`Error fetching Binance data: ${error instanceof Error ? error.message : String(error)}`, 'minimal');
            return [];
        }
    }

    async runOnce(): Promise<void> {
        try {
            this.log('Starting market data collection...', 'normal');
            
            const allMetrics: MarketMetrics[] = [];
            
            // Collect data from each configured exchange
            for (const exchange of this.options.exchanges || []) {
                if (!this.supportedExchanges.includes(exchange)) {
                    this.log(`Skipping unsupported exchange: ${exchange}`, 'normal');
                    continue;
                }
                
                let exchangeMetrics: MarketMetrics[] = [];
                
                switch (exchange) {
                    case 'hyperliquid':
                        exchangeMetrics = await this.fetchHyperliquidData();
                        break;
                    case 'binance':
                        exchangeMetrics = await this.fetchBinanceData();
                        break;
                    // Additional exchanges can be added here
                    default:
                        this.log(`Exchange ${exchange} is supported but not implemented yet`, 'normal');
                }
                
                if (exchangeMetrics.length > 0) {
                    allMetrics.push(...exchangeMetrics);
                }
            }

            if (allMetrics.length === 0) {
                this.log('No market metrics collected', 'normal');
            } else {
                this.log(`Collected ${allMetrics.length} market metrics across all exchanges`, 'normal');
                await this.insertMarketData(allMetrics);
            }

        } catch (error) {
            this.log(`Pipeline error: ${error instanceof Error ? error.message : String(error)}`, 'minimal');
            throw error;
        }
    }

    async start(): Promise<void> {
        if (this.isRunning) {
            this.log('Market data pipeline is already running', 'minimal');
            return;
        }

        this.isRunning = true;
        this.log('Starting market data pipeline...', 'minimal');

        await this.runOnce();
        this.intervalId = setInterval(() => this.runOnce(), this.options.updateInterval);
    }

    stop(): void {
        this.isRunning = false;
        this.log('Stopping market data pipeline...', 'minimal');

        if (this.intervalId) {
            clearInterval(this.intervalId);
        }
    }
}

// Example usage
if (require.main === module) {
    const pipeline = new MarketDataPipeline({
        logLevel: 'verbose',
        updateInterval: 600000,  // 10 minutes
        exchanges: ['hyperliquid', 'binance'],
        assets: [] // Empty array means all assets
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