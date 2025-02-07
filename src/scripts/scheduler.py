import asyncio
import schedule
import time
import subprocess
import logging
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def run_data_pipeline():
    """Run the perpetual metrics data pipeline"""
    try:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logger.info(f"\n{'='*50}\nStarting perpetual metrics pipeline at {timestamp}\n{'='*50}")
        
        # Step 1: Run ingest_perp_data.py
        logger.info("Running perpetuals data ingestion...")
        result = subprocess.run(
            ['python', 'scripts/ingest_perp_data.py'],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            logger.error(f"Perp data ingestion failed:\n{result.stderr}")
            raise Exception("Perp data ingestion failed")
        logger.info(f"Perp data ingestion output:\n{result.stdout}")
        
        # Step 2: Process and upload to Supabase
        logger.info("Processing and uploading data to Supabase...")
        result = subprocess.run(
            ['python', 'scripts/process_debug_data.py'],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            logger.error(f"Data processing failed:\n{result.stderr}")
            raise Exception("Data processing failed")
        logger.info(f"Data processing output:\n{result.stdout}")
        
        logger.info("Data pipeline completed successfully")
        
        # Archive old debug files
        await archive_old_debug_files()
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        raise

async def archive_old_debug_files():
    """Archive debug files older than 24 hours"""
    try:
        debug_dir = Path('data/debug')
        archive_dir = debug_dir / 'archive'
        archive_dir.mkdir(exist_ok=True)
        
        current_time = datetime.now().timestamp()
        
        for file in debug_dir.glob('*_*.json'):
            # Skip files in archive directory
            if 'archive' in str(file):
                continue
                
            # Get file age in hours
            file_age = (current_time - file.stat().st_mtime) / 3600
            
            # Archive files older than 24 hours
            if file_age > 24:
                archive_path = archive_dir / file.name
                file.rename(archive_path)
                logger.info(f"Archived {file.name}")
                
    except Exception as e:
        logger.error(f"Error archiving debug files: {str(e)}")

def run_scheduler():
    """Run the scheduler"""
    logger.info("Starting perpetual metrics scheduler...")
    
    # Schedule the pipeline to run every hour
    schedule.every().hour.at(":00").do(lambda: asyncio.run(run_data_pipeline()))
    
    # Run immediately on start
    asyncio.run(run_data_pipeline())
    
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
        except Exception as e:
            logger.error(f"Scheduler error: {str(e)}")
            time.sleep(300)  # Wait 5 minutes on error before retrying

if __name__ == "__main__":
    run_scheduler() 