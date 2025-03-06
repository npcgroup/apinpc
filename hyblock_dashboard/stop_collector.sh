#!/bin/bash

# Set the script directory as the working directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Check if the collector is running
PID_FILE="hyblock_collector.pid"
if [ ! -f "$PID_FILE" ]; then
    echo "Collector is not running (no PID file found)"
    exit 0
fi

PID=$(cat "$PID_FILE")
if ! ps -p $PID > /dev/null; then
    echo "Collector is not running (PID $PID not found)"
    rm "$PID_FILE"
    exit 0
fi

# Stop the collector
echo "Stopping Hyblock data collector (PID $PID)..."
kill $PID

# Wait for the process to terminate
MAX_WAIT=10
WAIT_COUNT=0
while ps -p $PID > /dev/null && [ $WAIT_COUNT -lt $MAX_WAIT ]; do
    echo "Waiting for collector to terminate..."
    sleep 1
    WAIT_COUNT=$((WAIT_COUNT + 1))
done

# Force kill if still running
if ps -p $PID > /dev/null; then
    echo "Collector did not terminate gracefully, force killing..."
    kill -9 $PID
    sleep 1
fi

# Check if the process is still running
if ps -p $PID > /dev/null; then
    echo "Failed to stop collector (PID $PID)"
    exit 1
else
    echo "Collector stopped successfully"
    rm "$PID_FILE"
fi

# Ask if the user wants to stop the database as well
read -p "Do you want to stop the database as well? (y/n): " STOP_DB
if [ "$STOP_DB" = "y" ] || [ "$STOP_DB" = "Y" ]; then
    echo "Stopping the database..."
    docker-compose down
    echo "Database stopped"
fi 