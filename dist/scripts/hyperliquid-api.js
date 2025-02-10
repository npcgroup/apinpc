"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.HyperLiquidAPI = void 0;
const node_fetch_1 = __importDefault(require("node-fetch"));
class HyperLiquidAPI {
    constructor() {
        this.baseUrl = 'https://api.hyperliquid.xyz';
    }
    /**
     * Get predicted funding rates for all assets
     */
    async getPredictedFundingRates() {
        const response = await (0, node_fetch_1.default)(`${this.baseUrl}/info`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                type: 'predictedFundings'
            })
        });
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`API Error ${response.status}: ${errorText}`);
        }
        const rawData = await response.json();
        // Transform the response into a more readable format
        return rawData
            .map(([asset, exchangeData]) => {
            // Find HyperLiquid data (marked as "HlPerp" in the response)
            const hlData = exchangeData.find(([exchange]) => exchange === 'HlPerp')?.[1];
            if (!hlData)
                return null;
            const predicted = parseFloat(hlData.fundingRate);
            return {
                asset,
                predicted: isNaN(predicted) ? 0 : predicted,
                timestamp: Date.now()
            };
        })
            .filter((rate) => rate !== null &&
            !isNaN(rate.predicted) &&
            rate.predicted !== 0);
    }
    /**
     * Get predicted funding rate for a specific asset
     */
    async getPredictedFundingRate(asset) {
        const rates = await this.getPredictedFundingRates();
        return rates.find(rate => rate.asset === asset) || null;
    }
    /**
     * Analyze funding rates data
     */
    analyzeFundingRates(rates, topN = 5) {
        const validRates = rates.filter(rate => !isNaN(rate.predicted) && rate.predicted !== 0);
        const sortedRates = validRates.sort((a, b) => Math.abs(b.predicted) - Math.abs(a.predicted));
        const positiveRates = validRates.filter(r => r.predicted > 0);
        const negativeRates = validRates.filter(r => r.predicted < 0);
        const averageRate = validRates.length > 0
            ? validRates.reduce((sum, rate) => sum + rate.predicted, 0) / validRates.length
            : 0;
        return {
            topOpportunities: sortedRates.slice(0, topN),
            statistics: {
                totalPairs: rates.length,
                pairsWithFunding: validRates.length,
                positiveRates: positiveRates.length,
                negativeRates: negativeRates.length,
                highestRate: sortedRates[0] || null,
                averageRate
            }
        };
    }
    /**
     * Format funding rate for display
     */
    formatFundingRate(rate, includeAnnualized = true) {
        const fundingPercent = (rate.predicted * 100).toFixed(6);
        const direction = rate.predicted >= 0 ? 'LONGS PAY' : 'SHORTS PAY';
        const annualized = (rate.predicted * 100 * 365).toFixed(2);
        return includeAnnualized
            ? `${rate.asset.padEnd(10)} ${fundingPercent.padStart(10)}% (${annualized}% APR) - ${direction}`
            : `${rate.asset.padEnd(10)} ${fundingPercent.padStart(10)}% (${direction})`;
    }
}
exports.HyperLiquidAPI = HyperLiquidAPI;
