import ccxt from 'ccxt';

// Configure exchanges with API keys from environment variables
export const exchanges = {
  hyperliquid: new ccxt.hyperliquid({
    apiKey: process.env.NEXT_PUBLIC_HYPERLIQUID_API_KEY,
    secret: process.env.NEXT_PUBLIC_HYPERLIQUID_SECRET,
    timeout: 30000,
    enableRateLimit: true,
  }),
  
  bybit: new ccxt.bybit({
    apiKey: process.env.NEXT_PUBLIC_BYBIT_API_KEY,
    secret: process.env.NEXT_PUBLIC_BYBIT_SECRET,
    timeout: 30000,
    enableRateLimit: true,
  }),
  // ... rest of the exchanges config
};

// ... rest of the helper functions 