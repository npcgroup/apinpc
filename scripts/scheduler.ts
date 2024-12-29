import { CronJob } from 'cron'
import { spawn } from 'child_process'
import path from 'path'

const INGESTION_INTERVAL = '*/5 * * * *' // Run every 5 minutes

const runIngestion = () => {
  const scriptPath = path.resolve(__dirname, 'run-ingestion.sh')
  
  const process = spawn('bash', [scriptPath], {
    stdio: 'inherit'
  })

  process.on('error', (error) => {
    console.error('Failed to start ingestion:', error)
  })

  process.on('close', (code) => {
    if (code !== 0) {
      console.error(`Ingestion process exited with code ${code}`)
    } else {
      console.log('Ingestion completed successfully')
    }
  })
}

// Create and start the cron job
const job = new CronJob(INGESTION_INTERVAL, runIngestion, null, true)

console.log('Scheduler started. Press Ctrl+C to stop.')

// Handle graceful shutdown
process.on('SIGINT', () => {
  console.log('Stopping scheduler...')
  job.stop()
  process.exit(0)
})