import os
import pandas as pd
import glob
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def combine_historical_data():
    # Directory containing historical CSV files
    data_dir = "data/crypto_historical"
    
    # Get all CSV files
    csv_files = glob.glob(os.path.join(data_dir, '*_historical.csv'))
    
    # List to store all dataframes
    all_dfs = []
    
    logger.info(f"Found {len(csv_files)} CSV files to process")
    
    # Process each file
    for file_path in csv_files:
        try:
            # Extract symbol from filename
            symbol = os.path.basename(file_path).replace('_historical.csv', '')
            logger.info(f"Processing {symbol}")
            
            # Read CSV
            df = pd.read_csv(file_path)
            
            # Add symbol column
            df['symbol'] = symbol
            
            # Convert data types to match Supabase schema
            df['datetime'] = pd.to_datetime(df['datetime'])
            df['timestamp'] = pd.to_numeric(df['timestamp'])
            numeric_columns = ['open', 'high', 'low', 'close', 'volumefrom', 'volumeto']
            df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric)
            
            all_dfs.append(df)
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {str(e)}")
    
    # Combine all dataframes
    logger.info("Combining all dataframes...")
    combined_df = pd.concat(all_dfs, ignore_index=True)
    
    # Sort by symbol and timestamp
    combined_df = combined_df.sort_values(['symbol', 'timestamp'])
    
    # Ensure column order matches Supabase
    columns = [
        'symbol',
        'timestamp',
        'datetime',
        'open',
        'high',
        'low',
        'close',
        'volumefrom',
        'volumeto'
    ]
    combined_df = combined_df[columns]
    
    # Generate output filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"data/combined_historical_{timestamp}.csv"
    
    # Save to CSV
    combined_df.to_csv(output_file, index=False)
    logger.info(f"Saved combined data to {output_file}")
    
    # Print some stats
    logger.info("\nDataset Statistics:")
    logger.info(f"Total rows: {len(combined_df)}")
    logger.info(f"Unique symbols: {combined_df['symbol'].nunique()}")
    logger.info(f"Date range: {combined_df['datetime'].min()} to {combined_df['datetime'].max()}")
    
    return output_file

if __name__ == "__main__":
    output_file = combine_historical_data() 