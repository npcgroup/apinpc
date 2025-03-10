# Hyperliquid Historical Funding Rates Collector

This script fetches historical funding rates from Hyperliquid for all available assets and stores them in a Supabase table for analysis.

## Prerequisites

- Python 3.7+
- Required Python packages (install with `pip install -r requirements.txt`):
  - pandas
  - requests
  - supabase
  - python-dotenv
  - rich

## Setup

1. Make sure you have a Supabase project set up with the appropriate credentials.

2. Set up your environment variables in a `.env` file:
   ```
   NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
   NEXT_PUBLIC_SUPABASE_KEY=your_supabase_key
   ```

3. Create the required table in Supabase. You can use the `--create-table` option to get the SQL commands:
   ```bash
   python hyperliquid_historical_funding.py --create-table
   ```
   
   Then run the displayed SQL in the Supabase SQL Editor.

## Usage

Run the script with default settings (fetches 90 days of historical data for all assets):

```bash
python hyperliquid_historical_funding.py
```

### Command-line Options

- `--days`: Number of days of historical data to fetch (default: 90)
- `--assets`: Specific assets to fetch (default: all assets)
- `--create-table`: Show SQL to create the table and exit

Examples:

```bash
# Fetch 30 days of historical data
python hyperliquid_historical_funding.py --days 30

# Fetch data for specific assets
python hyperliquid_historical_funding.py --assets BTC ETH SOL

# Show SQL to create the table
python hyperliquid_historical_funding.py --create-table
```

## Output

The script will:

1. Fetch all available assets from Hyperliquid (or use the ones specified)
2. For each asset, fetch historical funding rates in chunks
3. Process the data and store it in the Supabase table
4. Log progress and results to the console and a log file

## Data Structure

The data is stored in the `hyperliquid_historical_funding` table with the following structure:

| Column       | Type      | Description                           |
|--------------|-----------|---------------------------------------|
| id           | BIGSERIAL | Primary key                           |
| asset        | TEXT      | Asset symbol (e.g., "BTC")            |
| funding_rate | FLOAT     | Funding rate value                    |
| premium      | FLOAT     | Premium value                         |
| timestamp    | BIGINT    | Unix timestamp in milliseconds        |
| datetime     | TEXT      | ISO-formatted datetime                |
| exchange     | TEXT      | Exchange name (always "Hyperliquid")  |
| created_at   | TIMESTAMP | When the record was created           |

## Scheduling

You can schedule this script to run periodically using cron or a similar scheduler:

```bash
# Run daily at midnight
0 0 * * * cd /path/to/script && python hyperliquid_historical_funding.py --days 1
```

This will fetch the last day's worth of funding rates and add them to the database.

## Troubleshooting

- If you encounter rate limiting issues, increase the `RATE_LIMIT_DELAY` constant in the script.
- For large datasets, you may need to adjust the `CHUNK_SIZE` and `MAX_WORKERS` constants.
- Check the log file `hyperliquid_historical_funding.log` for detailed error messages. 