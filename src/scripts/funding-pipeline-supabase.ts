import { FundingPipeline, PipelineOptions } from './funding-pipeline';
import { supabase } from './utils/supabase-client';

interface PredictedFundingRate {
    timestamp: string;
    asset: string;
    predicted_rate: number;
    annualized_rate: number;
    direction: 'LONGS_PAY' | 'SHORTS_PAY';
    exchange: string;
    next_funding_time: string;
    created_at: string;
}

class SupabaseFundingPipeline extends FundingPipeline {
    constructor(options: PipelineOptions = {}) {
        super(options);
    }

    private async insertPredictedRates(rates: PredictedFundingRate[]) {
        this.log(`Inserting ${rates.length} predicted rates into Supabase...`, 'verbose');
        
        try {
            // Simple insert without upsert
            const { data, error } = await supabase
                .from('predicted_funding_rates')
                .insert(rates)
                .select();

            if (error) {
                this.log(`Supabase error: ${JSON.stringify(error)}`, 'minimal');
                throw new Error(`Failed to insert rates: ${error.message}`);
            }

            this.log(`Successfully inserted ${data?.length || 0} new rates`, 'normal');
            return data;
        } catch (error) {
            this.log(`Insert error: ${error instanceof Error ? error.message : JSON.stringify(error)}`, 'minimal');
            throw error;
        }
    }

    async runOnce() {
        try {
            const response = await fetch('https://api.hyperliquid.xyz/info', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ type: 'predictedFundings' })
            });

            if (!response.ok) {
                throw new Error(`API Error ${response.status}`);
            }

            const rawData = await response.json() as [string, Array<[string, { fundingRate: string; nextFundingTime: number; } | null]>][];
            const timestamp = new Date().toISOString();
            const created_at = timestamp;

            // Transform all exchange data into records
            const allRates: PredictedFundingRate[] = [];
            const validRates: Array<{ asset: string; predicted: number; timestamp: number }> = [];

            for (const [asset, exchanges] of rawData) {
                for (const [exchangeName, data] of exchanges) {
                    if (data && data.fundingRate) {
                        const rate = parseFloat(data.fundingRate);
                        if (!isNaN(rate)) {  // Remove zero check to include all valid rates
                            const nextFundingTime = new Date(data.nextFundingTime).toISOString();
                            
                            allRates.push({
                                timestamp,
                                asset,
                                predicted_rate: rate,
                                annualized_rate: rate * 365,
                                direction: rate >= 0 ? 'LONGS_PAY' : 'SHORTS_PAY',
                                exchange: exchangeName,
                                next_funding_time: nextFundingTime,
                                created_at
                            });
                            
                            validRates.push({
                                asset,
                                predicted: rate,
                                timestamp: Date.now()
                            });
                        }
                    }
                }
            }

            if (allRates.length === 0) {
                this.log('No valid rates found', 'normal');
            } else {
                this.log(`Found ${allRates.length} rates across all exchanges`, 'normal');
                await this.insertPredictedRates(allRates);
            }

            // Return FundingAnalysis object to satisfy the base class requirement
            return {
                topOpportunities: validRates,
                statistics: {
                    totalPairs: rawData.length,
                    pairsWithFunding: validRates.length,
                    positiveRates: validRates.filter(r => r.predicted > 0).length,
                    negativeRates: validRates.filter(r => r.predicted < 0).length,
                    highestRate: validRates.length > 0 ? validRates.reduce((max, curr) => 
                        Math.abs(curr.predicted) > Math.abs(max.predicted) ? curr : max
                    ) : null,
                    averageRate: validRates.reduce((sum, rate) => sum + rate.predicted, 0) / validRates.length || 0
                }
            };

        } catch (error) {
            this.log(`Pipeline error: ${error instanceof Error ? error.message : String(error)}`, 'minimal');
            throw error;
        }
    }
}

// Example usage
if (require.main === module) {
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
}

export { SupabaseFundingPipeline }; 