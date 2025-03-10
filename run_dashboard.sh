#!/bin/bash

# Run Dashboard Script
# This script sets up and runs the funding strategy dashboard with enhancements

# Set up environment
echo "Setting up environment..."
source .env 2>/dev/null || echo "No .env file found, using system environment variables"

# Check if required environment variables are set
if [ -z "$NEXT_PUBLIC_SUPABASE_URL" ] || [ -z "$NEXT_PUBLIC_SUPABASE_KEY" ]; then
    echo "Error: Required environment variables NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_KEY must be set"
    echo "Please create a .env file with these variables or set them in your environment"
    exit 1
fi

# Fix database schema if needed
echo "Checking database schema..."
python src/scripts/fix_database_schema.py

# Check if the price history table exists and populate it if needed
echo "Checking price history data..."
python src/scripts/update_dashboard_price_history.py

# Check if we need to collect price data
if [ "$1" == "--collect" ] || [ "$2" == "--collect" ]; then
    echo "Collecting price history data..."
    python src/scripts/populate_price_history.py --days 30 --exchange both
fi

# Check if we need to collect funding data
if [ "$1" == "--funding" ] || [ "$2" == "--funding" ]; then
    echo "Collecting funding rate data..."
    python src/scripts/funding_streamlit_app_stable.py --collect-only
fi

# Run the dashboard
echo "Starting dashboard..."
streamlit run src/scripts/funding_strategy_dashboard.py 