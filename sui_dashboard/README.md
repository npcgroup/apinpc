# SUI Dashboard

Real-time monitoring of SUI token prices and liquidity across exchanges.

## Features

- Real-time price tracking for SUI tokens across multiple exchanges (Binance CEX, Bluefin DEX)
- Liquidity monitoring with detailed visualization
- Arbitrage opportunity detection and tracking with profit estimates
- Interactive dashboard with customizable auto-refresh capability
- TimescaleDB integration for efficient time-series data storage
- CCXT integration for reliable exchange API access
- Robust error handling and database connection management
- Beautiful, modern UI with responsive design

## Project Structure

```
sui_dashboard/
├── collector/                # Data collection modules
│   ├── sui_data_collector.py # Main collector script
│   ├── sui_price_collector.py # Price data collection
│   └── sui_liquidity_collector.py # Liquidity data collection
├── dashboard/               # Streamlit dashboard
│   └── app.py               # Dashboard application
├── database/                # Database scripts
│   └── init_database.py     # Database initialization
├── utils/                   # Utility modules
│   └── database.py          # Database connection utilities
├── .env                     # Environment variables
├── requirements.txt         # Python dependencies
├── docker-compose.yml       # Docker Compose configuration
├── test_db_connection.py    # Database connection test
├── test_db_init.py          # Database initialization test
├── run_collector.sh         # Script to run the data collector
├── stop_collector.sh        # Script to stop the data collector
├── run_dashboard.sh         # Script to run the dashboard
└── setup_and_run.sh         # Script to set up and run everything
```

## Prerequisites

- Python 3.8+
- Docker and Docker Compose (for running TimescaleDB)
- Internet connection for API access

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd sui_dashboard
   ```

2. Install the required Python packages:
   ```
   pip install -r requirements.txt
   ```

3. Set up TimescaleDB using Docker:
   ```
   docker-compose up -d
   ```
   
   This will start a TimescaleDB container with the following configuration:
   - Database name: `sui_data`
   - Username: `postgres`
   - Password: `postgres`
   - Port: `5432`

   If you need to customize these settings, edit the `docker-compose.yml` file and update the `.env` file accordingly.

## Usage

### Setting Up and Running Everything

The easiest way to get started is to run the setup script:

```
./setup_and_run.sh
```

This will:
1. Start TimescaleDB in a Docker container
2. Install Python dependencies
3. Test the database connection
4. Initialize the database (with TimescaleDB extension check)
5. Start the data collector
6. Launch the Streamlit dashboard

### Starting the Data Collector Separately

If you want to run just the data collector:

```
./run_collector.sh
```

This will:
1. Check if database tables exist and initialize them if needed
2. Start the data collector in the background
3. Save the process ID for later termination

### Stopping the Data Collector

To stop the data collector, run:

```
./stop_collector.sh
```

### Running the Dashboard Separately

To start just the Streamlit dashboard:

```
./run_dashboard.sh
```

This will launch the dashboard in your default web browser at `http://localhost:8501`.

### Testing Database Connection

To verify that your database connection is working properly:

```
./test_db_connection.py
```

This will:
1. Test the connection to the database
2. Verify that the TimescaleDB extension is installed
3. Run a simple test query to ensure everything is working

## Dashboard Features

### Enhanced UI

The dashboard now features a modern, clean design with:
- Intuitive tabbed interface
- Status indicators for database connection and collector
- Responsive layout for various screen sizes
- Custom styling for better readability

### Real-time Data Visualization

- **Price Chart**: Track CEX vs DEX prices in real-time
- **Spread Chart**: Visualize price spread between exchanges with percentage difference
- **Liquidity Chart**: Monitor liquidity levels over time with logarithmic scale
- **Arbitrage Table**: Detailed view of arbitrage opportunities with estimated profits and costs

### User Controls

- **Customizable Time Period**: Select from 15 minutes up to 24 hours of data
- **Flexible Auto-Refresh**: Adjust refresh interval from 5 to 60 seconds
- **Manual Refresh Option**: Force refresh data on demand
- **Data Export**: Download arbitrage opportunity data as CSV

### Status Monitoring

- **Database Connection Status**: Shows connection health, TimescaleDB availability, and table existence
- **Data Collector Status**: Indicates whether the collector is currently running
- **Error Handling**: Informative error messages with troubleshooting suggestions

## Advanced Features

### Robust Database Management

- **Automatic TimescaleDB Extension Check**: Verifies the extension is properly installed
- **Transaction Management**: Proper transaction handling for data integrity
- **Connection Pooling**: Efficient connection handling with automatic reconnection
- **Batch Processing**: Optimized data insertion for high-volume scenarios

### Error Handling and Recovery

- **Automatic Retries**: Retry logic for temporary database connection issues
- **Graceful Degradation**: Dashboard will show partial data if some queries fail
- **Detailed Logging**: Comprehensive logging for troubleshooting
- **Helpful Error Messages**: User-friendly error messages with recovery suggestions

## Customization

- Edit the `.env` file to change database connection settings or API keys
- Modify the collection interval in `sui_data_collector.py` (default: 15 seconds)
- Adjust dashboard auto-refresh settings in the UI
- Add additional exchanges by implementing new collector functions

## Troubleshooting

### Database Connection Issues

- **TimescaleDB Not Running**: 
  ```
  docker ps | grep timescaledb
  ```
  If not listed, start it with:
  ```
  docker-compose up -d
  ```

- **Connection Test Failure**:
  ```
  python3 test_db_connection.py
  ```
  Check your `.env` file for correct credentials.

- **Missing TimescaleDB Extension**:
  The application will try to create it automatically, but if it fails, you may need to:
  ```sql
  CREATE EXTENSION IF NOT EXISTS timescaledb;
  ```

### Data Collection Issues

- Check the log file:
  ```
  cat collector/sui_collector.out

  tail -f collector/sui_collector.out
  ```

- Restart the collector:
  ```
  ./stop_collector.sh
  ./run_collector.sh
  ```

### Dashboard Issues

- Verify Streamlit is installed:
  ```
  pip install streamlit
  ```

- Check for port conflicts:
  ```
  netstat -tuln | grep 8501
  ```

- Try running with a different port:
  ```
  streamlit run dashboard/app.py --server.port 8502
  ```

## License

This project is licensed under the MIT License - see the LICENSE file for details. 