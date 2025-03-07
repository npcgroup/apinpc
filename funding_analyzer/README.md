# Funding Rate Differential Analyzer

This application analyzes funding rate differentials between cryptocurrency exchanges (primarily Binance and HyperLiquid) to identify potential arbitrage opportunities.

## Features

- Fetches and compares funding rates from multiple exchanges
- Visualizes funding rate differentials over time
- Analyzes post-event price behavior
- Identifies potential arbitrage opportunities based on funding rate thresholds

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Set up environment variables:
   - Create a `.env` file with the following variables:
     ```
     NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
     NEXT_PUBLIC_SUPABASE_KEY=your_supabase_key
     SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
     ```

3. Run the application:
   ```
   streamlit run funding_rate_differential.py
   ```

## Deployment

To deploy this application on Streamlit Cloud:

1. Push this folder to a GitHub repository
2. Connect your repository to Streamlit Cloud
3. Set the main file path to `funding_rate_differential.py`
4. Add your environment variables in the Streamlit Cloud secrets management
5. Deploy the application

## Requirements

See `requirements.txt` for a full list of dependencies. 