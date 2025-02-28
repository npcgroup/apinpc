#!/bin/bash
set -e  # Exit on error

# Function to handle errors
handle_error() {
    echo "Error: $1"
    exit 1
}

# Check Python version
python3 --version || handle_error "Python 3 is required"

# Check if Python virtual environment exists, if not create it
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv || handle_error "Failed to create virtual environment"
fi

# Activate virtual environment
source venv/bin/activate || handle_error "Failed to activate virtual environment"

# Install/upgrade pip
python -m pip install --upgrade pip || handle_error "Failed to upgrade pip"

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r src/scripts/requirements.txt || handle_error "Failed to install Python dependencies"

# Run the Node.js ingestion script
echo "Starting data ingestion..."
yarn ingest || handle_error "Data ingestion failed"

# Deactivate virtual environment
deactivate 