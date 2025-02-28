import os
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
import logging
from typing import List, Dict
import numpy as np
import glob
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HistoricalDataUploader:
    def __init__(self):
        # Initialize Supabase client like in other files
        self.supabase: Client = create_client(
            os.getenv('NEXT_PUBLIC_SUPABASE_URL'),
            os.getenv('NEXT_PUBLIC_SUPABASE_KEY')
        )
        self.data_dir = "data/crypto_historical"

    def preprocess_csv_files(self):
        """Add symbol column to all CSV files based on their filename"""
        logger.info("Preprocessing CSV files to add symbol columns...")
        
        # Get all CSV files
        csv_files = glob.glob(os.path.join(self.data_dir, '*_historical.csv'))
        
        for file_path in csv_files:
            try:
                # Extract symbol from filename
                symbol = os.path.basename(file_path).replace('_historical.csv', '')
                
                # Read CSV
                df = pd.read_csv(file_path)
                
                # Add symbol column if it doesn't exist
                if 'symbol' not in df.columns:
                    df['symbol'] = symbol
                    
                    # Save back to CSV
                    df.to_csv(file_path, index=False)
                    logger.info(f"Added symbol column to {symbol}_historical.csv")
                
            except Exception as e:
                logger.error(f"Error preprocessing {file_path}: {str(e)}")

    def process_file(self, filename: str) -> None:
        symbol = filename.replace('_historical.csv', '')
        logger.info(f"Processing {symbol}")
        
        try:
            df = pd.read_csv(os.path.join(self.data_dir, filename))
            
            # Convert data types
            df['datetime'] = pd.to_datetime(df['datetime'])
            numeric_columns = ['open', 'high', 'low', 'close', 'volumefrom', 'volumeto']
            df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric)
            df['timestamp'] = df['timestamp'].astype(np.int64)
            
            # Convert to records
            records = df.to_dict('records')
            for record in records:
                for col in numeric_columns:
                    record[col] = float(record[col])
                record['datetime'] = pd.to_datetime(record['datetime']).tz_localize('UTC').isoformat()
                record['timestamp'] = int(record['timestamp'])
                record['symbol'] = symbol
            
            # Upload in smaller batches
            batch_size = 100
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                try:
                    # Using the proper table name with schema
                    data = self.supabase.table('crypto_historical.price_history').upsert(
                        batch,
                        on_conflict='symbol,timestamp'
                    ).execute()
                    
                    if hasattr(data, 'data'):
                        logger.info(f"Successfully uploaded batch {i//batch_size + 1} of {len(records)//batch_size + 1} for {symbol}")
                    else:
                        logger.error(f"Unexpected response format for {symbol}")
                        logger.error(f"Response: {data}")
                        
                except Exception as e:
                    logger.error(f"Error uploading batch for {symbol}: {str(e)}")
                    logger.error(f"Sample record: {batch[0]}")
                
                # Small delay between batches
                time.sleep(0.5)
                
        except Exception as e:
            logger.error(f"Error processing {symbol}: {str(e)}")

    def upload_all(self) -> None:
        # First preprocess all files to add symbol columns
        self.preprocess_csv_files()
        
        # Then process and upload
        files = [f for f in os.listdir(self.data_dir) if f.endswith('_historical.csv')]
        
        for file in files:
            self.process_file(file)
            # Small delay between files
            time.sleep(1)

def main():
    try:
        uploader = HistoricalDataUploader()
        uploader.upload_all()
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        raise

if __name__ == "__main__":
    main()