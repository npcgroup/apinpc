"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.withRetry = withRetry;
async function withRetry(fn, maxRetries = 3, delay = 1000) {
    let lastError;
    for (let i = 0; i < maxRetries; i++) {
        try {
            return await fn();
        }
        catch (error) {
            lastError = error;
            await new Promise(resolve => setTimeout(resolve, delay * Math.pow(2, i)));
        }
    }
    throw lastError;
}
