#!/bin/bash
# Run all components of the Hyblock Dashboard

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

# Function to check if a process is running
is_process_running() {
    if [ -z "$1" ]; then
        return 1
    fi
    
    if ps -p "$1" > /dev/null; then
        return 0
    else
        return 1
    fi
}

# Function to kill a process and its children
kill_process_tree() {
    local PARENT_PID=$1
    if [ -z "$PARENT_PID" ]; then
        return
    fi
    
    # Get all child processes
    local CHILD_PIDS=$(pgrep -P $PARENT_PID)
    
    # Kill child processes first
    for PID in $CHILD_PIDS; do
        kill_process_tree $PID
    done
    
    # Kill the parent process
    if is_process_running $PARENT_PID; then
        print_status "Killing process $PARENT_PID"
        kill -15 $PARENT_PID 2>/dev/null || kill -9 $PARENT_PID 2>/dev/null
    fi
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
export STREAMLIT_SERVER_PORT=${STREAMLIT_SERVER_PORT:-"8501"}

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

# Check if PostgreSQL is running
print_status "Checking if PostgreSQL is running..."
if ! pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER > /dev/null 2>&1; then
    print_error "PostgreSQL is not running or not accessible"
    print_status "Please start PostgreSQL and try again"
    exit 1
fi
print_success "PostgreSQL is running"

# Check if the database exists
print_status "Checking if database '$DB_NAME' exists..."
if ! psql -h $DB_HOST -p $DB_PORT -U $DB_USER -lqt | cut -d \| -f 1 | grep -qw $DB_NAME; then
    print_error "Database '$DB_NAME' does not exist"
    print_status "Creating database '$DB_NAME'..."
    if ! createdb -h $DB_HOST -p $DB_PORT -U $DB_USER $DB_NAME; then
        print_error "Failed to create database '$DB_NAME'"
        exit 1
    fi
    print_success "Database '$DB_NAME' created"
else
    print_success "Database '$DB_NAME' exists"
fi

# Variables to store process IDs
MONITOR_PID=""
COLLECTOR_PID=""
STREAMLIT_PID=""
MONITOR_DASHBOARD_PID=""

# Function to clean up processes on exit
cleanup() {
    print_status "Cleaning up processes..."
    
    if [ -n "$MONITOR_PID" ]; then
        kill_process_tree $MONITOR_PID
    fi
    
    if [ -n "$COLLECTOR_PID" ]; then
        kill_process_tree $COLLECTOR_PID
    fi
    
    if [ -n "$STREAMLIT_PID" ]; then
        kill_process_tree $STREAMLIT_PID
    fi
    
    if [ -n "$MONITOR_DASHBOARD_PID" ]; then
        kill_process_tree $MONITOR_DASHBOARD_PID
    fi
    
    print_success "All processes cleaned up"
    exit 0
}

# Set up trap to catch signals
trap cleanup SIGINT SIGTERM

# Start the monitor process
print_success "Starting Hyblock system monitor..."
python "$SCRIPT_DIR/monitor.py" > "$SCRIPT_DIR/monitor.log" 2>&1 &
MONITOR_PID=$!

# Start the monitoring dashboard
print_success "Starting Hyblock monitoring dashboard..."
streamlit run "$SCRIPT_DIR/monitor_dashboard.py" --server.port 8506 > "$SCRIPT_DIR/monitor_dashboard.log" 2>&1 &
MONITOR_DASHBOARD_PID=$!

# Start the Streamlit app
print_success "Starting Hyblock Streamlit app..."
streamlit run "$SCRIPT_DIR/streamlit_app.py" --server.port 8501 > "$SCRIPT_DIR/streamlit_app.log" 2>&1 &
STREAMLIT_PID=$!

# Wait for the monitor to start the collector and Streamlit app
print_status "Waiting for processes to start..."
sleep 5

# Check if the monitor is running
if ! is_process_running $MONITOR_PID; then
    print_error "Monitor process failed to start"
    cat "$SCRIPT_DIR/monitor.log"
    cleanup
    exit 1
fi

# Check if the monitoring dashboard is running
if ! is_process_running $MONITOR_DASHBOARD_PID; then
    print_error "Monitoring dashboard failed to start"
    cat "$SCRIPT_DIR/monitor_dashboard.log"
    cleanup
    exit 1
fi

print_success "All processes started successfully"
print_status "Monitor PID: $MONITOR_PID"
print_status "Monitoring Dashboard PID: $MONITOR_DASHBOARD_PID"
print_status "Streamlit app should be available at http://localhost:$STREAMLIT_SERVER_PORT"
print_status "Monitoring dashboard should be available at http://localhost:8506"
print_status "Press Ctrl+C to stop all processes"

# Keep the script running until interrupted
while true; do
    if ! is_process_running $MONITOR_PID; then
        print_error "Monitor process has stopped unexpectedly"
        cleanup
        exit 1
    fi
    sleep 10
done 