#!/bin/bash
# Stop all components of the Hyblock Dashboard

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

# Stop the data collector
if [ -f "$SCRIPT_DIR/collector.pid" ]; then
    COLLECTOR_PID=$(cat "$SCRIPT_DIR/collector.pid")
    if ps -p $COLLECTOR_PID > /dev/null; then
        print_status "Stopping data collector (PID: $COLLECTOR_PID)"
        kill $COLLECTOR_PID
        print_success "Data collector stopped"
    else
        print_status "Data collector is not running"
    fi
    rm -f "$SCRIPT_DIR/collector.pid"
else
    print_status "No collector PID file found"
fi

# Stop the Streamlit dashboard
if [ -f "$SCRIPT_DIR/streamlit.pid" ]; then
    STREAMLIT_PID=$(cat "$SCRIPT_DIR/streamlit.pid")
    if ps -p $STREAMLIT_PID > /dev/null; then
        print_status "Stopping Streamlit dashboard (PID: $STREAMLIT_PID)"
        kill $STREAMLIT_PID
        print_success "Streamlit dashboard stopped"
    else
        print_status "Streamlit dashboard is not running"
    fi
    rm -f "$SCRIPT_DIR/streamlit.pid"
else
    print_status "No Streamlit PID file found"
fi

print_success "All components stopped successfully" 