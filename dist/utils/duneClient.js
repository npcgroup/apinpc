"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.DuneClient = void 0;
class DuneClient {
    constructor(apiKey) {
        this.apiKey = apiKey;
        this.baseUrl = 'https://api.dune.com/api/v1';
    }
    async getMetrics(queryId) {
        try {
            const response = await fetch(`${this.baseUrl}/query/${queryId}`, {
                headers: {
                    'x-dune-api-key': this.apiKey
                }
            });
            if (!response.ok) {
                throw new Error(`Dune API error: ${response.statusText}`);
            }
            const data = await response.json();
            return {
                success: true,
                data
            };
        }
        catch (error) {
            return {
                success: false,
                data: null,
                error: error instanceof Error ? error.message : 'Unknown error'
            };
        }
    }
    async getTokenMetrics(symbol) {
        // Replace with your actual query ID for token metrics
        return this.getMetrics(`token-metrics-${symbol}`);
    }
}
exports.DuneClient = DuneClient;
