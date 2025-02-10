"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.FundingArbitrageStrategy = void 0;
class FundingArbitrageStrategy {
    constructor(config) {
        this.config = config;
    }
    analyze(metrics) {
        const { threshold = 0.1 } = this.config;
        if (Math.abs(metrics.funding_rate) > threshold) {
            return {
                symbol: metrics.symbol,
                fundingRate: metrics.funding_rate,
                expectedReturn: metrics.funding_rate * metrics.open_interest,
                timestamp: new Date().toISOString()
            };
        }
        return null;
    }
}
exports.FundingArbitrageStrategy = FundingArbitrageStrategy;
