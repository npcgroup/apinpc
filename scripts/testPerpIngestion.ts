import { DataIngestionService } from '../services/dataIngestion';
import { supabaseAdmin } from '../lib/supabaseClient';
import { promisify } from 'util';
import { exec as execCallback } from 'child_process';
import { createHash } from 'crypto';

const exec = promisify(execCallback);

interface MetricsVersion {
  version: string;
  schemaHash: string;
  description: string;
}

interface ExecResult {
  stdout: string;
  stderr: string;
}

interface MetricQuality {
  metric_id: number;
  completeness_score: number;
  accuracy_score: number;
  timeliness_score: number;
  consistency_score: number;
  validation_errors: ValidationError[];
}

interface ValidationError {
  field: string;
  error: string;
  severity: 'warning' | 'error';
}

interface PerpMetric {
  id: number;
  symbol: string;
  timestamp: string;
  funding_rate: number;
  perp_volume_24h: number;
  open_interest: number;
  mark_price: number;
  spot_price: number;
  spot_volume_24h: number;
  liquidity: number;
  market_cap: number;
  total_supply: number;
  price_change_24h: number;
  txns_24h: number;
  holder_count?: number;
}

class TestPerpIngestion {
  private ingestionService: DataIngestionService;
  private currentVersion: MetricsVersion = {
    version: '1.0.0',
    schemaHash: '',
    description: 'Initial perpetual metrics schema'
  };

  constructor() {
    this.ingestionService = new DataIngestionService();
    this.currentVersion.schemaHash = this.generateSchemaHash();
  }

  private generateSchemaHash(): string {
    // Generate hash based on current schema structure
    const schemaStructure = JSON.stringify({
      version: '1.0.0',
      fields: [
        'funding_rate',
        'perp_volume_24h',
        'open_interest',
        'mark_price',
        'spot_price',
        'spot_volume_24h',
        'liquidity',
        'market_cap',
        'total_supply',
        'holder_count',
        'price_change_24h',
        'txns_24h'
      ]
    });

    return createHash('sha256').update(schemaStructure).digest('hex');
  }

  private async setupTestEnvironment() {
    const { data: version, error: versionError } = await supabaseAdmin
      .from('perpetuals.metrics_versions')
      .upsert([this.currentVersion])
      .select()
      .single();

    if (versionError) throw versionError;

    // Setup data sources
    const sources = [
      { name: 'hyperliquid', version: '1.0.0' },
      { name: 'dexscreener', version: '1.0.0' },
      { name: 'helius', version: '1.0.0' },
      { name: 'combined', version: '1.0.0' }
    ];

    const { error: sourcesError } = await supabaseAdmin
      .from('perpetuals.data_sources')
      .upsert(sources);

    if (sourcesError) throw sourcesError;

    return version.id;
  }

  private calculateCompletenessScore(metric: PerpMetric): number {
    const requiredFields = [
      'funding_rate', 'perp_volume_24h', 'open_interest', 
      'mark_price', 'spot_price', 'spot_volume_24h'
    ];
    const presentFields = requiredFields.filter(field => metric[field as keyof PerpMetric] != null);
    return (presentFields.length / requiredFields.length) * 100;
  }

  private calculateAccuracyScore(metric: PerpMetric): number {
    let score = 100;
    
    // Check for reasonable value ranges
    if (metric.funding_rate > 1 || metric.funding_rate < -1) score -= 20;
    if (metric.mark_price <= 0) score -= 20;
    if (metric.perp_volume_24h < 0) score -= 20;
    if (metric.open_interest < 0) score -= 20;
    if (metric.price_change_24h > 100 || metric.price_change_24h < -100) score -= 20;

    return Math.max(0, score);
  }

  private calculateTimelinessScore(metric: PerpMetric): number {
    const timestamp = new Date(metric.timestamp);
    const now = new Date();
    const diffMinutes = (now.getTime() - timestamp.getTime()) / (1000 * 60);
    
    // Score decreases as data gets older
    if (diffMinutes <= 15) return 100;
    if (diffMinutes <= 30) return 80;
    if (diffMinutes <= 60) return 60;
    if (diffMinutes <= 120) return 40;
    return 20;
  }

  private calculateConsistencyScore(metric: PerpMetric): number {
    let score = 100;
    
    // Check for data consistency
    if (Math.abs(metric.mark_price - metric.spot_price) / metric.spot_price > 0.1) {
      score -= 30; // Large price deviation
    }
    
    if (metric.perp_volume_24h > 0 && metric.open_interest === 0) {
      score -= 20; // Inconsistent volume/OI relationship
    }
    
    if (metric.market_cap > 0 && metric.total_supply === 0) {
      score -= 20; // Inconsistent market metrics
    }

    return Math.max(0, score);
  }

  private validateMetric(metric: PerpMetric): ValidationError[] {
    const errors: ValidationError[] = [];
    
    // Validate price relationships
    if (metric.mark_price <= 0) {
      errors.push({
        field: 'mark_price',
        error: 'Mark price must be positive',
        severity: 'error'
      });
    }
    
    if (metric.spot_price < 0) {
      errors.push({
        field: 'spot_price',
        error: 'Spot price cannot be negative',
        severity: 'error'
      });
    }
    
    // Validate volumes and liquidity
    if (metric.perp_volume_24h < 0) {
      errors.push({
        field: 'perp_volume_24h',
        error: 'Volume cannot be negative',
        severity: 'error'
      });
    }
    
    if (metric.open_interest < 0) {
      errors.push({
        field: 'open_interest',
        error: 'Open interest cannot be negative',
        severity: 'error'
      });
    }

    return errors;
  }

  async runTest() {
    try {
      console.log('Starting perpetuals test ingestion...');
      
      const isConnected = await this.ingestionService.testSupabaseConnection();
      if (!isConnected) throw new Error('Failed to connect to Supabase');

      const versionId = await this.setupTestEnvironment();
      
      console.log('Running Python perpetuals ingestion...');
      const { stdout, stderr }: ExecResult = await exec('python3 scripts/ingest_perp_data.py');

      if (stderr) console.error('Python stderr:', stderr);
      
      const metrics = JSON.parse(stdout) as PerpMetric[];
      const processedMetrics = await this.processTestData(metrics, versionId);
      
      await this.validateDataQuality(processedMetrics);
      
      console.log('Test completed successfully!');
      return processedMetrics;
      
    } catch (error) {
      console.error('Test failed:', error);
      throw error;
    }
  }

  private async processTestData(metrics: PerpMetric[], versionId: number) {
    // Transform and store test data
    const processedMetrics = metrics.map(metric => ({
      ...metric,
      environment: 'test',
      version_id: versionId,
      raw_data: JSON.stringify(metric)
    }));

    const { error } = await supabaseAdmin
      .from('perpetuals.perpetual_metrics')
      .upsert(processedMetrics);

    if (error) throw error;
    return processedMetrics;
  }

  private async validateDataQuality(metrics: PerpMetric[]) {
    const qualityMetrics = metrics.map(metric => ({
      metric_id: metric.id,
      completeness_score: this.calculateCompletenessScore(metric),
      accuracy_score: this.calculateAccuracyScore(metric),
      timeliness_score: this.calculateTimelinessScore(metric),
      consistency_score: this.calculateConsistencyScore(metric),
      validation_errors: this.validateMetric(metric)
    }));

    const { error } = await supabaseAdmin
      .from('perpetuals.metrics_quality')
      .upsert(qualityMetrics);

    if (error) throw error;
  }
}

// Start test
const tester = new TestPerpIngestion();
tester.runTest().catch(console.error); 