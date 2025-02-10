"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.runDataIngestion = runDataIngestion;
const dataIngestion_1 = require("../services/dataIngestion");
const cron_1 = require("cron");
async function runDataIngestion() {
    const ingestionService = new dataIngestion_1.DataIngestionService();
    try {
        await ingestionService.ingestAllData();
        console.log('Data ingestion completed successfully');
    }
    catch (error) {
        console.error('Error during data ingestion:', error);
    }
}
// Run data ingestion every hour
const job = new cron_1.CronJob('0 * * * *', runDataIngestion);
// Start the cron job if this script is run directly
if (require.main === module) {
    console.log('Starting data ingestion job...');
    job.start();
}
