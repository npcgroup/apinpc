import { CronJob } from 'cron'
import { exec } from 'child_process'
import { promisify } from 'util'
import dotenv from 'dotenv'
import path from 'path'

// Load environment variables
dotenv.config({ path: path.resolve(process.cwd(), '.env.local') })
dotenv.config({ path: path.resolve(process.cwd(), '.env') })

const execAsync = promisify(exec)

// Track the state of the ingestion
let isRunning = false
let lastRunTime: Date | null = null
let consecutiveFailures = 0
const MAX_FAILURES = 3

async function runIngestion() {
  if (isRunning) {
    console.log('⚠️ Previous ingestion still running, skipping...')
    return
  }

  try {
    isRunning = true
    console.log(`\n📊 Starting data ingestion at ${new Date().toISOString()}`)
    if (lastRunTime) {
      console.log(`ℹ️ Last successful run: ${lastRunTime.toISOString()}`)
    }

    const { stdout, stderr } = await execAsync('npm run ingest')
    
    if (stderr && !stderr.includes('DeprecationWarning')) {
      console.error('⚠️ Ingestion warnings:', stderr)
    }
    
    if (stdout) {
      console.log('📝 Ingestion output:', stdout)
    }

    lastRunTime = new Date()
    consecutiveFailures = 0
    console.log(`✅ Data ingestion completed at ${lastRunTime.toISOString()}`)

  } catch (error) {
    consecutiveFailures++
    console.error('🚨 Error during ingestion:', error)
    
    if (consecutiveFailures >= MAX_FAILURES) {
      console.error(`🛑 ${MAX_FAILURES} consecutive failures reached, stopping scheduler`)
      job.stop()
      process.exit(1)
    }
  } finally {
    isRunning = false
  }
}

// Run every 5 minutes
const job = new CronJob('*/5 * * * *', runIngestion, null, false, 'UTC')

console.log('🚀 Starting perpetual metrics scheduler...')
job.start()

// Run immediately on startup
runIngestion()

// Calculate and log next run time
const nextRun = job.nextDate()
console.log('⏰ Next run scheduled for:', nextRun.toString())

// Handle graceful shutdown
process.on('SIGINT', () => {
  console.log('\n👋 Stopping scheduler gracefully...')
  job.stop()
  process.exit(0)
})

process.on('SIGTERM', () => {
  console.log('\n👋 Stopping scheduler gracefully...')
  job.stop()
  process.exit(0)
})

// Global error handlers
process.on('uncaughtException', (error) => {
  console.error('🚨 Uncaught Exception:', error)
  job.stop()
  process.exit(1)
})

process.on('unhandledRejection', (reason, promise) => {
  console.error('🚨 Unhandled Rejection at:', promise, 'reason:', reason)
})