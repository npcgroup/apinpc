"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const hyperliquid_api_1 = require("./hyperliquid-api");
async function analyzeFunding() {
    const api = new hyperliquid_api_1.HyperLiquidAPI();
    try {
        console.log('Fetching HyperLiquid predicted funding rates...');
        const rates = await api.getPredictedFundingRates();
        const analysis = api.analyzeFundingRates(rates);
        // Display results
        console.log('\nTop 5 Funding Opportunities:');
        console.log('----------------------------------------');
        analysis.topOpportunities.forEach((rate, index) => {
            console.log(`${index + 1}. ${api.formatFundingRate(rate)}`);
        });
        console.log('\nStatistics:');
        console.log('----------------------------------------');
        const stats = analysis.statistics;
        console.log(`Total pairs: ${stats.totalPairs}`);
        console.log(`Pairs with funding: ${stats.pairsWithFunding}`);
        console.log(`Positive rates: ${stats.positiveRates}`);
        console.log(`Negative rates: ${stats.negativeRates}`);
        console.log(`Average rate: ${(stats.averageRate * 100).toFixed(6)}%`);
        if (stats.highestRate) {
            console.log('\nHighest funding rate:');
            console.log(api.formatFundingRate(stats.highestRate));
        }
        // Export data if needed
        const exportData = {
            timestamp: new Date().toISOString(),
            analysis: analysis
        };
        // You could save this to a file or database
        // await fs.writeFile('funding-analysis.json', JSON.stringify(exportData, null, 2));
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
// Run the analysis
analyzeFunding().catch(console.error);
