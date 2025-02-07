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

  binance: new ccxt.binance({
    apiKey: process.env.NEXT_PUBLIC_BINANCE_API_KEY,
    secret: process.env.NEXT_PUBLIC_BINANCE_SECRET,
    timeout: 30000,
    enableRateLimit: true,
    options: {
      defaultType: 'future',
      adjustForTimeDifference: true,
    }
  }),

  okx: new ccxt.okx({
    apiKey: process.env.NEXT_PUBLIC_OKX_API_KEY,
    secret: process.env.NEXT_PUBLIC_OKX_SECRET,
    password: process.env.NEXT_PUBLIC_OKX_PASSWORD,
    timeout: 30000,
    enableRateLimit: true,
  })
};

// Add helper functions for exchange operations
export const getExchangeSymbol = (token: string, exchange: string): string => {
  switch (exchange.toLowerCase()) {
    case 'hyperliquid':
      return `${token}-PERP`;
    case 'bybit':
      return `${token}USDT`;
    case 'binance':
      return `${token}/USDT:USDT`;
    case 'okx':
      return `${token}-USDT-SWAP`;
    default:
      return `${token}/USDT`;
  }
};

export const normalizeSymbol = (symbol: string, exchange: string): string => {
  // Remove common suffixes and standardize format
  return symbol
    .replace(/-PERP$/, '')
    .replace(/USDT$/, '')
    .replace(/-USDT-SWAP$/, '')
    .replace(/\/USDT:USDT$/, '')
    .toUpperCase();
};

export const getExchangeInstance = (exchangeName: string) => {
  const exchange = exchanges[exchangeName.toLowerCase() as keyof typeof exchanges];
  if (!exchange) {
    throw new Error(`Exchange ${exchangeName} not supported`);
  }
  return exchange;
};

export const isExchangeSupported = (exchangeName: string): boolean => {
  return exchangeName.toLowerCase() in exchanges;
};

// Add types for exchange responses
export interface ExchangeFundingRate {
  fundingRate: number;
  predictedFundingRate?: number;
  timestamp: number;
}

export interface ExchangeTicker {
  last: number;
  quoteVolume: number;
  timestamp: number;
}

// Add error handling wrapper
export const safeExchangeExecute = async <T>(
  exchange: ccxt.Exchange,
  method: string,
  ...args: any[]
): Promise<T | null> => {
  try {
    // @ts-ignore - method exists on exchange
    const result = await exchange[method](...args);
    return result as T;
  } catch (error) {
    console.error(`Error executing ${method} on ${exchange.id}:`, error);
    return null;
  }
}; 