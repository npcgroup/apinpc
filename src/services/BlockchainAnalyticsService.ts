import { createClient, SupabaseClient } from '@supabase/supabase-js';
import { 
  Asset, AssetType, Chain, DataProvider, Environment,
  TokenMetrics, PerpetualMetrics, NFTMetrics, ProtocolMetrics,
  DataQuality, AuditLog 
} from '../types/blockchain-analytics';
import { 
  DefiLlamaClient, DuneClient, BitqueryClient,
  FootprintClient, TheGraphClient, HyperliquidClient 
} from '../utils/clients';

export class BlockchainAnalyticsService {
  private supabase: SupabaseClient;
  private providers: Map<DataProvider, any>;
  private environment: Environment;

  constructor(
    supabaseUrl: string,
    supabaseKey: string,
    environment: Environment = Environment.PRODUCTION
  ) {
    this.supabase = createClient(supabaseUrl, supabaseKey);
    this.environment = environment;
    this.providers = new Map();
    this.initializeProviders();
  }

  private initializeProviders() {
    const config = {
      defillamaKey: process.env.DEFILLAMA_API_KEY,
      duneKey: process.env.DUNE_API_KEY,
      bitqueryKey: process.env.BITQUERY_API_KEY,
      footprintKey: process.env.FOOTPRINT_API_KEY,
      thegraphKey: process.env.THEGRAPH_API_KEY,
      hyperliquidKey: process.env.HYPERLIQUID_API_KEY
    };

    this.providers.set(DataProvider.DEFILLAMA, new DefiLlamaClient(config.defillamaKey));
    this.providers.set(DataProvider.DUNE, new DuneClient(config.duneKey));
    this.providers.set(DataProvider.BITQUERY, new BitqueryClient(config.bitqueryKey));
    this.providers.set(DataProvider.FOOTPRINT, new FootprintClient(config.footprintKey));
    this.providers.set(DataProvider.THEGRAPH, new TheGraphClient(config.thegraphKey));
    this.providers.set(DataProvider.HYPERLIQUID, new HyperliquidClient());
  }

  async ingestTokenMetrics(asset: Asset): Promise<void> {
    try {
      const metrics = await this.aggregateTokenMetrics(asset);
      await this.storeTokenMetrics(metrics);
      await this.updateDataQuality(DataProvider.DEFILLAMA, 'token_metrics');
    } catch (error) {
      await this.logError('token_metrics', asset.id, error);
      throw error;
    }
  }

  async ingestPerpetualMetrics(asset: Asset): Promise<void> {
    try {
      const metrics = await this.aggregatePerpetualMetrics(asset);
      await this.storePerpetualMetrics(metrics);
      await this.updateDataQuality(DataProvider.HYPERLIQUID, 'perpetual_metrics');
    } catch (error) {
      await this.logError('perpetual_metrics', asset.id, error);
      throw error;
    }
  }

  async ingestNFTMetrics(asset: Asset): Promise<void> {
    try {
      const metrics = await this.aggregateNFTMetrics(asset);
      await this.storeNFTMetrics(metrics);
      await this.updateDataQuality(DataProvider.BITQUERY, 'nft_metrics');
    } catch (error) {
      await this.logError('nft_metrics', asset.id, error);
      throw error;
    }
  }

  private async aggregateTokenMetrics(asset: Asset): Promise<TokenMetrics> {
    const defiLlama = this.providers.get(DataProvider.DEFILLAMA);
    const dune = this.providers.get(DataProvider.DUNE);
    
    // Fetch data from multiple sources
    const [defiLlamaData, duneData] = await Promise.all([
      defiLlama.getTokenMetrics(asset.contract_address),
      dune.getTokenMetrics(asset.contract_address)
    ]);

    // Combine and validate data
    const metrics: TokenMetrics = {
      id: 0, // Will be set by DB
      asset_id: asset.id,
      environment: this.environment,
      timestamp: new Date(),
      source_id: defiLlama.id,
      price: this.validatePrice(defiLlamaData.price, duneData.price),
      volume_24h: defiLlamaData.volume24h || duneData.volume24h,
      market_cap: defiLlamaData.marketCap,
      total_supply: defiLlamaData.totalSupply,
      holder_count: duneData.holders,
      raw_data: {
        defiLlama: defiLlamaData,
        dune: duneData
      },
      created_at: new Date()
    };

    return this.validateMetrics(metrics);
  }

  private async aggregatePerpetualMetrics(asset: Asset): Promise<PerpetualMetrics> {
    const hyperliquid = this.providers.get(DataProvider.HYPERLIQUID);
    const dexscreener = this.providers.get(DataProvider.BITQUERY);

    // Fetch data from multiple sources
    const [hlData, dexData] = await Promise.all([
      hyperliquid.getMarketMetrics(asset.symbol),
      dexscreener.getPerpetualMetrics(asset.symbol)
    ]);

    const metrics: PerpetualMetrics = {
      id: 0,
      asset_id: asset.id,
      environment: this.environment,
      timestamp: new Date(),
      source_id: hyperliquid.id,
      funding_rate: hlData.funding_rate,
      open_interest: hlData.open_interest,
      volume_24h: hlData.volume_24h,
      long_positions: hlData.long_positions,
      short_positions: hlData.short_positions,
      liquidations_24h: hlData.liquidations_24h,
      raw_data: {
        hyperliquid: hlData,
        dexscreener: dexData
      },
      created_at: new Date()
    };

    return this.validateMetrics(metrics);
  }

  private async aggregateNFTMetrics(asset: Asset): Promise<NFTMetrics> {
    const bitquery = this.providers.get(DataProvider.BITQUERY);
    const footprint = this.providers.get(DataProvider.FOOTPRINT);

    // Fetch data from multiple sources
    const [bitqueryData, footprintData] = await Promise.all([
      bitquery.getNFTMetrics(asset.contract_address),
      footprint.getNFTMetrics(asset.contract_address)
    ]);

    const metrics: NFTMetrics = {
      id: 0,
      asset_id: asset.id,
      environment: this.environment,
      timestamp: new Date(),
      source_id: bitquery.id,
      floor_price: bitqueryData.floor_price,
      volume_24h: bitqueryData.volume_24h,
      sales_count: bitqueryData.sales_count,
      holder_count: bitqueryData.holder_count,
      listed_count: bitqueryData.listed_count,
      raw_data: {
        bitquery: bitqueryData,
        footprint: footprintData
      },
      created_at: new Date()
    };

    return this.validateMetrics(metrics);
  }

  private async updateDataQuality(provider: DataProvider, metricType: string): Promise<void> {
    const quality: DataQuality = {
      id: 0,
      source_id: this.providers.get(provider).id,
      metric_type: metricType,
      timestamp: new Date(),
      completeness_score: await this.calculateCompletenessScore(provider, metricType),
      accuracy_score: await this.calculateAccuracyScore(provider, metricType),
      timeliness_score: await this.calculateTimelinessScore(provider, metricType),
      consistency_score: await this.calculateConsistencyScore(provider, metricType),
      created_at: new Date()
    };

    const { error } = await this.supabase
      .from('blockchain_analytics.data_quality')
      .upsert(quality);

    if (error) throw error;
  }

  private async logError(table: string, recordId: number, error: any): Promise<void> {
    const auditLog: AuditLog = {
      id: 0,
      table_name: table,
      record_id: recordId,
      action: 'ERROR',
      old_data: null,
      new_data: { error: error.message, stack: error.stack },
      created_at: new Date()
    };

    await this.supabase
      .from('blockchain_analytics.audit_log')
      .insert(auditLog);
  }

  private validateMetrics<T>(metrics: T): T {
    // Implement validation logic
    return metrics;
  }

  private validatePrice(price1: number, price2: number): number {
    // Implement price validation logic
    const deviation = Math.abs(price1 - price2) / ((price1 + price2) / 2);
    if (deviation > 0.05) {
      // Log price discrepancy
      console.warn(`Price deviation of ${deviation * 100}% detected`);
    }
    return (price1 + price2) / 2;
  }

  private async calculateCompletenessScore(provider: DataProvider, metricType: string): Promise<number> {
    // Implement completeness calculation
    return 0.95;
  }

  private async calculateAccuracyScore(provider: DataProvider, metricType: string): Promise<number> {
    // Implement accuracy calculation
    return 0.90;
  }

  private async calculateTimelinessScore(provider: DataProvider, metricType: string): Promise<number> {
    // Implement timeliness calculation
    return 0.85;
  }

  private async calculateConsistencyScore(provider: DataProvider, metricType: string): Promise<number> {
    // Implement consistency calculation
    return 0.88;
  }

  private async storeTokenMetrics(metrics: TokenMetrics): Promise<void> {
    const { error } = await this.supabase
      .from('blockchain_analytics.token_metrics')
      .upsert(metrics);

    if (error) throw error;
  }

  private async storePerpetualMetrics(metrics: PerpetualMetrics): Promise<void> {
    const { error } = await this.supabase
      .from('blockchain_analytics.perpetual_metrics')
      .upsert(metrics);

    if (error) throw error;
  }

  private async storeNFTMetrics(metrics: NFTMetrics): Promise<void> {
    const { error } = await this.supabase
      .from('blockchain_analytics.nft_metrics')
      .upsert(metrics);

    if (error) throw error;
  }

  // Add more implementation methods...
} 