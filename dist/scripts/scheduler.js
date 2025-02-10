"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const cron_1 = require("cron");
const child_process_1 = require("child_process");
const path_1 = __importDefault(require("path"));
const INGESTION_INTERVAL = '*/5 * * * *'; // Run every 5 minutes
const runIngestion = () => {
    const scriptPath = path_1.default.resolve(__dirname, 'run-ingestion.sh');
    const process = (0, child_process_1.spawn)('bash', [scriptPath], {
        stdio: 'inherit'
    });
    process.on('error', (error) => {
        console.error('Failed to start ingestion:', error);
    });
    process.on('close', (code) => {
        if (code !== 0) {
            console.error(`Ingestion process exited with code ${code}`);
        }
        else {
            console.log('Ingestion completed successfully');
        }
    });
};
// Create and start the cron job
const job = new cron_1.CronJob(INGESTION_INTERVAL, runIngestion, null, true);
console.log('Scheduler started. Press Ctrl+C to stop.');
// Handle graceful shutdown
process.on('SIGINT', () => {
    console.log('Stopping scheduler...');
    job.stop();
    process.exit(0);
});
