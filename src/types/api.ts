export interface ApiExample {
  title: string;
  code: string;
  response: string;
  language: string;
}

export interface BaseEndpoint {
  method: 'GET' | 'POST' | 'PUT' | 'DELETE';
  path: string;
  description: string;
  parameters?: {
    name: string;
    type: string;
    required: boolean;
    description: string;
  }[];
}

export interface ApiEndpoint extends BaseEndpoint {
  examples?: ApiExample[];
  authentication?: string;
  rateLimit?: string;
  category?: string;
  schema?: {
    request?: object;
    response?: object;
  };
}

export interface ApiResponse {
  error?: string
  data?: any
  status?: number
  timestamp?: string
}

export interface ApiEndpointConfig {
  url: string | ((param: string) => string)
  method: 'GET' | 'POST'
  description?: string
}

// Common interfaces for API responses
export interface TokenPriceData {
  price: number;
  totalSupply?: number;
}

export interface TokenDetailsData {
  price: number;
  marketCap: number;
  volume24h: number;
  totalSupply?: number;
}

export interface TokenMetricsData {
  volume24h?: number;
  transactions24h?: number;
  uniqueUsers24h?: number;
}

export interface MessariMetricsData {
  price?: number;
  volume24h?: number;
  marketCap?: number;
  supply?: number;
}

export interface BitqueryMetricsData {
  transactions24h?: number;
  uniqueSenders24h?: number;
  uniqueReceivers24h?: number;
  volume24h?: number;
}

export interface DuneMetricsData {
  volume24h?: number;
  transactions24h?: number;
  uniqueUsers24h?: number;
}

export interface FlipsideMetricsData {
  volume24h?: number;
  transactions24h?: number;
  uniqueUsers24h?: number;
}

// Add TokenPricesResponse interface
export interface TokenPricesResponse {
  [address: string]: {
    price: number;
    totalSupply?: number;
  };
} 