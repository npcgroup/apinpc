#!/bin/bash

# Set the script directory as the working directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Check if the database is running
echo "Checking database connection..."
python -c "
import sys
sys.path.append('$SCRIPT_DIR')
from utils.database import connect_to_database
conn = connect_to_database()
if conn:
    print('Database connection successful')
    conn.close()
else:
    print('Database connection failed')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo "Database connection failed. Make sure the database is running."
    
    echo "Starting the database with Docker Compose..."
    docker-compose up -d
    
    echo "Waiting for database to be ready..."
    MAX_RETRIES=30
    RETRY_COUNT=0

    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        # Check if the database is ready
        docker exec hyblock_timescaledb pg_isready -U postgres > /dev/null 2>&1
        if [ $? -eq 0 ]; then
            echo "Database is ready."
            break
        fi
        
        echo "Waiting for database to be ready... ($(($RETRY_COUNT + 1))/$MAX_RETRIES)"
        sleep 2
        RETRY_COUNT=$(($RETRY_COUNT + 1))
    done

    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        echo "Error: Database did not become ready within the expected time."
        echo "Please check the database logs with 'docker logs hyblock_timescaledb'."
        exit 1
    fi
fi

# Start the dashboard
echo "Starting Hyblock dashboard..."
python dashboard/app.py 