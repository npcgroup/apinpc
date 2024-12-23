import { CronJob } from 'cron'
import { runIngestAndStore } from './ingestAndStore'

async function startScheduler() {
  console.log('🚀 Starting perpetual metrics scheduler...')

  // Initialize last run time
  let lastRunTime = new Date()
  let isRunning = false

  // Function to run the ingestion
  async function runIngestion() {
    if (isRunning) {
      console.log('⚠️ Previous job still running, skipping this iteration')
      return
    }

    try {
      isRunning = true
      console.log(`\n📊 Starting data ingestion at ${new Date().toLocaleString()}`)
      console.log(`ℹ️ Last successful run: ${lastRunTime.toLocaleString()}`)

      await runIngestAndStore()
      
      lastRunTime = new Date()
      console.log(`✅ Data ingestion completed at ${lastRunTime.toLocaleString()}`)
    } catch (error) {
      console.error('🚨 Error during data ingestion:', error)
    } finally {
      isRunning = false
    }
  }

  // Run immediately on startup
  await runIngestion()

  // Run every 15 minutes
  const job = new CronJob('*/15 * * * *', async () => {
    await runIngestion()
  }, null, true, 'UTC')

  job.start()

  console.log('⌛ Next run scheduled for:', job.nextDate().toLocaleString())

  // Keep the process alive
  process.stdin.resume()

  // Handle graceful shutdown
  process.on('SIGINT', () => {
    console.log('\n🛑 Stopping scheduler...')
    job.stop()
    process.exit(0)
  })

  process.on('SIGTERM', () => {
    console.log('\n🛑 Stopping scheduler...')
    job.stop()
    process.exit(0)
  })
}

// Error handling for the main process
process.on('uncaughtException', (error) => {
  console.error('🚨 Uncaught Exception:', error)
})

process.on('unhandledRejection', (reason, promise) => {
  console.error('🚨 Unhandled Rejection at:', promise, 'reason:', reason)
})

// Start the scheduler with proper error handling
startScheduler().catch(error => {
  console.error('🚨 Failed to start scheduler:', error)
  process.exit(1)
})