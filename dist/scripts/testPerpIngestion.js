"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const dataIngestion_1 = require("../src/services/dataIngestion");
const supabaseClient_1 = require("../lib/supabaseClient");
const util_1 = require("util");
const child_process_1 = require("child_process");
const crypto_1 = require("crypto");
const exec = (0, util_1.promisify)(child_process_1.exec);
class TestPerpIngestion {
    constructor() {
        this.currentVersion = {
            version: '1.0.0',
            schemaHash: '',
            description: 'Initial perpetual metrics schema'
        };
        this.ingestionService = new dataIngestion_1.DataIngestionService();
        this.currentVersion.schemaHash = this.generateSchemaHash();
    }
    generateSchemaHash() {
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
        return (0, crypto_1.createHash)('sha256').update(schemaStructure).digest('hex');
    }
    async setupTestEnvironment() {
        const { data: version, error: versionError } = await supabaseClient_1.supabaseAdmin
            .from('perpetuals.metrics_versions')
            .upsert([this.currentVersion])
            .select()
            .single();
        if (versionError)
            throw versionError;
        // Setup data sources
        const sources = [
            { name: 'hyperliquid', version: '1.0.0' },
            { name: 'dexscreener', version: '1.0.0' },
            { name: 'helius', version: '1.0.0' },
            { name: 'combined', version: '1.0.0' }
        ];
        const { error: sourcesError } = await supabaseClient_1.supabaseAdmin
            .from('perpetuals.data_sources')
            .upsert(sources);
        if (sourcesError)
            throw sourcesError;
        return version.id;
    }
    calculateCompletenessScore(metric) {
        const requiredFields = [
            'funding_rate', 'perp_volume_24h', 'open_interest',
            'mark_price', 'spot_price', 'spot_volume_24h'
        ];
        const presentFields = requiredFields.filter(field => metric[field] != null);
        return (presentFields.length / requiredFields.length) * 100;
    }
    calculateAccuracyScore(metric) {
        let score = 100;
        // Check for reasonable value ranges
        if (metric.funding_rate > 1 || metric.funding_rate < -1)
            score -= 20;
        if (metric.mark_price <= 0)
            score -= 20;
        if (metric.perp_volume_24h < 0)
            score -= 20;
        if (metric.open_interest < 0)
            score -= 20;
        if (metric.price_change_24h > 100 || metric.price_change_24h < -100)
            score -= 20;
        return Math.max(0, score);
    }
    calculateTimelinessScore(metric) {
        const timestamp = new Date(metric.timestamp);
        const now = new Date();
        const diffMinutes = (now.getTime() - timestamp.getTime()) / (1000 * 60);
        // Score decreases as data gets older
        if (diffMinutes <= 15)
            return 100;
        if (diffMinutes <= 30)
            return 80;
        if (diffMinutes <= 60)
            return 60;
        if (diffMinutes <= 120)
            return 40;
        return 20;
    }
    calculateConsistencyScore(metric) {
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
    validateMetric(metric) {
        const errors = [];
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
            if (!isConnected)
                throw new Error('Failed to connect to Supabase');
            const versionId = await this.setupTestEnvironment();
            console.log('Running Python perpetuals ingestion...');
            const { stdout, stderr } = await exec('python3 scripts/ingest_perp_data.py');
            if (stderr)
                console.error('Python stderr:', stderr);
            const metrics = JSON.parse(stdout);
            const processedMetrics = await this.processTestData(metrics, versionId);
            await this.validateDataQuality(processedMetrics);
            console.log('Test completed successfully!');
            return processedMetrics;
        }
        catch (error) {
            console.error('Test failed:', error);
            throw error;
        }
    }
    async processTestData(metrics, versionId) {
        // Transform and store test data
        const processedMetrics = metrics.map(metric => ({
            ...metric,
            environment: 'test',
            version_id: versionId,
            raw_data: JSON.stringify(metric)
        }));
        const { error } = await supabaseClient_1.supabaseAdmin
            .from('perpetuals.perpetual_metrics')
            .upsert(processedMetrics);
        if (error)
            throw error;
        return processedMetrics;
    }
    async validateDataQuality(metrics) {
        const qualityMetrics = metrics.map(metric => ({
            metric_id: metric.id,
            completeness_score: this.calculateCompletenessScore(metric),
            accuracy_score: this.calculateAccuracyScore(metric),
            timeliness_score: this.calculateTimelinessScore(metric),
            consistency_score: this.calculateConsistencyScore(metric),
            validation_errors: this.validateMetric(metric)
        }));
        const { error } = await supabaseClient_1.supabaseAdmin
            .from('perpetuals.metrics_quality')
            .upsert(qualityMetrics);
        if (error)
            throw error;
    }
}
// Start test
const tester = new TestPerpIngestion();
tester.runTest().catch(console.error);
