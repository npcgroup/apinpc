"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.exchanges = void 0;
const ccxt_1 = __importDefault(require("ccxt"));
// Configure exchanges with API keys from environment variables
exports.exchanges = {
    hyperliquid: new ccxt_1.default.hyperliquid({
        apiKey: process.env.NEXT_PUBLIC_HYPERLIQUID_API_KEY,
        secret: process.env.NEXT_PUBLIC_HYPERLIQUID_SECRET,
        timeout: 30000,
        enableRateLimit: true,
    }),
    bybit: new ccxt_1.default.bybit({
        apiKey: process.env.NEXT_PUBLIC_BYBIT_API_KEY,
        secret: process.env.NEXT_PUBLIC_BYBIT_SECRET,
        timeout: 30000,
        enableRateLimit: true,
    }),
    // ... rest of the exchanges config
};
// ... rest of the helper functions 
