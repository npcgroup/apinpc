"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.FlipsideClient = void 0;
const sdk_1 = require("@flipsidecrypto/sdk");
class FlipsideClient {
    constructor(apiKey) {
        this.sdk = new sdk_1.Flipside(apiKey, 'https://api.flipsidecrypto.com');
    }
    async runQuery(query) {
        try {
            const result = await this.sdk.query.run({
                sql: query,
                timeoutMinutes: 5,
            });
            return result;
        }
        catch (error) {
            throw new Error(error instanceof Error ? error.message : 'Query failed');
        }
    }
}
exports.FlipsideClient = FlipsideClient;
