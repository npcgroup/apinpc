#!/bin/bash

# Set the script directory as the working directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

echo "=== Hyblock API Data Collector Database Reset ==="
echo

# Check if Docker is running
echo "Checking if Docker is running..."
docker info > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "ERROR: Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if the database container is running
echo "Checking if the database container is running..."
if ! docker ps | grep -q "hyblock_timescaledb"; then
    echo "Database container is not running. Starting it..."
    docker-compose up -d timescaledb
    
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

# Confirm with the user
echo "WARNING: This will delete all data in the hyblock_data database."
read -p "Are you sure you want to continue? (y/n): " CONFIRM
if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
    echo "Database reset aborted."
    exit 0
fi

# Drop and recreate the database
echo "Dropping and recreating the database..."
docker exec hyblock_timescaledb psql -U postgres -c "DROP DATABASE IF EXISTS hyblock_data;"
docker exec hyblock_timescaledb psql -U postgres -c "CREATE DATABASE hyblock_data;"

if [ $? -ne 0 ]; then
    echo "Error: Failed to drop and recreate the database."
    exit 1
fi

echo "Database dropped and recreated successfully."
echo

# Initialize the database
echo "Initializing the database..."
python database/init_database.py

if [ $? -ne 0 ]; then
    echo "Error: Failed to initialize the database."
    exit 1
fi

echo "Database initialized successfully."
echo

echo "=== Database Reset Completed Successfully ==="
echo 