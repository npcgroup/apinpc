"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.CoinAlyzeAPI = void 0;
const node_fetch_1 = __importDefault(require("node-fetch"));
class CoinAlyzeAPI {
    constructor(config) {
        this.lastRequestTime = 0;
        this.config = {
            baseUrl: 'https://api.coinalyze.net',
            rateLimit: 40,
            ...config
        };
    }
    /**
     * Base request handler with rate limiting
     */
    async makeRequest(endpoint, params) {
        const now = Date.now();
        const timeSinceLast = now - this.lastRequestTime;
        // Enforce rate limit (40 requests/minute)
        if (timeSinceLast < 1500) { // 60s/40 = 1.5s between requests
            await new Promise(resolve => setTimeout(resolve, 1500 - timeSinceLast));
        }
        // Add /v1/ to the endpoint path
        const url = new URL(`${this.config.baseUrl}/v1/${endpoint}`);
        console.log('Making request to:', url.toString()); // Debug log
        if (params) {
            Object.entries(params).forEach(([key, value]) => {
                if (Array.isArray(value)) {
                    url.searchParams.append(key, value.join(','));
                }
                else {
                    url.searchParams.append(key, value.toString());
                }
            });
        }
        // Try different header variations
        const headers = {
            'X-API-Key': this.config.apiKey, // Capitalized version
            'x-api-key': this.config.apiKey, // lowercase version
            'apikey': this.config.apiKey, // simple version
            'Accept': 'application/json'
            // Removed Content-Type as it's a GET request
        };
        console.log('Request headers:', headers); // Debug log
        const response = await (0, node_fetch_1.default)(url.toString(), {
            method: 'GET',
            headers
        });
        this.lastRequestTime = Date.now();
        if (!response.ok) {
            const errorText = await response.text();
            console.log('Full response:', {
                status: response.status,
                headers: Object.fromEntries(response.headers.entries()),
                body: errorText,
                url: url.toString() // Log the URL that was called
            });
            throw new Error(`API Error ${response.status}: ${errorText}`);
        }
        return response.json();
    }
    /**
     * Get list of supported exchanges
     */
    async getSupportedExchanges() {
        return this.makeRequest('exchanges');
    }
    /**
     * Get current funding rates for specified symbols
     */
    async getCurrentFundingRates(symbols) {
        return this.makeRequest('funding-rate', { symbols });
    }
    /**
     * Get OHLCV history for specified parameters
     */
    async getOHLCVHistory(params) {
        return this.makeRequest('ohlcv-history', {
            symbols: params.symbols,
            interval: params.interval,
            from: params.from,
            to: params.to
        });
    }
    /**
     * Get open interest history for specified parameters
     */
    async getOpenInterestHistory(params) {
        return this.makeRequest('open-interest-history', {
            symbols: params.symbols,
            interval: params.interval,
            from: params.from,
            to: params.to,
            convert_to_usd: params.convertToUSD ? 'true' : 'false'
        });
    }
}
exports.CoinAlyzeAPI = CoinAlyzeAPI;
// Example usage:
/*
async function example() {
  const api = new CoinAlyzeAPI({
    apiKey: 'your-api-key-here'
  });

  // Get supported exchanges
  const exchanges = await api.getSupportedExchanges();
  console.log('Supported exchanges:', exchanges);

  // Get current funding rates
  const fundingRates = await api.getCurrentFundingRates(['BTC-PERP', 'ETH-PERP']);
  console.log('Funding rates:', fundingRates);

  // Get OHLCV history
  const ohlcvData = await api.getOHLCVHistory({
    symbols: ['BTC-PERP'],
    interval: '1h',
    from: Date.now() - 24 * 60 * 60 * 1000, // 24 hours ago
    to: Date.now()
  });
  console.log('OHLCV data:', ohlcvData);
}
*/ 
