import pandas as pd
from datetime import datetime, timedelta
import logging
import os
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def filter_csv_by_date_range():
    """
    Filter the CSV file by date range and ensure all tokens have complete price data
    """
    # Define input and output files
    input_file = "data/latest_price_data_20250227_135723.csv"  # Use the specific file name
    
    # Check if input file exists
    if not os.path.exists(input_file):
        logger.error(f"Input file not found: {input_file}")
        return None
    
    # Generate output filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"data/filtered_data_{timestamp}.csv"
    
    logger.info(f"Input file: {input_file}")
    logger.info(f"Output file will be: {output_file}")
    
    # Define the date range
    start_date = datetime(2025, 2, 18)
    end_date = datetime(2025, 2, 27, 23, 59, 59)  # End of day on Feb 27
    
    logger.info(f"Filtering records between {start_date.strftime('%Y-%m-%d')} and {end_date.strftime('%Y-%m-%d')}")
    
    try:
        # Read the entire CSV file
        logger.info("Reading the input file...")
        df = pd.read_csv(input_file)
        logger.info(f"Read {len(df)} rows from input file")
        
        # Check for zero or NaN prices in the input file
        zero_prices = df[(df['close'] == 0) | df['close'].isna()]
        if not zero_prices.empty:
            logger.warning(f"Found {len(zero_prices)} rows with zero or NaN prices in the input file")
            logger.warning(f"Symbols with zero prices: {zero_prices['symbol'].unique().tolist()}")
        
        # Convert datetime column to datetime type
        df['datetime'] = pd.to_datetime(df['datetime'])
        
        # Filter by date range
        logger.info("Filtering by date range...")
        filtered_df = df[(df['datetime'] >= start_date) & (df['datetime'] <= end_date)]
        logger.info(f"Filtered to {len(filtered_df)} rows")
        
        # Check if we have data
        if filtered_df.empty:
            logger.error("No data found in the specified date range")
            return None
        
        # Get unique symbols
        symbols = filtered_df['symbol'].unique()
        logger.info(f"Found {len(symbols)} unique symbols")
        
        # Create a list to store DataFrames with complete data
        complete_dfs = []
        
        # Process each symbol
        for symbol in symbols:
            logger.info(f"Processing symbol: {symbol}")
            
            # Get data for this symbol
            symbol_df = filtered_df[filtered_df['symbol'] == symbol].copy()
            
            # Check for zero prices
            zero_price_rows = symbol_df[(symbol_df['close'] == 0) | symbol_df['close'].isna()]
            if not zero_price_rows.empty:
                logger.warning(f"Symbol {symbol} has {len(zero_price_rows)} rows with zero or NaN prices")
            
            # Sort by timestamp
            symbol_df = symbol_df.sort_values('timestamp')
            
            # Check if we have enough data
            if len(symbol_df) <= 1:
                logger.warning(f"Symbol {symbol} has only {len(symbol_df)} data points, skipping gap filling")
                complete_dfs.append(symbol_df)
                continue
            
            # Calculate time differences between consecutive rows
            symbol_df['time_diff'] = symbol_df['timestamp'].diff()
            
            # Standard time difference for hourly data (in seconds)
            hourly_diff = 3600
            
            # Find gaps (where time difference is more than hourly)
            gaps = symbol_df[symbol_df['time_diff'] > hourly_diff * 1.5]
            
            if not gaps.empty:
                logger.info(f"Found {len(gaps)} gaps in data for {symbol}")
                
                # Create a complete time series with hourly intervals
                min_time = symbol_df['timestamp'].min()
                max_time = symbol_df['timestamp'].max()
                
                # Create a complete range of hourly timestamps
                complete_timestamps = list(range(int(min_time), int(max_time) + hourly_diff, hourly_diff))
                
                # Create a DataFrame with the complete timestamps
                complete_df = pd.DataFrame({'timestamp': complete_timestamps})
                
                # Convert timestamps to datetime for merging
                complete_df['datetime'] = complete_df['timestamp'].apply(
                    lambda x: datetime.utcfromtimestamp(x).isoformat()
                )
                
                # Merge with the original data
                merged_df = pd.merge(complete_df, symbol_df.drop('time_diff', axis=1), 
                                     on=['timestamp', 'datetime'], how='left')
                
                # Fill symbol column
                merged_df['symbol'] = symbol
                
                # Check for zero or NaN values before filling
                for col in ['open', 'high', 'low', 'close', 'volumefrom', 'volumeto']:
                    # Replace zeros with NaN to avoid propagating zeros during filling
                    merged_df[col] = merged_df[col].replace(0, np.nan)
                    
                    # Forward fill and backward fill
                    merged_df[col] = merged_df[col].ffill().bfill()
                    
                    # If still NaN (could happen if all values are NaN), use the last known good value from the original data
                    if merged_df[col].isna().any():
                        last_good_value = symbol_df[symbol_df[col].notna() & (symbol_df[col] != 0)][col].iloc[-1] if not symbol_df[symbol_df[col].notna() & (symbol_df[col] != 0)].empty else None
                        if last_good_value is not None:
                            merged_df[col] = merged_df[col].fillna(last_good_value)
                        else:
                            # If no good value exists, use a reasonable default
                            if col in ['open', 'high', 'low', 'close']:
                                # For price columns, use the average of non-zero values across all symbols
                                avg_price = filtered_df[filtered_df[col] > 0][col].mean()
                                merged_df[col] = merged_df[col].fillna(avg_price)
                            else:
                                # For volume columns, use 0
                                merged_df[col] = merged_df[col].fillna(0)
                
                # Verify no NaN or zero prices remain
                zero_after = merged_df[(merged_df['close'] == 0) | merged_df['close'].isna()]
                if not zero_after.empty:
                    logger.warning(f"Symbol {symbol} still has {len(zero_after)} rows with zero or NaN prices after filling")
                    
                    # Try one more approach - use the mean of non-zero values for this symbol
                    for col in ['open', 'high', 'low', 'close']:
                        non_zero_mean = merged_df[merged_df[col] > 0][col].mean()
                        if not np.isnan(non_zero_mean):
                            merged_df[col] = merged_df[col].replace(0, non_zero_mean)
                            merged_df[col] = merged_df[col].fillna(non_zero_mean)
                
                complete_dfs.append(merged_df)
            else:
                # No gaps found, but still check for zero prices
                for col in ['open', 'high', 'low', 'close']:
                    # Replace zeros with the mean of non-zero values
                    non_zero_mean = symbol_df[symbol_df[col] > 0][col].mean()
                    if not np.isnan(non_zero_mean):
                        symbol_df[col] = symbol_df[col].replace(0, non_zero_mean)
                
                symbol_df = symbol_df.drop('time_diff', axis=1)
                complete_dfs.append(symbol_df)
        
        # Combine all complete DataFrames
        if complete_dfs:
            result_df = pd.concat(complete_dfs, ignore_index=True)
            
            # Sort by symbol and timestamp
            result_df = result_df.sort_values(['symbol', 'timestamp'])
            
            # Ensure all required columns are present
            required_columns = [
                'symbol', 'timestamp', 'datetime', 'open', 'high', 'low', 'close', 'volumefrom', 'volumeto'
            ]
            
            # Select only the required columns
            result_df = result_df[required_columns]
            
            # Final check for zero or NaN prices
            final_zeros = result_df[(result_df['close'] == 0) | result_df['close'].isna()]
            if not final_zeros.empty:
                logger.warning(f"Final dataset still has {len(final_zeros)} rows with zero or NaN prices")
                logger.warning(f"Symbols with zero prices: {final_zeros['symbol'].unique().tolist()}")
                
                # Last resort - replace any remaining zeros with the global mean
                global_mean = result_df[result_df['close'] > 0]['close'].mean()
                for col in ['open', 'high', 'low', 'close']:
                    result_df[col] = result_df[col].replace(0, global_mean)
                    result_df[col] = result_df[col].fillna(global_mean)
            
            # Write to output file
            logger.info(f"Writing {len(result_df)} rows to output file: {output_file}")
            result_df.to_csv(output_file, index=False)
            
            # Verify the output file
            if os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                logger.info(f"Output file created: {output_file} (Size: {file_size} bytes)")
                
                # Read a sample from the output file
                sample_df = pd.read_csv(output_file, nrows=5)
                logger.info(f"Sample from output file:\n{sample_df}")
                
                # Count rows per symbol
                symbol_counts = result_df['symbol'].value_counts()
                logger.info(f"Rows per symbol (top 10):\n{symbol_counts.head(10)}")
                
                # Check for symbols with few data points
                low_data_symbols = symbol_counts[symbol_counts < 24*5].index.tolist()  # Less than 5 days of hourly data
                if low_data_symbols:
                    logger.warning(f"Symbols with limited data points: {low_data_symbols}")
                
                # Final verification - check for zero prices in the output file
                verification_df = pd.read_csv(output_file)
                zero_in_output = verification_df[(verification_df['close'] == 0) | verification_df['close'].isna()]
                if not zero_in_output.empty:
                    logger.error(f"Output file still has {len(zero_in_output)} rows with zero or NaN prices")
                    logger.error(f"Symbols with zero prices in output: {zero_in_output['symbol'].unique().tolist()}")
                else:
                    logger.info("Verification successful: No zero or NaN prices in the output file")
            else:
                logger.error(f"Output file was not created: {output_file}")
        else:
            logger.error("No complete data frames were created")
            return None
        
        return output_file
    
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

if __name__ == "__main__":
    output_file = filter_csv_by_date_range()
    if output_file:
        logger.info(f"Script completed successfully. Output file: {output_file}")
    else:
        logger.error("Script failed to create output file")