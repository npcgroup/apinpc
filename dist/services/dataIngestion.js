"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.DataIngestionService = void 0;
const supabaseClient_1 = require("../lib/supabaseClient");
const formatters_1 = require("../utils/formatters");
class DataIngestionService {
    constructor() {
        this.supabase = supabaseClient_1.supabase;
    }
    async testSupabaseConnection() {
        try {
            const { error } = await this.supabase.from('health').select('*');
            return !error;
        }
        catch {
            return false;
        }
    }
    async fetchBirdeyeData(address) {
        try {
            const data = {
                price: 0,
                volume: 0,
                liquidity: 0,
                priceChange24h: 0,
                totalSupply: 0,
                marketCap: 0,
                volume24h: 0,
                holderCount: 0
            };
            return {
                ...data,
                formatted: {
                    price: (0, formatters_1.formatCurrency)(data.price),
                    volume: (0, formatters_1.formatNumber)(data.volume),
                    liquidity: (0, formatters_1.formatNumber)(data.liquidity)
                }
            };
        }
        catch (error) {
            console.error('Error fetching Birdeye data:', error);
            throw error;
        }
    }
    async fetchDexScreenerData(address) {
        try {
            const data = {
                price: 0,
                volume: 0,
                liquidity: 0,
                volume24h: 0
            };
            return {
                ...data,
                formatted: {
                    price: (0, formatters_1.formatCurrency)(data.price),
                    volume: (0, formatters_1.formatNumber)(data.volume),
                    liquidity: (0, formatters_1.formatNumber)(data.liquidity)
                }
            };
        }
        catch (error) {
            console.error('Error fetching DexScreener data:', error);
            throw error;
        }
    }
    async fetchHyperliquidData() {
        try {
            const data = {
                price: 0,
                volume: 0,
                liquidity: 0,
                mark_price: 0,
                funding_rate: 0,
                open_interest: 0,
                volume_24h: 0
            };
            return {
                ...data,
                formatted: {
                    price: (0, formatters_1.formatCurrency)(data.price),
                    volume: (0, formatters_1.formatNumber)(data.volume),
                    liquidity: (0, formatters_1.formatNumber)(data.liquidity)
                }
            };
        }
        catch (error) {
            console.error('Error fetching Hyperliquid data:', error);
            throw error;
        }
    }
    async fetchCombinedMarketData(_symbol, address) {
        try {
            const [birdeye, hyperliquid] = await Promise.all([
                this.fetchBirdeyeData(address),
                this.fetchHyperliquidData()
            ]);
            return { birdeye, hyperliquid };
        }
        catch (error) {
            console.error('Error fetching combined market data:', error);
            throw error;
        }
    }
    async ingestMetrics(metrics) {
        try {
            const { error } = await this.supabase
                .from('perpetual_metrics')
                .insert(metrics);
            if (error)
                throw error;
        }
        catch (error) {
            console.error('Error ingesting metrics:', error);
            throw error;
        }
    }
}
exports.DataIngestionService = DataIngestionService;
