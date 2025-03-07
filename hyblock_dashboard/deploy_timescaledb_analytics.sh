#!/bin/bash
# Deployment script for TimescaleDB Analytics Platform

echo "===== TimescaleDB Analytics Platform Deployment ====="
echo "This script will set up TimescaleDB and configure advanced analytics"

# Step 1: Ensure TimescaleDB extension is installed
echo "Step 1: Ensuring TimescaleDB extension is installed..."
psql -h localhost -d hyblock_data -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"

# Step 2: Convert tables to hypertables
echo "Step 2: Converting tables to hypertables..."
psql -h localhost -d hyblock_data -f scripts/convert_all_tables.sql

# Step 3: Set up continuous aggregates
echo "Step 3: Setting up continuous aggregates..."
psql -h localhost -d hyblock_data -f scripts/setup_simplified_aggregates.sql

# Step 4: Generate MCP configuration
echo "Step 4: Generating MCP configuration..."
node scripts/generate_mcp_config.js

# Step 5: Restart MCP server (if applicable)
echo "Step 5: Restarting MCP server..."
# Add commands to restart your MCP server here if needed

echo "===== Deployment Complete ====="
echo "TimescaleDB Analytics Platform is now ready to use!"
echo "You can access the advanced analytics through the MCP interface." 