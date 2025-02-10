"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const dotenv_1 = __importDefault(require("dotenv"));
const path_1 = require("path");
// Load environment variables from all possible locations
dotenv_1.default.config({ path: (0, path_1.resolve)(__dirname, '../.env') });
dotenv_1.default.config({ path: (0, path_1.resolve)(__dirname, '../.env.local') });
dotenv_1.default.config({ path: (0, path_1.resolve)(__dirname, '../app/.env.local') });
const dataIngestion_1 = require("../src/services/dataIngestion");
const tokens_1 = require("../src/config/tokens");
async function testDataIngestion() {
    const service = new dataIngestion_1.DataIngestionService();
    try {
        // Test Supabase connection first
        const isConnected = await service.testSupabaseConnection();
        if (!isConnected) {
            throw new Error('Failed to connect to Supabase');
        }
        // Test with POPCAT as our first token
        const testSymbol = 'POPCAT';
        const testAddress = tokens_1.TOKEN_ADDRESSES[testSymbol];
        if (!testAddress) {
            throw new Error(`No address found for symbol: ${testSymbol}`);
        }
        console.log(`Testing with ${testSymbol} (${testAddress})...`);
        const [birdeyeData, dexData, hlData] = await Promise.all([
            service.fetchBirdeyeData(testAddress).catch(error => {
                console.error('Birdeye fetch failed:', error);
                return service.getDefaultTokenData();
            }),
            service.fetchDexScreenerData(testAddress).catch(error => {
                console.error('DexScreener fetch failed:', error);
                return service.getDefaultDexData();
            }),
            service.fetchHyperliquidData(testSymbol).catch(error => {
                console.error('HyperLiquid fetch failed:', error);
                return service.getDefaultMarketData();
            })
        ]);
        const metric = {
            symbol: testSymbol,
            timestamp: new Date().toISOString(),
            mark_price: hlData.mark_price || birdeyeData.price,
            funding_rate: hlData.funding_rate,
            open_interest: hlData.open_interest,
            volume_24h: hlData.volume_24h,
            price_change_24h: birdeyeData.priceChange24h,
            total_supply: birdeyeData.totalSupply,
            market_cap: birdeyeData.marketCap,
            liquidity: Math.max(birdeyeData.liquidity, dexData.liquidity),
            spot_price: birdeyeData.price,
            spot_volume_24h: Math.max(birdeyeData.volume24h, dexData.volume24h),
            txns_24h: 0,
            holder_count: birdeyeData.holderCount,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
        };
        await service.ingestMetrics([metric]);
        console.log('✅ Test successful');
        console.log('Sample metric:', JSON.stringify(metric, null, 2));
    }
    catch (error) {
        console.error('❌ Test failed:', error instanceof Error ? error.message : error);
        process.exit(1);
    }
}
testDataIngestion();
