import { createClient } from '@supabase/supabase-js'
import { DuneClient } from '@/utils/duneClient'
import { FlipsideClient } from '@/utils/flipsideClient'
import { DefiLlamaClient } from '@/utils/defiLlamaClient'
import { EtherscanClient } from '@/utils/etherscanClient'
import { formatMetrics, formatDuneMetrics, formatFlipsideMetrics, type MetricData } from '@/utils/metrics'
import { supabaseAdmin as supabase } from '../lib/supabaseClient'
import { ErrorWithDetails } from '../types/errors'
import { MessariClient } from '@/utils/messariClient'
import { BitqueryClient } from '@/utils/bitqueryClient'
import { FootprintClient } from '@/utils/footprintClient'
import { withRetry, withTimeout } from '@/utils/retryUtils'
import { 
  TokenMetricsData,
  MessariMetricsData,
  DuneMetricsData,
  FlipsideMetricsData 
} from '../types/api'
import { Token as TokenType } from '../types/tokens'
import { DexScreenerClient } from '@/utils/dexScreenerClient'
import { DexScreenerToken } from '../utils/dexScreenerClient'
import { loadMetricsData, getLatestDataFile } from '../utils/loadMetrics'
import { TokenMetric, DexPair } from '../types/metrics'
import { PerpetualMetrics, TRACKED_PERP_TOKENS } from '../types/perpetuals'
import { promises as fs } from 'fs'
import * as path from 'path'

interface ProtocolData {
  name: string
  tvl: number
  volume24h: number
  fees24h: number
  users24h: number
  chains: string[]
  timestamp: Date
}

interface TokenData {
  address: string
  symbol: string
  name: string
  price: number
  volume24h: number
  marketCap: number
  timestamp: Date
}

interface ChainMetrics {
  chain: string
  tvl: number
  transactions24h: number
  fees24h: number
  active_addresses_24h: number
  timestamp: Date
}

interface Protocol {
  name: string;
  tvl: number;
  chains: string[];
  volume24h?: number;
  fees24h?: number;
  users24h?: number;
}

interface DuneMetrics {
  chain?: string;
  transactions24h?: number;
  fees24h?: number;
  activeAddresses24h?: number;
  volume24h?: number;
  timestamp?: Date;
  [key: string]: any;
}

// Add this interface for raw DefiLlama data
interface RawDefiLlamaProtocol {
  name: string;
  tvl: number | null;
  chains: string[] | null;
  volume24h?: number | null;
  fees24h?: number | null;
  users24h?: number | null;
  // Add any other properties that might come from DefiLlama
}

interface DexMetrics {
  name: string;
  volume24h: number;
  tvl: number;
  trades24h: number;
  unique_traders_24h: number;
  timestamp: Date;
}

interface LendingMetrics {
  name: string;
  tvl: number;
  total_borrowed: number;
  total_supplied: number;
  borrow_apy: number;
  supply_apy: number;
  timestamp: Date;
}

interface DerivativesMetrics {
  name: string;
  volume24h: number;
  open_interest: number;
  trades24h: number;
  unique_traders_24h: number;
  timestamp: Date;
}

interface MergedToken {
  address: string;
  symbol: string;
  name: string;
  price: number;
  volume24h: number;
  marketCap: number;
  totalSupply: number;
}

// Add type for token prices response
interface TokenPricesResponse {
  [address: string]: {
    price: number;
    totalSupply?: number;
  };
}

interface TokenPriceData {
  price?: number;
  totalSupply?: number;
}

interface TokenDetailsData {
  price?: number;
  marketCap?: number;
  volume24h?: number;
  totalSupply?: number;
}

// Update the return type to match DexScreenerMetric
interface DexScreenerMetric {
  name: string;
  symbol: string;
  price: number;
  volume24h: number;
  marketCap: number;
  address: string;
  timestamp?: Date;
}

export class DataIngestionService {
  private duneClient: DuneClient
  private flipsideClient: FlipsideClient
  private defiLlamaClient: DefiLlamaClient
  private etherscanClient: EtherscanClient
  private messariClient: MessariClient
  private bitqueryClient: BitqueryClient
  private footprintClient: FootprintClient
  private dexScreenerClient: DexScreenerClient

  constructor() {
    this.duneClient = new DuneClient(process.env.NEXT_PUBLIC_DUNE_API_KEY!)
    this.flipsideClient = new FlipsideClient(process.env.NEXT_PUBLIC_FLIPSIDE_API_KEY!)
    this.defiLlamaClient = new DefiLlamaClient()
    this.etherscanClient = new EtherscanClient(process.env.NEXT_PUBLIC_ETHERSCAN_API_KEY!)
    this.messariClient = new MessariClient(process.env.NEXT_PUBLIC_MESSARI_API_KEY!)
    this.bitqueryClient = new BitqueryClient(process.env.NEXT_PUBLIC_BITQUERY_API_KEY!)
    this.footprintClient = new FootprintClient(process.env.NEXT_PUBLIC_FOOTPRINT_API_KEY!)
    this.dexScreenerClient = new DexScreenerClient();
  }

  public async ingestAllData() {
    try {
      console.log('Starting data ingestion...')
      
      await this.ingestProtocolData().catch((e: unknown) => {
        const err = e as ErrorWithDetails;
        console.error('Protocol data ingestion failed:', {
          name: err.name || 'Unknown Error',
          message: err.message || 'An unknown error occurred',
          stack: err.stack,
          details: err.details
        });
        throw err;
      });
      
      await this.ingestTokenData().catch(e => {
        console.error('Token data ingestion failed:', e);
        throw e;
      });
      
      console.log('Skipping chain metrics ingestion...');
      
      await this.ingestDexData().catch(e => {
        console.error('DEX data ingestion failed:', e);
        throw e;
      });
      
      await this.ingestLendingData().catch(e => {
        console.error('Lending data ingestion failed:', e);
        throw e;
      });
      
      await this.ingestDerivativesData().catch(e => {
        console.error('Derivatives data ingestion failed:', e);
        throw e;
      });

      console.log('Data ingestion completed successfully')
    } catch (error: unknown) {
      const err = error as ErrorWithDetails;
      console.error('Error during data ingestion:', {
        name: err.name || 'Unknown Error',
        message: err.message || 'An unknown error occurred',
        stack: err.stack,
        details: err.details
      });
      throw err;
    }
  }

  private async ingestProtocolData() {
    try {
      console.log('Ingesting protocol data...');
      
      const protocols = await this.defiLlamaClient.getTopProtocols() as RawDefiLlamaProtocol[];
      
      const validProtocolData = await Promise.all(
        protocols
          .filter(protocol => protocol.tvl !== null && protocol.chains !== null)
          .map(async (protocol) => {
            try {
              const [duneMetrics, flipsideMetrics] = await Promise.all([
                this.duneClient.getProtocolMetrics(protocol.name),
                this.flipsideClient.getProtocolMetrics(protocol.name)
              ]);

              return {
                name: protocol.name,
                tvl: protocol.tvl!,
                volume24h: protocol.volume24h ?? duneMetrics.volume24h ?? flipsideMetrics.volume24h ?? 0,
                fees24h: protocol.fees24h ?? duneMetrics.fees24h ?? flipsideMetrics.fees24h ?? 0,
                users24h: protocol.users24h ?? duneMetrics.users24h ?? flipsideMetrics.users24h ?? 0,
                chains: protocol.chains!,
                timestamp: new Date()
              };
            } catch (error) {
              console.error(`Error processing protocol ${protocol.name}:`, error);
              return null;
            }
          })
      );

      const filteredData = validProtocolData.filter((data): data is NonNullable<typeof data> => data !== null);

      console.log(`Upserting ${filteredData.length} protocol metrics to Supabase`);
      const { error } = await supabase
        .from('protocol_metrics')
        .upsert(filteredData, {
          onConflict: 'name',
          ignoreDuplicates: false
        });

      if (error) {
        console.error('Protocol metrics upsert error:', error);
        throw error;
      }
    } catch (error: unknown) {
      const err = error as ErrorWithDetails;
      console.error('Protocol ingestion error:', error);
      throw err;
    }
  }

  private mergeTokenData(tokenDataSources: any[]): MergedToken[] {
    const [coinGeckoTokens, defiLlamaTokens, flipsideTokens] = tokenDataSources;
    
    // Create a map of tokens by address
    const tokenMap = new Map<string, MergedToken>();

    // Merge CoinGecko data
    coinGeckoTokens.forEach((token: any) => {
      tokenMap.set(token.address.toLowerCase(), {
        address: token.address,
        symbol: token.symbol,
        name: token.name,
        price: token.current_price || 0,
        volume24h: token.total_volume || 0,
        marketCap: token.market_cap || 0,
        totalSupply: token.total_supply || 0
      });
    });

    // Merge DeFiLlama data
    Object.entries(defiLlamaTokens).forEach(([address, data]: [string, any]) => {
      const existing = tokenMap.get(address.toLowerCase());
      if (existing) {
        existing.price = data.price || existing.price;
        existing.totalSupply = data.totalSupply || existing.totalSupply;
        existing.marketCap = existing.price * existing.totalSupply;
      }
    });

    // Merge Flipside data
    flipsideTokens.forEach((token: any) => {
      const existing = tokenMap.get(token.address.toLowerCase());
      if (existing) {
        existing.volume24h = token.volume24h || existing.volume24h;
        existing.totalSupply = token.totalSupply || existing.totalSupply;
      }
    });

    return Array.from(tokenMap.values());
  }

  private async ingestTokenData() {
    try {
      console.log('Ingesting token data...');
      
      // Get token data from multiple sources
      const [defiLlamaTokens, dexScreenerPairs] = await Promise.all([
        this.fetchDefiLlamaTokens(),
        this.dexScreenerClient.getLatestTokenProfiles()
      ]);

      // Combine and validate token data
      const tokenPromises = defiLlamaTokens.map(async (token) => {
        try {
          // Skip metrics fetch for zero address
          if (token.address === '0x0000000000000000000000000000000000000000') {
            return {
              ...token,
              timestamp: new Date()
            };
          }

          // Get token metrics from our authenticated APIs with proper error handling
          const [duneMetrics, flipsideMetrics, messariMetrics] = await Promise.allSettled([
            this.duneClient.getTokenMetrics(token.address).catch(err => {
              console.warn(`Dune metrics failed for ${token.symbol}:`, err.message);
              return null;
            }),
            this.flipsideClient.getTokenMetrics(token.address).catch(err => {
              console.warn(`Flipside metrics failed for ${token.symbol}:`, err.message);
              return null;
            }),
            this.messariClient.getAssetMetrics(token.symbol).catch(err => {
              console.warn(`Messari metrics failed for ${token.symbol}:`, err.message);
              return null;
            })
          ]);

          // Find matching DexScreener pair data
          const dexScreenerData = dexScreenerPairs.find(p => 
            p.tokenAddress.toLowerCase() === token.address.toLowerCase()
          );

          // Combine metrics, using the first available value
          const volume24h = 
            (duneMetrics.status === 'fulfilled' && duneMetrics.value?.volume24h) ||
            (flipsideMetrics.status === 'fulfilled' && flipsideMetrics.value?.volume24h) ||
            (messariMetrics.status === 'fulfilled' && messariMetrics.value?.volume24h) ||
            token.volume24h ||
            0;

          return {
            ...token,
            volume24h,
            icon: dexScreenerData?.icon,
            description: dexScreenerData?.description,
            timestamp: new Date()
          };
        } catch (error) {
          console.error(`Error processing token ${token.symbol}:`, error);
          return null;
        }
      });

      const tokenResults = await Promise.all(tokenPromises);
      const validTokenData = tokenResults.filter((data): data is NonNullable<typeof data> => 
        data !== null && data.price > 0
      );

      if (validTokenData.length === 0) {
        console.warn('No valid token data to insert');
        return;
      }

      console.log(`Upserting ${validTokenData.length} token metrics to Supabase`);
      const { error } = await supabase
        .from('token_metrics')
        .upsert(validTokenData, {
          onConflict: 'address',
          ignoreDuplicates: false
        });

      if (error) {
        console.error('Token metrics upsert error:', error);
        throw error;
      }
    } catch (error) {
      console.error('Token data ingestion error:', error);
      throw error;
    }
  }

  private async ingestChainMetrics() {
    console.log('Ingesting chain metrics...')
    
    const chains = ['ethereum', 'bsc', 'polygon', 'arbitrum', 'optimism']
    
    const chainMetrics: ChainMetrics[] = await Promise.all(
      chains.map(async (chain) => {
        const [duneMetrics, flipsideMetrics] = await Promise.all([
          this.duneClient.getChainMetrics(chain),
          this.flipsideClient.getChainMetrics(chain)
        ])

        const tvl = await this.defiLlamaClient.getChainTVL(chain)

        return {
          chain,
          tvl: tvl || 0,
          transactions24h: duneMetrics.transactions24h || flipsideMetrics.transactions24h || 0,
          fees24h: duneMetrics.fees24h || flipsideMetrics.fees24h || 0,
          active_addresses_24h: duneMetrics.activeAddresses24h || flipsideMetrics.activeAddresses24h || 0,
          timestamp: new Date()
        }
      })
    )

    console.log(`Inserting ${chainMetrics.length} chain metrics to Supabase`);
    const { error } = await supabase
      .from('chain_metrics')
      .insert(chainMetrics)

    if (error) {
      console.error('Chain metrics insertion error:', error);
      throw error;
    }
  }

  private async ingestDexData() {
    try {
      console.log('Ingesting DEX data...');
      
      const dexProtocols = ['uniswap', 'sushiswap', 'curve', 'balancer', 'pancakeswap'];
      
      const dexMetrics = await Promise.all(
        dexProtocols.map(async (protocol) => {
          try {
            // Get TVL from DefiLlama
            const tvl = await this.defiLlamaClient.getProtocolTVL(protocol);
            
            // Get metrics from multiple sources
            const [duneMetrics, flipsideMetrics] = await Promise.all([
              this.duneClient.getDexMetrics(protocol).catch(() => ({
                volume24h: 0,
                trades24h: 0,
                uniqueTraders24h: 0
              })),
              this.flipsideClient.getDexMetrics(protocol).catch(() => ({
                volume24h: 0,
                trades24h: 0,
                uniqueTraders24h: 0
              }))
            ]);

            return {
              name: protocol,
              volume24h: duneMetrics.volume24h || flipsideMetrics.volume24h || 0,
              tvl: tvl || 0,
              trades24h: duneMetrics.trades24h || flipsideMetrics.trades24h || 0,
              unique_traders_24h: duneMetrics.uniqueTraders24h || flipsideMetrics.uniqueTraders24h || 0,
              timestamp: new Date()
            };
          } catch (error) {
            console.error(`Error processing DEX ${protocol}:`, error);
            return null;
          }
        })
      );

      // Filter out any failed protocol processing
      const validDexMetrics = dexMetrics.filter((data): data is NonNullable<typeof data> => data !== null);

      console.log(`Upserting ${validDexMetrics.length} DEX metrics to Supabase`);
      const { error } = await supabase
        .from('dex_metrics')
        .upsert(validDexMetrics, {
          onConflict: 'name',
          ignoreDuplicates: false // This allows updates to existing records
        });

      if (error) {
        console.error('DEX metrics upsert error:', error);
        throw error;
      }
    } catch (error: unknown) {
      const err = error as ErrorWithDetails;
      console.error('DEX data ingestion error:', {
        name: err.name || 'Unknown Error',
        message: err.message || 'An unknown error occurred',
        stack: err.stack,
        details: err.details
      });
      throw err;
    }
  }

  private async ingestLendingData() {
    try {
      console.log('Ingesting lending protocol data...');
      
      // Define known lending protocols
      const lendingProtocols = [
        { name: 'aave-v3', displayName: 'Aave V3' },
        { name: 'compound-v3', displayName: 'Compound V3' },
        { name: 'maker', displayName: 'MakerDAO' },
        { name: 'benqi', displayName: 'Benqi' },
        { name: 'venus', displayName: 'Venus' },
        { name: 'justlend', displayName: 'JustLend' },
        { name: 'morpho', displayName: 'Morpho' }
      ];
      
      const lendingMetrics = await Promise.all(
        lendingProtocols.map(async (protocol) => {
          try {
            // Get TVL from DefiLlama
            const tvl = await this.defiLlamaClient.getProtocolTVL(protocol.name);
            
            // Get detailed lending metrics from multiple sources
            const [duneMetrics, flipsideMetrics] = await Promise.all([
              this.duneClient.getLendingMetrics(protocol.displayName).catch(() => ({
                totalBorrowed: 0,
                totalSupplied: 0,
                borrowApy: 0,
                supplyApy: 0
              })),
              this.flipsideClient.getLendingMetrics(protocol.displayName).catch(() => ({
                totalBorrowed: 0,
                totalSupplied: 0,
                borrowApy: 0,
                supplyApy: 0
              }))
            ]);

            // Combine and validate metrics
            return {
              name: protocol.displayName,
              tvl: tvl || 0,
              total_borrowed: duneMetrics.totalBorrowed || flipsideMetrics.totalBorrowed || 0,
              total_supplied: duneMetrics.totalSupplied || flipsideMetrics.totalSupplied || 0,
              borrow_apy: duneMetrics.borrowApy || flipsideMetrics.borrowApy || 0,
              supply_apy: duneMetrics.supplyApy || flipsideMetrics.supplyApy || 0,
              timestamp: new Date()
            };
          } catch (error) {
            console.error(`Error processing lending protocol ${protocol.displayName}:`, error);
            return null;
          }
        })
      );

      const validLendingMetrics = lendingMetrics.filter((data): data is NonNullable<typeof data> => 
        data !== null && data.tvl > 0
      );

      if (validLendingMetrics.length === 0) {
        console.warn('No valid lending metrics to insert');
        return;
      }

      console.log(`Upserting ${validLendingMetrics.length} lending metrics to Supabase`);
      const { error } = await supabase
        .from('lending_metrics')
        .upsert(validLendingMetrics, {
          onConflict: 'name',
          ignoreDuplicates: false
        });

      if (error) {
        console.error('Lending metrics upsert error:', error);
        throw error;
      }
    } catch (error: unknown) {
      const err = error as ErrorWithDetails;
      console.error('Lending data ingestion error:', {
        name: err.name || 'Unknown Error',
        message: err.message || 'An unknown error occurred',
        stack: err.stack,
        details: err.details
      });
      throw err;
    }
  }

  private async ingestDerivativesData() {
    try {
      console.log('Ingesting derivatives data...')
      
      const derivativesProtocols = ['gmx', 'dydx', 'perpetual', 'synthetix']
      
      const derivativesMetrics = await Promise.all(
        derivativesProtocols.map(async (protocol) => {
          try {
            const [duneMetrics, flipsideMetrics] = await Promise.all([
              this.duneClient.getDerivativesMetrics(protocol),
              this.flipsideClient.getDerivativesMetrics(protocol)
            ]);

            return {
              name: protocol,
              volume24h: duneMetrics.volume24h || flipsideMetrics.volume24h || 0,
              open_interest: duneMetrics.openInterest || flipsideMetrics.openInterest || 0,
              trades24h: duneMetrics.trades24h || flipsideMetrics.trades24h || 0,
              unique_traders_24h: duneMetrics.uniqueTraders24h || flipsideMetrics.uniqueTraders24h || 0,
              timestamp: new Date()
            };
          } catch (error) {
            console.error(`Error processing derivatives protocol ${protocol}:`, error);
            return null;
          }
        })
      );

      // Filter out any failed protocol processing
      const validDerivativesMetrics = derivativesMetrics.filter((data): data is NonNullable<typeof data> => data !== null);

      console.log(`Inserting ${validDerivativesMetrics.length} derivatives metrics to Supabase`);
      const { error } = await supabase
        .from('derivatives_metrics')
        .insert(validDerivativesMetrics);

      if (error) {
        console.error('Derivatives metrics insertion error:', error);
        throw error;
      }
    } catch (error: unknown) {
      const err = error as ErrorWithDetails;
      console.error('Derivatives data ingestion error:', {
        name: err.name || 'Unknown Error',
        message: err.message || 'An unknown error occurred',
        stack: err.stack,
        details: err.details
      });
      throw err;
    }
  }

  public async fetchTopProtocols(): Promise<Protocol[]> {
    const rawProtocols = await this.defiLlamaClient.getTopProtocols() as RawDefiLlamaProtocol[];
    return rawProtocols
      .filter(raw => raw.tvl !== null && raw.chains !== null)
      .map(raw => ({
        name: raw.name,
        tvl: raw.tvl!,
        chains: raw.chains!,
        volume24h: raw.volume24h ?? 0,
        fees24h: raw.fees24h ?? 0,
        users24h: raw.users24h ?? 0
      }));
  }

  public async fetchChainMetrics(chain: string): Promise<DuneMetrics> {
    return this.duneClient.getChainMetrics(chain);
  }

  public async fetchTopTokens(): Promise<TokenType[]> {
    try {
      // Get token data from multiple sources including DexScreener
      const [defiLlamaTokens, dexScreenerPairs] = await Promise.all([
        this.fetchDefiLlamaTokens(),
        this.dexScreenerClient.getLatestTokenProfiles()
      ]);

      // Combine and enrich token data
      const enrichedTokens = defiLlamaTokens.map(token => {
        const dexScreenerData = dexScreenerPairs.find(p => 
          p.tokenAddress.toLowerCase() === token.address.toLowerCase()
        );

        return {
          ...token,
          icon: dexScreenerData?.icon,
          description: dexScreenerData?.description,
          // Add any other DexScreener data you want to include
        };
      });

      return enrichedTokens;
    } catch (error) {
      console.error('Error fetching top tokens:', error);
      return [];
    }
  }

  private async fetchDefiLlamaTokens(): Promise<TokenType[]> {
    try {
      const response = await withRetry(
        async () => {
          // Get token prices from DefiLlama
          const response = await this.defiLlamaClient.getTokenPrices();
          
          // Transform DefiLlama data to match TokenType interface
          return Object.entries(response).map(([address, tokenData]) => ({
            address: address.toLowerCase(),
            symbol: '', // Will be enriched later
            name: '', // Will be enriched later
            price: tokenData.price || 0,
            volume24h: 0, // DefiLlama doesn't provide this in basic endpoint
            marketCap: (tokenData.price || 0) * (tokenData.totalSupply || 0),
            totalSupply: tokenData.totalSupply
          }));
        },
        3,
        2000
      );

      if (!response.length) {
        console.warn('Failed to fetch tokens from DefiLlama');
        return [];
      }

      // Get additional token metadata from DefiLlama protocols
      const protocols = await this.defiLlamaClient.getTopProtocols();
      const protocolMap = new Map(protocols.map(p => [p.name.toLowerCase(), p]));

      // Enrich token data with protocol information
      return response.map(token => {
        const protocol = protocolMap.get(token.address);
        return {
          ...token,
          symbol: protocol?.symbol || token.address.slice(0, 6).toUpperCase(),
          name: protocol?.name || token.address,
          volume24h: protocol?.volume24h || 0
        };
      });

    } catch (error) {
      console.error('Error fetching DefiLlama tokens:', error);
      return [];
    }
  }

  async fetchDEXScreenerData(): Promise<DexScreenerMetric[]> {
    try {
      const data = await this.dexScreenerClient.getLatestTokenProfiles()
      return data.map(token => ({
        name: token.name,
        symbol: token.symbol,
        price: token.price,
        volume24h: token.volume24h,
        marketCap: token.marketCap,
        address: token.tokenAddress
      }))
    } catch (error) {
      console.error('Error fetching DEXScreener data:', error)
      throw error
    }
  }

  async syncMetricsToSupabase() {
    try {
      console.log('Loading metrics data...');
      const { tokens, pairs } = loadMetricsData();
      console.log(`Loaded ${tokens.length} tokens and ${pairs.length} pairs`);
      
      // Batch process tokens
      if (tokens.length > 0) {
        console.log('Upserting tokens to Supabase...');
        const { error: tokenError } = await supabase
          .from('token_metrics')
          .upsert(
            tokens.map((token: TokenMetric) => ({
              token_address: token.address,
              symbol: token.symbol,
              name: token.name,
              price: token.price,
              volume_24h: token.volume24h,
              market_cap: token.marketCap,
              total_supply: token.totalSupply,
              timestamp: token.timestamp,
              source: 'combined' as const
            }))
          );

        if (tokenError) {
          console.error('Token upsert error:', tokenError);
          throw new ErrorWithDetails('Token sync error', tokenError);
        }
        console.log('Token upsert completed successfully');
      }

      // Batch process DEX pairs
      if (pairs.length > 0) {
        console.log('Upserting pairs to Supabase...');
        const { error: pairError } = await supabase
          .from('dexscreener_pairs')
          .upsert(
            pairs.map((pair: DexPair) => ({
              pair_address: pair.pair_address,
              chain_id: pair.chain_id,
              dex_id: pair.dex_id,
              token_1_symbol: pair.token_1_symbol,
              token_1_address: pair.token_1_address,
              token_2_symbol: pair.token_2_symbol,
              token_2_address: pair.token_2_address,
              price_usd: pair.price_usd,
              liquidity_usd: pair.liquidity_usd,
              volume_24h: pair.volume_24h,
              price_change_24h: pair.price_change_24h,
              created_at: pair.created_at
            }))
          );

        if (pairError) {
          console.error('Pair upsert error:', pairError);
          throw new ErrorWithDetails('Pair sync error', pairError);
        }
        console.log('Pair upsert completed successfully');
      }

      return {
        tokensProcessed: tokens.length,
        pairsProcessed: pairs.length
      };

    } catch (error) {
      console.error('Error syncing metrics to Supabase:', error);
      throw new ErrorWithDetails('Failed to sync metrics', error);
    }
  }

  // Add method to trigger Python ingestion
  async runPythonIngestion() {
    try {
      const { exec } = require('child_process');
      
      return new Promise((resolve, reject) => {
        exec('python3 scripts/run_ingestion.py', (error: any, stdout: string, stderr: string) => {
          if (error) {
            console.error(`Python ingestion error: ${error}`);
            reject(error);
            return;
          }
          
          console.log(`Python ingestion output: ${stdout}`);
          if (stderr) console.error(`Python ingestion stderr: ${stderr}`);
          
          resolve(stdout);
        });
      });
    } catch (error) {
      console.error('Failed to run Python ingestion:', error);
      throw error;
    }
  }

  async testSupabaseConnection() {
    try {
      console.log('Testing Supabase connection...');
      
      // Try a simple query
      const { data, error } = await supabase
        .from('token_metrics')
        .select('*')
        .limit(1);
      
      if (error) {
        console.error('Supabase connection error:', error);
        throw error;
      }
      
      console.log('Supabase connection successful:', data);
      return true;
    } catch (error) {
      console.error('Failed to connect to Supabase:', error);
      return false;
    }
  }

  // Combined method to run both ingestion and sync
  async fullIngestionProcess() {
    try {
      console.log('Starting full ingestion process...');
      
      // Test Supabase connection first
      const isConnected = await this.testSupabaseConnection();
      if (!isConnected) {
        throw new Error('Failed to connect to Supabase');
      }
      
      // Step 1: Run Python ingestion
      console.log('Running Python ingestion...');
      const pythonOutput = await this.runPythonIngestion();
      console.log('Python ingestion completed:', pythonOutput);
      
      // Verify data files exist
      const { tokens, pairs } = loadMetricsData();
      console.log('Loaded data files:', {
        tokenCount: tokens.length,
        pairsCount: pairs.length,
        tokenExample: tokens[0],
        pairExample: pairs[0]
      });
      
      // Step 2: Sync data to Supabase
      console.log('Starting Supabase sync...');
      const syncResults = await this.syncMetricsToSupabase();
      console.log('Supabase sync completed:', syncResults);
      
      // Verify data was inserted
      const { data: verifyData, error: verifyError } = await supabase
        .from('token_metrics')
        .select('*')
        .limit(1);
        
      console.log('Verification results:', { 
        hasData: verifyData && verifyData.length > 0,
        error: verifyError 
      });
      
      return {
        message: 'Full ingestion process completed',
        pythonOutput,
        ...syncResults,
        hasData: verifyData && verifyData.length > 0
      };
    } catch (error) {
      console.error('Full ingestion process failed:', error);
      throw error;
    }
  }

  async syncPerpMetricsToSupabase() {
    try {
      const perpMetricsPath = path.join(process.cwd(), 'data', 'perp_metrics.json');
      const rawData = await fs.readFile(perpMetricsPath, 'utf8');
      const metrics: PerpetualMetrics[] = JSON.parse(rawData);

      // Batch upsert to Supabase
      const { error } = await supabase
        .from('perpetual_metrics')
        .upsert(
          metrics.map(metric => ({
            symbol: metric.symbol,
            timestamp: metric.timestamp,
            funding_rate: metric.funding_rate,
            perp_volume_24h: metric.perp_volume_24h,
            open_interest: metric.open_interest,
            mark_price: metric.mark_price,
            spot_price: metric.spot_price,
            spot_volume_24h: metric.spot_volume_24h,
            liquidity: metric.liquidity,
            holder_count: metric.holder_count
          })),
          { onConflict: 'symbol,timestamp' }
        );

      if (error) throw new ErrorWithDetails('Perpetual metrics sync error', error);

      return {
        message: 'Perpetual metrics sync completed',
        recordsProcessed: metrics.length
      };
    } catch (error) {
      console.error('Error syncing perpetual metrics:', error);
      throw error;
    }
  }
} 