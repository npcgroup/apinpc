"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const hyperliquid_api_1 = require("./hyperliquid-api");
async function main() {
    const api = new hyperliquid_api_1.HyperLiquidAPI();
    try {
        console.log('Fetching HyperLiquid predicted funding rates...');
        // Get all funding rates
        const rates = await api.getPredictedFundingRates();
        // Filter out zero rates and sort by absolute funding rate value
        const validRates = rates.filter(rate => !isNaN(rate.predicted) && rate.predicted !== 0);
        const sortedRates = validRates.sort((a, b) => Math.abs(b.predicted) - Math.abs(a.predicted));
        // Format and display the results
        console.log('\nPredicted Funding Rates (sorted by magnitude):');
        console.log('----------------------------------------');
        sortedRates.forEach(rate => {
            const fundingPercent = (rate.predicted * 100).toFixed(6); // Increased precision
            const direction = rate.predicted >= 0 ? 'LONGS PAY' : 'SHORTS PAY';
            const formattedRate = `${fundingPercent}%`.padStart(10);
            console.log(`${rate.asset.padEnd(10)} ${formattedRate} (${direction})`);
        });
        // Show some statistics
        console.log('\nStatistics:');
        console.log('----------------------------------------');
        const positiveRates = sortedRates.filter(r => r.predicted > 0);
        const negativeRates = sortedRates.filter(r => r.predicted < 0);
        console.log(`Total pairs with funding: ${sortedRates.length}`);
        console.log(`Total pairs: ${rates.length}`);
        console.log(`Positive rates: ${positiveRates.length}`);
        console.log(`Negative rates: ${negativeRates.length}`);
        // Find highest absolute funding rate
        if (sortedRates.length > 0) {
            const highestAbs = sortedRates[0];
            console.log(`\nHighest funding rate: ${highestAbs.asset} at ${(highestAbs.predicted * 100).toFixed(6)}%`);
            // Show top 5 opportunities
            console.log('\nTop 5 Funding Opportunities:');
            console.log('----------------------------------------');
            sortedRates.slice(0, 5).forEach((rate, index) => {
                const fundingPercent = (rate.predicted * 100).toFixed(6);
                const annualized = (rate.predicted * 100 * 365).toFixed(2);
                const direction = rate.predicted >= 0 ? 'LONGS PAY' : 'SHORTS PAY';
                console.log(`${index + 1}. ${rate.asset.padEnd(10)} ${fundingPercent.padStart(10)}% (${annualized}% APR) - ${direction}`);
            });
        }
    }
    catch (error) {
        if (error instanceof Error) {
            console.error('Error:', error.message);
        }
        else {
            console.error('Unknown error:', error);
        }
    }
}
// Run the script
main().catch(console.error);
