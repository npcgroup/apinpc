"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const dataIngestion_1 = require("../services/dataIngestion");
async function testIngestion() {
    try {
        const service = new dataIngestion_1.DataIngestionService();
        // Test connection first
        const isConnected = await service.testSupabaseConnection();
        console.log('Supabase connection test:', isConnected);
        if (!isConnected) {
            console.error('Failed to connect to Supabase. Check your credentials.');
            return;
        }
        // Run full ingestion
        const result = await service.fullIngestionProcess();
        console.log('Ingestion completed:', result);
    }
    catch (error) {
        console.error('Test failed:', error);
    }
}
testIngestion();
