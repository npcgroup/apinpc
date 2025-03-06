#!/bin/bash

# Set the script directory as the working directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

echo "=== Hyblock API Data Collector Troubleshooting ==="
echo

# Check if Docker is running
echo "Checking if Docker is running..."
docker info > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "ERROR: Docker is not running. Please start Docker and try again."
    exit 1
else
    echo "Docker is running."
fi
echo

# Check if the database container is running
echo "Checking if the database container is running..."
if docker ps | grep -q "hyblock_timescaledb"; then
    echo "Database container is running."
    
    # Check if the database is ready
    echo "Checking if the database is ready..."
    if docker exec hyblock_timescaledb pg_isready -U postgres > /dev/null 2>&1; then
        echo "Database is ready."
    else
        echo "WARNING: Database container is running but not ready."
        echo "Checking database logs..."
        docker logs hyblock_timescaledb | tail -n 20
    fi
else
    echo "WARNING: Database container is not running."
    
    # Check if the database container exists
    if docker ps -a | grep -q "hyblock_timescaledb"; then
        echo "Database container exists but is not running."
        echo "Starting the database container..."
        docker start hyblock_timescaledb
        
        if [ $? -ne 0 ]; then
            echo "ERROR: Failed to start the database container."
            echo "Checking container status..."
            docker inspect hyblock_timescaledb | grep -E "Status|Error"
        else
            echo "Database container started."
        fi
    else
        echo "Database container does not exist."
        echo "Trying to create and start the database container..."
        docker-compose up -d timescaledb
        
        if [ $? -ne 0 ]; then
            echo "ERROR: Failed to create and start the database container."
        else
            echo "Database container created and started."
        fi
    fi
fi
echo

# Check database connection settings
echo "Checking database connection settings..."
if [ -f ".env" ]; then
    echo "Current database connection settings:"
    grep "DB_" .env
    
    # Check if we're on macOS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "Detected macOS."
        
        # Check if the DB_HOST is set to localhost
        if grep -q "DB_HOST=localhost" .env; then
            echo "DB_HOST is set to localhost for macOS."
        else
            echo "WARNING: DB_HOST is not set to localhost for macOS."
            echo "This may cause connection issues."
            
            # Ask if the user wants to update the DB_HOST
            read -p "Do you want to update DB_HOST to localhost? (y/n): " UPDATE_HOST
            if [ "$UPDATE_HOST" = "y" ] || [ "$UPDATE_HOST" = "Y" ]; then
                echo "Updating DB_HOST to localhost..."
                sed -i.bak 's/DB_HOST=.*/DB_HOST=localhost/' .env
                rm -f .env.bak
                echo "DB_HOST updated."
            fi
        fi
    fi
else
    echo "ERROR: .env file not found."
    echo "Creating a default .env file..."
    
    cat > .env << EOL
# Database configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=hyblock_data
DB_USER=postgres
DB_PASSWORD=postgres

# API configuration
HYBLOCK_API_KEY=your_api_key_here

# Logging configuration
LOG_LEVEL=INFO
EOL
    
    echo ".env file created."
fi
echo

# Test database connection
echo "Testing database connection..."
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
    echo "ERROR: Database connection test failed."
    
    # Check if the database container is running
    if docker ps | grep -q "hyblock_timescaledb"; then
        echo "Database container is running."
        
        # Check database logs
        echo "Checking database logs..."
        docker logs hyblock_timescaledb | tail -n 20
        
        # Check if the database is initialized
        echo "Checking if the database is initialized..."
        docker exec hyblock_timescaledb psql -U postgres -c "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'hyblock_data');" hyblock_data
        
        if [ $? -ne 0 ]; then
            echo "WARNING: Failed to check if the database is initialized."
            echo "This may indicate that the database does not exist."
            
            # Ask if the user wants to recreate the database
            read -p "Do you want to recreate the database? (y/n): " RECREATE_DB
            if [ "$RECREATE_DB" = "y" ] || [ "$RECREATE_DB" = "Y" ]; then
                echo "Recreating the database..."
                docker exec hyblock_timescaledb psql -U postgres -c "DROP DATABASE IF EXISTS hyblock_data;"
                docker exec hyblock_timescaledb psql -U postgres -c "CREATE DATABASE hyblock_data;"
                
                echo "Initializing the database..."
                python database/init_database.py
                
                if [ $? -ne 0 ]; then
                    echo "ERROR: Failed to initialize the database."
                else
                    echo "Database initialized successfully."
                fi
            fi
        fi
    else
        echo "ERROR: Database container is not running."
    fi
else
    echo "Database connection test passed."
fi
echo

# Check API key
echo "Checking API key..."
API_KEY=$(grep "HYBLOCK_API_KEY" .env | cut -d "=" -f 2)
if [ "$API_KEY" = "your_api_key_here" ]; then
    echo "WARNING: API key is not set."
    echo "You will need to set your API key before using the data collector."
    
    # Ask if the user wants to set the API key
    read -p "Do you want to set your API key now? (y/n): " SET_API_KEY
    if [ "$SET_API_KEY" = "y" ] || [ "$SET_API_KEY" = "Y" ]; then
        echo "Please enter your Hyblock API key:"
        read NEW_API_KEY
        
        if [ -n "$NEW_API_KEY" ]; then
            echo "Updating API key..."
            sed -i.bak "s/HYBLOCK_API_KEY=.*/HYBLOCK_API_KEY=$NEW_API_KEY/" .env
            rm -f .env.bak
            echo "API key updated."
            
            # Test API connection
            echo "Testing API connection..."
            python test_api_connection.py
            
            if [ $? -ne 0 ]; then
                echo "WARNING: API connection test failed."
                echo "Please check your API key and try again."
            else
                echo "API connection test passed."
            fi
        else
            echo "No API key provided. Skipping API key update."
        fi
    fi
else
    echo "API key is set."
    
    # Test API connection
    echo "Testing API connection..."
    python test_api_connection.py
    
    if [ $? -ne 0 ]; then
        echo "WARNING: API connection test failed."
        echo "Please check your API key and try again."
    else
        echo "API connection test passed."
    fi
fi
echo

echo "=== Troubleshooting completed ==="
echo
echo "If you're still experiencing issues, please check the logs:"
echo "  - Database logs: docker logs hyblock_timescaledb"
echo "  - Collector logs: cat hyblock_collector.out"
echo "  - Application logs: cat hyblock_data.log"
echo 