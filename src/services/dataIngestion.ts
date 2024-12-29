import { createClient } from '@supabase/supabase-js'
import type { Database } from '@/types/supabase'
import { 
  BirdeyeTokenData,
  HyperliquidMarketData,
  DexScreenerData,
  MetricData
} from '@/types/api'
import { env } from '@/config/env'
import birdeyedotso from '@api/birdeyedotso'
import { withRetry } from '@/utils/retryUtils'
import { spawn } from 'child_process'

export class DataIngestionService {
  private supabase;
  private rawData: {
    birdeye: Record<string, any>;
    dexscreener: Record<string, any>;
    hyperliquid: Record<string, any>;
  };

  constructor() {
    this.supabase = createClient<Database>(
      env.SUPABASE_URL,
      env.SUPABASE_SERVICE_KEY
    );
    this.rawData = {
      birdeye: {},
      dexscreener: {},
      hyperliquid: {}
    };
  }

  async fetchBirdeyeData(address: string): Promise<BirdeyeTokenData> {
    return withRetry(async () => {
      try {
        const [overviewResponse, infoResponse] = await Promise.all([
          birdeyedotso.get('/defi/token_overview', {
            params: {
              address,
              chain: 'solana'
            }
          }),
          birdeyedotso.get('/defi/token_info', {
            params: {
              address,
              chain: 'solana'
            }
          })
        ]);

        if (!overviewResponse?.data?.data || !infoResponse?.data?.data) {
          throw new Error('Invalid Birdeye API response');
        }

        const overview = overviewResponse.data.data;
        const info = infoResponse.data.data;

        const result: BirdeyeTokenData = {
          price: Number(overview.price || 0),
          volume24h: Number(overview.volume24h || 0),
          priceChange24h: Number(overview.priceChange24h || 0),
          marketCap: Number(overview.marketCap || 0),
          totalSupply: Number(info.supply || 0),
          holderCount: Number(info.holderCount || 0),
          liquidity: Number(overview.liquidity || 0)
        };

        this.rawData.birdeye[address] = {
          timestamp: new Date().toISOString(),
          overview,
          info,
          parsed: result
        };

        return result;
      } catch (error) {
        console.error('Error fetching Birdeye data:', error);
        return this.getDefaultTokenData();
      }
    });
  }

  async ingestMetrics(metrics: MetricData[]): Promise<void> {
    return withRetry(async () => {
      const timestamp = new Date().toISOString();
      
      const formattedMetrics = metrics.map(metric => ({
        ...metric,
        timestamp,
        created_at: timestamp,
        updated_at: timestamp,
        // Ensure all numeric fields are properly formatted
        mark_price: Number(metric.mark_price) || 0,
        funding_rate: Number(metric.funding_rate) || 0,
        open_interest: Number(metric.open_interest) || 0,
        volume_24h: Number(metric.volume_24h) || 0,
        price_change_24h: Number(metric.price_change_24h) || 0,
        total_supply: Number(metric.total_supply) || 0,
        market_cap: Number(metric.market_cap) || 0,
        liquidity: Number(metric.liquidity) || 0,
        spot_price: Number(metric.spot_price) || 0,
        spot_volume_24h: Number(metric.spot_volume_24h) || 0,
        txns_24h: Number(metric.txns_24h) || 0,
        holder_count: metric.holder_count ? Number(metric.holder_count) : null
      }));

      // Store raw data for debugging
      await this.saveRawData(timestamp);
      
      console.log('Attempting to insert metrics:', JSON.stringify(formattedMetrics, null, 2));
      
      const { error } = await this.supabase
        .from('perpetual_metrics')
        .insert(formattedMetrics);

      if (error) {
        console.error('Supabase error:', error);
        throw error;
      }

      console.log(`Successfully inserted ${metrics.length} metrics`);
    });
  }

  private async saveRawData(timestamp: string): Promise<void> {
    const { error } = await this.supabase
      .from('raw_data')
      .insert({
        timestamp,
        data: this.rawData
      });

    if (error) {
      console.error('Error saving raw data:', error);
    }
  }

  public getDefaultTokenData(): BirdeyeTokenData {
    return {
      price: 0,
      volume24h: 0,
      priceChange24h: 0,
      marketCap: 0,
      totalSupply: 0,
      holderCount: 0,
      liquidity: 0
    };
  }

  async testSupabaseConnection(): Promise<boolean> {
    try {
      const { error } = await this.supabase
        .from('perpetual_metrics')
        .select('id')
        .limit(1)
        .single();

      return !error;
    } catch (error) {
      console.error('Supabase connection test error:', error);
      return false;
    }
  }

  async fetchHyperliquidData(symbol: string): Promise<HyperliquidMarketData> {
    return withRetry(async () => {
      try {
        const response = await fetch(`https://api.hyperliquid.xyz/info`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ type: 'meta_and_asset_ctx' })
        });

        if (!response.ok) {
          throw new Error(`HyperLiquid API error: ${response.statusText}`);
        }

        const data = await response.json();
        const assetCtx = data.assetCtxs[symbol];

        if (!assetCtx) {
          throw new Error(`No data found for symbol ${symbol}`);
        }

        return {
          funding_rate: Number(assetCtx.funding),
          mark_price: Number(assetCtx.markPx),
          open_interest: Number(assetCtx.openInterest),
          volume_24h: Number(assetCtx.dayNtlVlm),
          oracle_price: assetCtx.oraclePx ? Number(assetCtx.oraclePx) : undefined,
          premium: assetCtx.premium ? Number(assetCtx.premium) : undefined,
          price_24h_ago: assetCtx.prevDayPx ? Number(assetCtx.prevDayPx) : undefined,
          impact_prices: assetCtx.impactPxs?.map(Number),
          mid_price: assetCtx.midPx ? Number(assetCtx.midPx) : undefined
        };
      } catch (error) {
        console.error('Error fetching HyperLiquid data:', error);
        return this.getDefaultMarketData();
      }
    });
  }

  async fetchHyperLiquidFunding(symbol: string): Promise<number> {
    const data = await this.fetchHyperliquidData(symbol);
    return data.funding_rate;
  }

  async fetchDexScreenerData(address: string): Promise<DexScreenerData> {
    return withRetry(async () => {
      try {
        const response = await fetch(`https://api.dexscreener.com/latest/dex/tokens/${address}`);
        if (!response.ok) {
          throw new Error(`DexScreener API error: ${response.statusText}`);
        }
        
        const responseData = await response.json();
        const pair = responseData.pairs?.[0];
        
        const result = {
          price: parseFloat(pair?.priceUsd || '0'),
          volume24h: parseFloat(pair?.volume?.h24 || '0'),
          liquidity: parseFloat(pair?.liquidity?.usd || '0'),
          priceChange24h: parseFloat(pair?.priceChange?.h24 || '0')
        };

        this.rawData.dexscreener[address] = result;
        return result;
      } catch (error) {
        console.error('Error fetching DexScreener data:', error);
        return this.getDefaultDexData();
      }
    });
  }

  public getDefaultMarketData(): HyperliquidMarketData {
    return {
      funding_rate: 0,
      mark_price: 0,
      open_interest: 0,
      volume_24h: 0
    };
  }

  public getDefaultDexData(): DexScreenerData {
    return {
      price: 0,
      volume24h: 0,
      liquidity: 0,
      priceChange24h: 0
    };
  }

  async testConnection(): Promise<boolean> {
    return this.testSupabaseConnection();
  }

  async fetchCombinedMarketData(symbol: string, address: string): Promise<{
    birdeye: BirdeyeTokenData;
    hyperliquid: HyperliquidMarketData;
  }> {
    return new Promise((resolve, reject) => {
      const pythonProcess = spawn('python', [
        'scripts/fetch_market_data.py',
        symbol,
        address,
        env.BIRDEYE_API_KEY
      ]);

      let dataString = '';

      pythonProcess.stdout.on('data', (data) => {
        dataString += data.toString();
      });

      pythonProcess.stderr.on('data', (data) => {
        console.error(`Python Error: ${data}`);
      });

      pythonProcess.on('close', (code) => {
        if (code !== 0) {
          reject(new Error(`Python process exited with code ${code}`));
          return;
        }

        try {
          const result = JSON.parse(dataString);
          resolve({
            birdeye: this.parseBirdeyeData(result.birdeye),
            hyperliquid: this.parseHyperliquidData(result.hyperliquid)
          });
        } catch (error) {
          reject(error);
        }
      });
    });
  }

  private parseBirdeyeData(data: any): BirdeyeTokenData {
    if (!data?.data) {
      return this.getDefaultTokenData();
    }

    const overview = data.data;
    return {
      price: Number(overview.price || 0),
      volume24h: Number(overview.volume24h || 0),
      priceChange24h: Number(overview.priceChange24h || 0),
      marketCap: Number(overview.marketCap || 0),
      totalSupply: Number(overview.totalSupply || 0),
      holderCount: Number(overview.holderCount || 0),
      liquidity: Number(overview.liquidity || 0)
    };
  }

  private parseHyperliquidData(data: any): HyperliquidMarketData {
    if (!data) {
      return this.getDefaultMarketData();
    }
    return data;
  }
} 