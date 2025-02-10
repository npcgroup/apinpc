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
        console.log('Raw API response:', JSON.stringify(rawData, null, 2));
        // Transform the response into a more readable format
        return rawData.map(([asset, predictedRate]) => {
            const predicted = parseFloat(predictedRate);
            return {
                asset,
                predicted: isNaN(predicted) ? 0 : predicted, // Default to 0 if NaN
                timestamp: Date.now()
            };
        });
    }
    /**
     * Get predicted funding rate for a specific asset
     */
    async getPredictedFundingRate(asset) {
        const rates = await this.getPredictedFundingRates();
        return rates.find(rate => rate.asset === asset) || null;
    }
}
exports.HyperLiquidAPI = HyperLiquidAPI;
