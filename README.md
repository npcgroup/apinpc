# Crypto Funding Rate Analysis Platform

This repository contains tools for analyzing cryptocurrency funding rates and price data to identify trading opportunities and market regimes.

## Overview

The platform consists of several components:
- Data collection scripts for funding rates and price history
- Streamlit dashboards for visualizing and analyzing the data
- Supabase database for storing and querying the data

## Features

- **Funding Rate Analysis**: Track and analyze funding rates across multiple exchanges
- **Price-Funding Correlation**: Analyze the relationship between price movements and funding rates
- **Term Structure Analysis**: Visualize the term structure of funding rates
- **Volatility Clustering**: Identify periods of high volatility
- **Arbitrage Efficiency**: Analyze arbitrage opportunities between exchanges
- **Funding Reversals**: Detect when funding rates reverse direction

## Getting Started

### Prerequisites

- Python 3.8+
- Supabase account
- API keys for supported exchanges (Binance, Hyperliquid)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/crypto-funding-analysis.git
cd crypto-funding-analysis
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file with the following variables:
```
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_KEY=your_supabase_key
```

4. Create the required database tables:
```bash
psql -h your_supabase_host -d postgres -U postgres -f src/scripts/create_price_history_table.sql
```

### Usage

#### Data Collection

To collect funding rate data:
```bash
python src/scripts/funding_streamlit_app_stable.py --collect-only
```

To collect price history data:
```bash
python src/scripts/populate_price_history.py --days 30 --exchange both
```

#### Running the Dashboard

To run the funding strategy dashboard:
```bash
streamlit run src/scripts/funding_strategy_dashboard.py
```

## Dashboard Components

### Funding Analysis
- Visualize funding rates over time
- Compare funding rates across exchanges
- Identify coins with extreme funding rates

### Term Structure
- Analyze the term structure of funding rates
- Identify contango and backwardation

### Volatility Clustering
- Identify periods of high volatility
- Analyze the relationship between volatility and funding rates

### Arbitrage Efficiency
- Analyze arbitrage opportunities between exchanges
- Track the efficiency of funding rate arbitrage

### Funding Reversals
- Detect when funding rates reverse direction
- Analyze the impact of funding reversals on price

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
