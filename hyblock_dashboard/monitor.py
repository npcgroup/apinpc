#!/usr/bin/env python3
"""
Hyblock System Monitor

This script monitors the health of the Hyblock data collector and Streamlit app,
and restarts them if necessary.
"""

import os
import sys
import time
import logging
import subprocess
import psutil
import signal
import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("hyblock_monitor.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("hyblock_monitor")

# Configuration
CHECK_INTERVAL = 60  # Check every 60 seconds
MAX_RESTART_ATTEMPTS = 3  # Maximum number of restart attempts
RESTART_COOLDOWN = 300  # Wait 5 minutes between restart attempts
COLLECTOR_SCRIPT = "data_collector.py"
STREAMLIT_SCRIPT = "streamlit_app.py"
COLLECTOR_LOG = "collector.log"
STREAMLIT_LOG = "streamlit.log"

# Process tracking
collector_process = None
streamlit_process = None
last_collector_restart = 0
last_streamlit_restart = 0
collector_restart_attempts = 0
streamlit_restart_attempts = 0

def is_process_running(process):
    """Check if a process is still running"""
    if process is None:
        return False
    
    try:
        return process.poll() is None
    except:
        return False

def start_collector():
    """Start the data collector process"""
    global collector_process, collector_restart_attempts, last_collector_restart
    
    logger.info("Starting data collector...")
    
    try:
        # Get the current directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Start the collector process
        collector_log = open(os.path.join(current_dir, COLLECTOR_LOG), "a")
        collector_process = subprocess.Popen(
            ["python", os.path.join(current_dir, COLLECTOR_SCRIPT)],
            stdout=collector_log,
            stderr=collector_log,
            cwd=current_dir
        )
        
        logger.info(f"Data collector started with PID {collector_process.pid}")
        collector_restart_attempts = 0
        last_collector_restart = time.time()
        return True
    except Exception as e:
        logger.error(f"Failed to start data collector: {e}")
        return False

def start_streamlit():
    """Start the Streamlit app process"""
    global streamlit_process, streamlit_restart_attempts, last_streamlit_restart
    
    logger.info("Starting Streamlit app...")
    
    try:
        # Get the current directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Start the Streamlit process
        streamlit_log = open(os.path.join(current_dir, STREAMLIT_LOG), "a")
        streamlit_process = subprocess.Popen(
            ["streamlit", "run", os.path.join(current_dir, STREAMLIT_SCRIPT)],
            stdout=streamlit_log,
            stderr=streamlit_log,
            cwd=current_dir
        )
        
        logger.info(f"Streamlit app started with PID {streamlit_process.pid}")
        streamlit_restart_attempts = 0
        last_streamlit_restart = time.time()
        return True
    except Exception as e:
        logger.error(f"Failed to start Streamlit app: {e}")
        return False

def check_collector_health():
    """Check the health of the data collector process"""
    global collector_process, collector_restart_attempts, last_collector_restart
    
    # Check if the collector process is running
    if not is_process_running(collector_process):
        logger.warning("Data collector is not running")
        
        # Check if we should restart
        current_time = time.time()
        if current_time - last_collector_restart > RESTART_COOLDOWN:
            # Reset restart attempts if it's been a while since the last restart
            collector_restart_attempts = 0
        
        if collector_restart_attempts < MAX_RESTART_ATTEMPTS:
            logger.info(f"Attempting to restart data collector (attempt {collector_restart_attempts + 1}/{MAX_RESTART_ATTEMPTS})")
            if start_collector():
                collector_restart_attempts += 1
            else:
                logger.error("Failed to restart data collector")
        else:
            logger.error(f"Maximum restart attempts ({MAX_RESTART_ATTEMPTS}) reached for data collector")
    else:
        logger.debug(f"Data collector is running with PID {collector_process.pid}")

def check_streamlit_health():
    """Check the health of the Streamlit app process"""
    global streamlit_process, streamlit_restart_attempts, last_streamlit_restart
    
    # Check if the Streamlit process is running
    if not is_process_running(streamlit_process):
        logger.warning("Streamlit app is not running")
        
        # Check if we should restart
        current_time = time.time()
        if current_time - last_streamlit_restart > RESTART_COOLDOWN:
            # Reset restart attempts if it's been a while since the last restart
            streamlit_restart_attempts = 0
        
        if streamlit_restart_attempts < MAX_RESTART_ATTEMPTS:
            logger.info(f"Attempting to restart Streamlit app (attempt {streamlit_restart_attempts + 1}/{MAX_RESTART_ATTEMPTS})")
            if start_streamlit():
                streamlit_restart_attempts += 1
            else:
                logger.error("Failed to restart Streamlit app")
        else:
            logger.error(f"Maximum restart attempts ({MAX_RESTART_ATTEMPTS}) reached for Streamlit app")
    else:
        logger.debug(f"Streamlit app is running with PID {streamlit_process.pid}")

def check_database_health():
    """Check the health of the database"""
    try:
        # Import database module
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from utils.database import connect_to_database, execute_query
        
        # Connect to the database
        conn = connect_to_database()
        if not conn:
            logger.error("Failed to connect to database")
            return False
        
        # Check if we can execute a simple query
        result = execute_query(conn, "SELECT 1")
        if result:
            logger.debug("Database is healthy")
            conn.close()
            return True
        else:
            logger.error("Failed to execute query on database")
            conn.close()
            return False
    except Exception as e:
        logger.error(f"Error checking database health: {e}")
        return False

def cleanup():
    """Clean up processes before exiting"""
    logger.info("Cleaning up processes...")
    
    if collector_process:
        try:
            collector_process.terminate()
            logger.info(f"Terminated data collector process (PID {collector_process.pid})")
        except:
            pass
    
    if streamlit_process:
        try:
            streamlit_process.terminate()
            logger.info(f"Terminated Streamlit process (PID {streamlit_process.pid})")
        except:
            pass

def signal_handler(sig, frame):
    """Handle signals to clean up before exiting"""
    logger.info(f"Received signal {sig}, shutting down...")
    cleanup()
    sys.exit(0)

def main():
    """Main function"""
    logger.info("Starting Hyblock system monitor...")
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start processes
    start_collector()
    start_streamlit()
    
    try:
        while True:
            # Check process health
            check_collector_health()
            check_streamlit_health()
            check_database_health()
            
            # Wait for next check
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down...")
    finally:
        cleanup()

if __name__ == "__main__":
    main() 