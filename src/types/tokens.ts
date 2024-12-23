export interface Token {
  address: string;
  symbol: string;
  name: string;
  price: number;
  volume24h: number;
  marketCap: number;
  totalSupply?: number;
} 