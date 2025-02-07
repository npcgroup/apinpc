import { DataIngestionService } from '../services/dataIngestion'
import { CronJob } from 'cron'

async function runDataIngestion() {
  const ingestionService = new DataIngestionService()
  
  try {
    await ingestionService.ingestAllData()
    console.log('Data ingestion completed successfully')
  } catch (error) {
    console.error('Error during data ingestion:', error)
  }
}

// Run data ingestion every hour
const job = new CronJob('0 * * * *', runDataIngestion)

// Also export function for manual runs
export { runDataIngestion }

// Start the cron job if this script is run directly
if (require.main === module) {
  console.log('Starting data ingestion job...')
  job.start()
} 