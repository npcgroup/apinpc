#!/bin/bash

# Set environment variables
export HYBLOCK_API_KEY="your_api_key_here"
export HYBLOCK_CLIENT_ID="your_client_id_here"
export HYBLOCK_CLIENT_SECRET="your_client_secret_here"
export DB_HOST="localhost"
export DB_PORT="5432"
export DB_NAME="hyblock_data"
export DB_USER="postgres"
export DB_PASSWORD="postgres"
export LOG_LEVEL="INFO"

# Change to the hyblock_dashboard directory
cd "$(dirname "$0")"

# Run the Streamlit app
echo "Starting Hyblock Streamlit app..."
streamlit run streamlit_app.py

echo "Streamlit app stopped." 