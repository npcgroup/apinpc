#!/bin/bash

# Set the script directory as the working directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

echo "=== Hyblock API Credentials Update ==="
echo

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found."
    echo "Please run the setup script first."
    exit 1
fi

# Get the current API credentials
CURRENT_API_KEY=$(grep "HYBLOCK_API_KEY" .env | cut -d '=' -f2)
CURRENT_BEARER_TOKEN=$(grep "HYBLOCK_BEARER_TOKEN" .env | cut -d '=' -f2)
CURRENT_CLIENT_ID=$(grep "HYBLOCK_CLIENT_ID" .env | cut -d '=' -f2)

echo "Current API key: $CURRENT_API_KEY"
echo "Current Bearer token: ${CURRENT_BEARER_TOKEN:0:20}... (truncated)"
echo "Current Client ID: $CURRENT_CLIENT_ID"
echo

# Prompt for new API key
read -p "Enter your Hyblock API key (leave empty to keep current): " NEW_API_KEY
if [ -z "$NEW_API_KEY" ]; then
    NEW_API_KEY=$CURRENT_API_KEY
    echo "Keeping current API key."
fi

# Prompt for new Bearer token
read -p "Enter your Hyblock Bearer token (leave empty to keep current): " NEW_BEARER_TOKEN
if [ -z "$NEW_BEARER_TOKEN" ]; then
    NEW_BEARER_TOKEN=$CURRENT_BEARER_TOKEN
    echo "Keeping current Bearer token."
fi

# Prompt for new Client ID
read -p "Enter your Hyblock Client ID (leave empty to keep current): " NEW_CLIENT_ID
if [ -z "$NEW_CLIENT_ID" ]; then
    NEW_CLIENT_ID=$CURRENT_CLIENT_ID
    echo "Keeping current Client ID."
fi

# Update the credentials in the .env file
sed -i '' "s/HYBLOCK_API_KEY=.*/HYBLOCK_API_KEY=$NEW_API_KEY/" .env
sed -i '' "s/HYBLOCK_BEARER_TOKEN=.*/HYBLOCK_BEARER_TOKEN=$NEW_BEARER_TOKEN/" .env
sed -i '' "s/HYBLOCK_CLIENT_ID=.*/HYBLOCK_CLIENT_ID=$NEW_CLIENT_ID/" .env

echo
echo "API credentials updated successfully."
echo

# Test the API connection
echo "Testing API connection..."
python -c "
import sys
sys.path.append('.')
import asyncio
from collector.hyblock_api import HyblockAPI

async def test_api():
    api = await HyblockAPI().initialize()
    try:
        result = await api.fetch_endpoint('market/kline', {'coin': 'SUI', 'exchange': 'BINANCE', 'timeframe': '1h'})
        if result:
            print('API connection successful!')
            print(f'Fetched data for {result[\"params\"][\"coin\"]} on {result[\"params\"][\"exchange\"]}')
        else:
            print('API connection failed. Please check your API credentials.')
    finally:
        await api.close()

asyncio.run(test_api())
"

echo
echo "=== API Credentials Update Completed ==="
echo 