import time
import ccxt
import pandas as pd
import streamlit as st
import plotly.express as px


def get_binance_funding_rate(exchange, symbol):
    """
    Fetch the *latest* funding rate for a given symbol on Binance Futures.
    CCXT returns the rate as a decimal (e.g. 0.0001 = 0.01%).
    """
    try:
        rate_info = exchange.fetch_funding_rate(symbol)
        return rate_info['fundingRate']
    except Exception as e:
        st.warning(f"Error fetching funding rate for {symbol}: {e}")
        return None

def get_ohlcv_data(exchange, symbol, timeframe='1h', limit=72):
    """
    Fetch up to `limit` candles of OHLCV data for `symbol` with the given `timeframe`.
    Returns a DataFrame with columns [open, high, low, close, volume] and a datetime index.
    """
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp','open','high','low','close','volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        return df
    except Exception as e:
        st.warning(f"Error fetching OHLCV data for {symbol}: {e}")
        return pd.DataFrame()

def calculate_relative_changes(df):
    """
    Calculate the historical 24h, 48h, 72h performance from the last 72 hours of 1h candles.
    For example, performance over 24h is:
       (current_price - price_24h_ago) / price_24h_ago * 100
    """
    if df.empty:
        return {"24h_perf": None, "48h_perf": None, "72h_perf": None}
    
    current_price = df['close'].iloc[-1]
    
    def price_n_hours_ago(n):
        if len(df) < n:
            return None
        return df['close'].iloc[-n]
    
    results = {}
    for hrs in [24, 48, 72]:
        past_price = price_n_hours_ago(hrs)
        if past_price is not None:
            change_pct = (current_price - past_price) / past_price * 100
            results[f"{hrs}h_perf"] = round(change_pct, 2)
        else:
            results[f"{hrs}h_perf"] = None
    
    return results



def main():
    st.title("Funding Rate vs. Price Performance Dashboard")
    st.write("""
    This dashboard fetches the *latest* funding rate (displayed in the ticker label) and calculates 
    the historical 24h, 48h, and 72h price performance (as percentage changes) from the past 72 hours of OHLC data.
    The raw data is shown in the table below, and the bar chart plots the three performance metrics.
    Additionally, the price charts are displayed.
    """)

    # User input: symbols (e.g., for Binance Futures use "BTC/USDT:USDT")
    default_symbols = ["BTC/USDT:USDT", "ETH/USDT:USDT", "SOL/USDT:USDT", "AVAX/USDT:USDT", "LINK/USDT:USDT"]
    user_input = st.text_input("Enter symbols (comma separated):", ",".join(default_symbols))
    symbols = [s.strip() for s in user_input.split(",") if s.strip()]

    # Instantiate ccxt for Binance Futures
    binance = ccxt.binance({"enableRateLimit": True})
    binance.options['defaultType'] = 'future'

    # We'll build two datasets:
    # 1. raw_data: a table that includes funding rate and performance metrics.
    # 2. bar_chart_data: for the bar chart, only including 24h, 48h, 72h performance.
    raw_data = []
    bar_chart_data = []

    with st.spinner("Loading data..."):
        for symbol in symbols:
            # Get the current funding rate
            funding_rate = get_binance_funding_rate(binance, symbol)
            funding_rate_pct = round(funding_rate * 100, 4) if funding_rate is not None else None

            # Get up to 72 hours of 1h candles
            df_ohlc = get_ohlcv_data(binance, symbol, timeframe='1h', limit=72)
            if df_ohlc.empty:
                continue

            # Compute historical performance
            perf_dict = calculate_relative_changes(df_ohlc)

            # Build raw data table
            raw_data.append({
                "symbol": symbol,
                "funding_rate(%)": funding_rate_pct,
                "24h_perf(%)": perf_dict.get("24h_perf"),
                "48h_perf(%)": perf_dict.get("48h_perf"),
                "72h_perf(%)": perf_dict.get("72h_perf")
            })

            # For the bar chart, create a label that includes the funding rate number
            ticker_label = f"{symbol} (Fund: {funding_rate_pct}%)"
            for hrs_label in ["24h_perf", "48h_perf", "72h_perf"]:
                display_label = hrs_label.replace("_", " ").replace("perf", "Perf").strip() + " (%)"
                value = perf_dict.get(hrs_label)
                if value is not None:
                    bar_chart_data.append({
                        "Ticker": ticker_label,
                        "Metric": display_label,
                        "Value": value
                    })

            time.sleep(binance.rateLimit / 1000)  # Respect rate limit

    # Show the raw data table (as before)
    st.subheader("Raw Data")
    df_raw = pd.DataFrame(raw_data)
    st.dataframe(df_raw)

    # Create a grouped bar chart for the performance metrics only
    if bar_chart_data:
        df_bar = pd.DataFrame(bar_chart_data)
        st.subheader("Grouped Bar Chart: Price Performance (24h/48h/72h)")
        fig = px.bar(
            df_bar,
            x="Ticker",
            y="Value",
            color="Metric",
            barmode="group",
            labels={"Value": "Percentage Change (%)", "Ticker": "Ticker (Funding Rate)"},
            title="Historical Price Performance vs. Funding Rate (Displayed in Ticker Label)"
        )
        fig.update_layout(legend_title_text="Metric", xaxis={'categoryorder':'category ascending'})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No bar chart data available.")

    # Price charts: one per symbol, with y-axis scaled to the data's min and max.
    st.subheader("Price Charts (Last 72 Hours)")
    for symbol in symbols:
        df_ohlc = get_ohlcv_data(binance, symbol, timeframe='1h', limit=72)
        if df_ohlc.empty:
            st.warning(f"No OHLC data for {symbol}")
            continue

        # Create a Plotly line chart and update the y-axis to zoom between min and max.
        fig_price = px.line(
            df_ohlc, 
            x=df_ohlc.index, 
            y="close", 
            title=f"Price Chart for {symbol}"
        )
        # Set the y-axis range to the min and max of the 'close' column.
        fig_price.update_yaxes(range=[df_ohlc['close'].min(), df_ohlc['close'].max()])
        st.plotly_chart(fig_price, use_container_width=True)

if __name__ == "__main__":
    main()
