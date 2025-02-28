import pandas as pd
import numpy as np
from datetime import datetime

# Define custom data types for reading the CSV with explicit float64
dtypes = {
    'token_pair': str,
    # Let pandas infer numeric types initially
    'one_day_volume': str,
    'dau_1d': str,
    'prev_volume_1d': str,
    'volume_change_1d_pct': str,
    'seven_day_volume': str,
    'dau_7d': str,
    'prev_volume_7d': str,
    'volume_change_7d_pct': str,
    'thirty_day_volume': str,
    'prev_volume_30d': str,
    'volume_change_30d_pct': str
}

def clean_numeric(val):
    """Clean numeric values, handling empty strings and invalid values"""
    if pd.isna(val) or val == '':
        return 0.0
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0

def transform_csv(input_file, output_file):
    # Read CSV with specified data types and handle bad lines
    df = pd.read_csv(input_file, 
                     dtype=dtypes,
                     on_bad_lines='warn')
    
    # Define numeric columns
    numeric_columns = ['one_day_volume', 'prev_volume_1d', 'volume_change_1d_pct',
                      'seven_day_volume', 'prev_volume_7d', 'volume_change_7d_pct',
                      'thirty_day_volume', 'prev_volume_30d', 'volume_change_30d_pct']
    
    # Convert numeric columns safely
    for col in numeric_columns:
        df[col] = df[col].apply(clean_numeric).astype('float64')
    
    # Convert DAU columns to integers, replacing NaN with 0
    dau_columns = ['dau_1d', 'dau_7d', 'dau_30d']
    for col in dau_columns:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype('Int64')
    
    # Replace infinite values with 0
    df = df.replace([np.inf, -np.inf], 0)
    
    # Sort by 7-day volume in descending order
    df = df.sort_values('seven_day_volume', ascending=False)
    
    # Round numeric columns
    df[numeric_columns] = df[numeric_columns].round(2)
    
    # Save transformed data
    df.to_csv(output_file, 
              index=False,
              float_format='%.2f',
              encoding='utf-8')
    
    return df

def main():
    input_file = 'data/solana_pair_data_20250212_175034.csv'
    output_file = 'data/transformed_dex_data_solana.csv'
    
    try:
        transformed_df = transform_csv(input_file, output_file)
        print(f"Transformed data saved to {output_file}")
        print("\nSample of transformed data:")
        print(transformed_df.head())
    except Exception as e:
        print(f"Error during transformation: {str(e)}")
        raise

if __name__ == "__main__":
    main() 