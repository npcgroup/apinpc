#!/bin/bash

# Make the script exit on any error
set -e

echo "🚀 Starting data ingestion process..."

# Run TypeScript ingestion
echo "📊 Running TypeScript ingestion..."
npm run ingest

# Check if Python virtual environment exists, if not create it
if [ ! -d "app/venv" ]; then
    echo "🔧 Setting up Python virtual environment..."
    python3 -m venv app/venv
fi

# Activate virtual environment
source app/venv/bin/activate

# Install Python dependencies if needed
if [ ! -f "app/venv/lib/python3.12/site-packages/pip/_vendor/rich/_windows.py" ]; then
    echo "📦 Installing Python dependencies..."
    pip install -r requirements.txt
fi

# Run Python ingestion
echo "📊 Running Python ingestion..."
python3 scripts/ingest_perp_data.py

# Deactivate virtual environment
deactivate

echo "✅ Data ingestion completed!" 