import { SupabaseClient } from '@supabase/supabase-js';

export interface StrategyConfig {
  name: string;
  description: string;
  parameters: Record<string, any>;
}

export interface StrategyResult {
  timestamp: number;
  signals: Record<string, any>;
  metrics: Record<string, number>;
}

export abstract class BaseStrategy {
  protected name: string;
  protected description: string;
  protected supabaseClient: SupabaseClient;
  protected parameters: Record<string, any>;

  constructor(config: StrategyConfig, supabaseClient: SupabaseClient) {
    this.name = config.name;
    this.description = config.description;
    this.parameters = config.parameters;
    this.supabaseClient = supabaseClient;
  }

  abstract initialize(): Promise<void>;
  abstract execute(): Promise<StrategyResult>;
  abstract cleanup(): Promise<void>;

  protected async logResult(result: StrategyResult): Promise<void> {
    try {
      await this.supabaseClient
        .from('strategy_results')
        .insert({
          strategy_name: this.name,
          timestamp: new Date(result.timestamp).toISOString(),
          signals: result.signals,
          metrics: result.metrics
        });
    } catch (error) {
      console.error(`Error logging result for strategy ${this.name}:`, error);
    }
  }

  protected async fetchHistoricalData(
    table: string,
    timeStart: Date,
    timeEnd: Date
  ): Promise<any[]> {
    const { data, error } = await this.supabaseClient
      .from(table)
      .select('*')
      .gte('timestamp', timeStart.toISOString())
      .lte('timestamp', timeEnd.toISOString());

    if (error) throw error;
    return data;
  }
} 