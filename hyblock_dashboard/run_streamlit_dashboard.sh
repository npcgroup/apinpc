#!/bin/bash

# Set the script directory as the working directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

echo "=== Hyblock Streamlit Dashboard ==="
echo

# Check if the database is running
echo "Checking database connection..."
python -c "
import sys
from utils.database import connect_to_database

conn = connect_to_database()
if conn:
    print('Database connection successful')
    conn.close()
else:
    print('Database connection failed')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo "Database connection failed. Please make sure the database is running."
    exit 1
fi

# Start the Streamlit dashboard
echo "Starting Hyblock Streamlit dashboard..."
streamlit run streamlit_app.py --server.port 8503 --server.address 0.0.0.0

echo
echo "=== Dashboard Closed ===" 