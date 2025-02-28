import requests
import os
from datetime import datetime

def fetch_dune_data():
    # API configuration
    api_key = "7nUl1BMrzLhXj7NrgAD4D1G7cBS1xvSz"
    url = "https://api.dune.com/api/v1/query/3084508/results/csv?limit=1000"
    
    # Headers for the request
    headers = {
        "X-Dune-API-Key": api_key
    }
    
    try:
        # Make the request
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Create data directory if it doesn't exist
        data_dir = "data"
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/solana_pair_data_{timestamp}.csv"
        
        # Write the response content to a CSV file
        with open(filename, 'wb') as f:
            f.write(response.content)
            
        print(f"Data successfully saved to {filename}")
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
    except IOError as e:
        print(f"Error saving file: {e}")

if __name__ == "__main__":
    fetch_dune_data()