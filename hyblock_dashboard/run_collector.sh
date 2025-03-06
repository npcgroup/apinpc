#!/bin/bash

# Set up colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print status messages
print_status() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

# Function to print success messages
print_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

# Function to print error messages
print_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
print_status "Script running from: $SCRIPT_DIR"

# Load environment variables from .env file if it exists
if [ -f "$SCRIPT_DIR/.env" ]; then
    print_status "Loading environment variables from .env file"
    export $(grep -v '^#' "$SCRIPT_DIR/.env" | xargs)
fi

# Set default values for environment variables if not already set
export HYBLOCK_API_KEY=${HYBLOCK_API_KEY:-"your_api_key_here"}
export HYBLOCK_CLIENT_ID=${HYBLOCK_CLIENT_ID:-"your_client_id_here"}
export HYBLOCK_CLIENT_SECRET=${HYBLOCK_CLIENT_SECRET:-"your_client_secret_here"}
export DB_HOST=${DB_HOST:-"localhost"}
export DB_PORT=${DB_PORT:-"5432"}
export DB_NAME=${DB_NAME:-"hyblock_data"}
export DB_USER=${DB_USER:-"postgres"}
export DB_PASSWORD=${DB_PASSWORD:-"postgres"}
export LOG_LEVEL=${LOG_LEVEL:-"INFO"}

# Check if API key is set
if [ "$HYBLOCK_API_KEY" = "your_api_key_here" ]; then
    print_error "HYBLOCK_API_KEY environment variable is not set properly"
    print_status "Please set the API key using: export HYBLOCK_API_KEY=your_api_key"
    exit 1
fi

# Check if client ID and secret are set
if [ "$HYBLOCK_CLIENT_ID" = "your_client_id_here" ] || [ "$HYBLOCK_CLIENT_SECRET" = "your_client_secret_here" ]; then
    print_error "HYBLOCK_CLIENT_ID or HYBLOCK_CLIENT_SECRET environment variables are not set properly"
    print_status "Please set them using: export HYBLOCK_CLIENT_ID=your_client_id"
    print_status "                        export HYBLOCK_CLIENT_SECRET=your_client_secret"
    exit 1
fi

# Check for timestamp validity in the database
print_status "Checking for timestamp validity in the database..."
python -c "
import sys
import os
sys.path.append('$SCRIPT_DIR')
from utils.database import connect_to_database, execute_query

conn = connect_to_database()
if conn:
    query = \"\"\"
        SELECT COUNT(*) 
        FROM hyblock_data 
        WHERE timestamp < '1971-01-01'
    \"\"\"
    results = execute_query(conn, query)
    if results and results[0][0] > 0:
        print(f\"{results[0][0]} records have invalid timestamps from 1970\")
        sys.exit(1)
    else:
        print(\"No invalid timestamps found\")
        sys.exit(0)
else:
    print(\"Could not connect to database\")
    sys.exit(1)
"

# Check the result of the timestamp validation
if [ $? -ne 0 ]; then
    print_error "Invalid timestamps detected in the database"
    print_status "Running timestamp fix script..."
    
    # Run the timestamp fix script
    python "$SCRIPT_DIR/fix_timestamps.py"
    
    if [ $? -ne 0 ]; then
        print_error "Failed to fix timestamps. Please investigate manually."
        print_status "You can run the fix script directly: python $SCRIPT_DIR/fix_timestamps.py"
        exit 1
    else
        print_success "Timestamps fixed successfully"
    fi
fi

# Run the data collector
print_success "Starting Hyblock data collector..."
python "$SCRIPT_DIR/data_collector.py"

# Check for timestamp issues after collection
print_status "Checking for timestamp validity after data collection..."
python -c "
import sys
import os
sys.path.append('$SCRIPT_DIR')
from utils.database import connect_to_database, execute_query

conn = connect_to_database()
if conn:
    query = \"\"\"
        SELECT COUNT(*) 
        FROM hyblock_data 
        WHERE timestamp < '1971-01-01'
    \"\"\"
    results = execute_query(conn, query)
    if results and results[0][0] > 0:
        print(f\"{results[0][0]} records have invalid timestamps from 1970\")
        sys.exit(1)
    else:
        print(\"No invalid timestamps found\")
        sys.exit(0)
else:
    print(\"Could not connect to database\")
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    print_error "New invalid timestamps detected after data collection"
    print_status "You may need to fix the data_collector.py script"
    exit 1
fi

print_success "Data collection completed." 