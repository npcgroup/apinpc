#!/bin/bash

# Set the script directory as the working directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

echo "=== Hyblock API Data Collector Setup ==="
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is required but not installed."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker Compose is required but not installed."
    exit 1
fi

echo "All prerequisites are installed."
echo

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Error: Failed to install Python dependencies."
    exit 1
fi
echo "Python dependencies installed successfully."
echo

# Make scripts executable
echo "Making scripts executable..."
chmod +x run_collector.sh stop_collector.sh run_dashboard.sh update_api_key.sh
echo "Scripts are now executable."
echo

# Check Docker connectivity
echo "Checking Docker connectivity..."
docker info > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Warning: Docker daemon is not running or not accessible."
    echo "Please start Docker and try again."
    exit 1
fi

# Check if TimescaleDB image is available locally
echo "Checking if TimescaleDB image is available locally..."
if ! docker images | grep -q "timescale/timescaledb"; then
    echo "TimescaleDB image not found locally. Trying to pull it..."
    
    # Try to pull the image
    docker pull timescale/timescaledb:latest-pg14
    if [ $? -ne 0 ]; then
        echo "Warning: Failed to pull TimescaleDB image from Docker Hub."
        echo "There might be network connectivity issues."
        
        # Ask if the user wants to continue
        read -p "Do you want to continue with the setup? (y/n): " CONTINUE
        if [ "$CONTINUE" != "y" ] && [ "$CONTINUE" != "Y" ]; then
            echo "Setup aborted."
            exit 1
        fi
    fi
fi

# Start the database
echo "Starting the database with Docker Compose..."
# Try to start just the TimescaleDB container first
docker-compose up -d timescaledb
if [ $? -ne 0 ]; then
    echo "Error: Failed to start the TimescaleDB container."
    exit 1
fi

echo "TimescaleDB started successfully."

# Try to start pgAdmin (optional) only if we have internet connectivity
if docker pull hello-world > /dev/null 2>&1; then
    echo "Starting pgAdmin (optional)..."
    docker-compose up -d pgadmin
    if [ $? -ne 0 ]; then
        echo "Warning: Failed to start pgAdmin. This is optional and won't affect the core functionality."
        echo "You can manually start it later with 'docker-compose up -d pgadmin'."
    fi
else
    echo "Skipping pgAdmin setup due to network connectivity issues."
    echo "You can manually start it later with 'docker-compose up -d pgadmin'."
fi

echo "Database services started."
echo

# Wait for the database to be ready
echo "Waiting for the database to be ready..."
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

# Give the database a bit more time to fully initialize
echo "Giving the database a bit more time to fully initialize..."
sleep 5

# Initialize the database
echo "Initializing the database..."
python database/init_database.py
if [ $? -ne 0 ]; then
    echo "Error: Failed to initialize the database."
    echo "Checking database connection details..."
    
    # Print the current database connection details
    echo "Current database connection details:"
    grep "DB_" .env
    
    echo "Checking if the database container is running..."
    docker ps | grep hyblock_timescaledb
    
    echo "Checking database logs..."
    docker logs hyblock_timescaledb | tail -n 20
    
    echo "You may need to manually fix the database connection settings in the .env file."
    exit 1
fi
echo "Database initialized successfully."
echo

# Test the database connection
echo "Testing the database connection..."
python test_db_connection.py
if [ $? -ne 0 ]; then
    echo "Error: Database connection test failed."
    exit 1
fi
echo "Database connection test passed."
echo

# Prompt for API key
echo "Please enter your Hyblock API key (leave blank to skip):"
read API_KEY

if [ -n "$API_KEY" ]; then
    # Update the .env file with the API key
    echo "Updating the .env file with the API key..."
    sed -i.bak "s/HYBLOCK_API_KEY=.*/HYBLOCK_API_KEY=$API_KEY/" .env
    rm -f .env.bak
    echo "API key updated successfully."
    
    # Test the API connection
    echo "Testing the API connection..."
    python test_api.py
    if [ $? -ne 0 ]; then
        echo "Warning: API connection test failed. Please check your API key and try again."
        echo "You can manually test the API connection later with 'python test_api_connection.py'."
    else
        echo "API connection test passed."
    fi
    echo
else
    echo "No API key provided. You will need to add your API key to the .env file before using the data collector."
    echo
fi

echo "=== Setup completed successfully! ==="
echo
echo "You can now run the data collector with:"
echo "  ./run_collector.sh"
echo
echo "And the dashboard with:"
echo "  ./run_dashboard.sh"
echo
echo "To stop the data collector, run:"
echo "  ./stop_collector.sh" 