# Hyblock Data Dashboard

A comprehensive dashboard for visualizing and analyzing cryptocurrency data from the Hyblock API.

## Overview

This system consists of three main components:

1. **Data Collector**: Fetches data from the Hyblock API and stores it in a PostgreSQL database.
2. **Streamlit Dashboard**: Visualizes the data in an interactive web interface.
3. **System Monitor**: Ensures that all components are running properly and restarts them if necessary.

## Requirements

- Python 3.8+
- PostgreSQL 12+
- TimescaleDB extension for PostgreSQL
- Streamlit
- psycopg2
- requests
- pandas
- plotly
- dotenv

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/hyblock-dashboard.git
   cd hyblock-dashboard
   ```

2. Create a virtual environment and install dependencies:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Set up PostgreSQL and TimescaleDB:
   - Install PostgreSQL and TimescaleDB
   - Create a database for the application
   - Create a user with appropriate permissions

4. Create a `.env` file with your configuration:
   ```
   HYBLOCK_API_KEY=your_api_key_here
   HYBLOCK_CLIENT_ID=your_client_id_here
   HYBLOCK_CLIENT_SECRET=your_client_secret_here
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=hyblock_data
   DB_USER=postgres
   DB_PASSWORD=your_password_here
   LOG_LEVEL=INFO
   STREAMLIT_SERVER_PORT=8501
   ```

## Usage

### Starting the System

To start all components at once, run:

```
./run_all.sh
```

This script will:
1. Check if PostgreSQL is running
2. Create the database if it doesn't exist
3. Start the system monitor
4. The monitor will start the data collector and Streamlit dashboard

The Streamlit dashboard will be available at http://localhost:8501 (or the port specified in your .env file).

### Starting Components Individually

If you prefer to start components individually:

1. Start the data collector:
   ```
   python data_collector.py
   ```

2. Start the Streamlit dashboard:
   ```
   streamlit run streamlit_app.py
   ```

3. Start the system monitor:
   ```
   python monitor.py
   ```

## Troubleshooting

### Database Connection Issues

If you encounter database connection issues:

1. Check if PostgreSQL is running:
   ```
   pg_isready -h localhost -p 5432
   ```

2. Verify your database credentials in the `.env` file.

3. Check the database logs:
   ```
   tail -f hyblock_data.log
   ```

### API Connection Issues

If you encounter issues connecting to the Hyblock API:

1. Verify your API credentials in the `.env` file.

2. Check the data collector logs:
   ```
   tail -f collector.log
   ```

3. Ensure your internet connection is stable.

### Streamlit Dashboard Issues

If the Streamlit dashboard is not working properly:

1. Check the Streamlit logs:
   ```
   tail -f streamlit.log
   ```

2. Verify that the data collector is running and populating the database.

3. Restart the Streamlit dashboard:
   ```
   streamlit run streamlit_app.py
   ```

## Architecture

The system follows a simple architecture:

1. The data collector fetches data from the Hyblock API and stores it in the PostgreSQL database.
2. The Streamlit dashboard reads data from the database and visualizes it.
3. The system monitor ensures that all components are running properly.

### Database Schema

The main table in the database is `hyblock_data` with the following schema:

- `id`: Primary key
- `endpoint`: The API endpoint from which the data was fetched
- `coin`: The cryptocurrency symbol
- `exchange`: The exchange from which the data was fetched
- `timeframe`: The timeframe of the data (e.g., 1m, 5m, 15m, 1h, 4h, 1d)
- `market_cap_category`: The market cap category of the coin
- `timestamp`: The timestamp of the data
- `data`: The actual data in JSON format

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 