#!/bin/bash

# Make the script exit on any error
set -e

echo "🚀 Starting data ingestion process..."

# Run TypeScript ingestion
echo "📊 Running TypeScript ingestion..."
npm run ingest

echo "✅ Data ingestion completed!" 