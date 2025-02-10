"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.BitqueryClient = void 0;
const baseClient_1 = require("./baseClient");
class BitqueryClient extends baseClient_1.BaseApiClient {
    async query(query) {
        return this.request('/api/query', {
            method: 'POST',
            body: JSON.stringify({ query }),
        });
    }
}
exports.BitqueryClient = BitqueryClient;
