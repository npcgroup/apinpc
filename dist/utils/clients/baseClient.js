"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.BaseApiClient = void 0;
class BaseApiClient {
    constructor(apiKey) {
        this.apiKey = apiKey;
    }
    async request(endpoint, options) {
        const response = await fetch(endpoint, {
            ...options,
            headers: {
                ...options?.headers,
                'Authorization': `Bearer ${this.apiKey}`,
            },
        });
        if (!response.ok) {
            throw new Error(`API request failed: ${response.statusText}`);
        }
        return response.json();
    }
}
exports.BaseApiClient = BaseApiClient;
