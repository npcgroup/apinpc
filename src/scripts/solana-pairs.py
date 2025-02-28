import requests
import os
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_dune_data():
    """Fetch data from Dune query 3084516 and save as CSV"""
    
    # API configuration
    api_key = "7nUl1BMrzLhXj7NrgAD4D1G7cBS1xvSz"
    url = "https://api.dune.com/api/v1/query/3084508/results/csv?limit=1000"
    
    # Headers for the request
    headers = {
        "X-Dune-API-Key": api_key
    }
    
    try:
        # Make the request
        logger.info("Fetching data from Dune API...")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Create data directory if it doesn't exist
        data_dir = "data/dune"
        os.makedirs(data_dir, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{data_dir}/dune_query_3084516_{timestamp}.csv"
        
        # Write the response content to a CSV file
        with open(filename, 'wb') as f:
            f.write(response.content)
            
        logger.info(f"Data successfully saved to {filename}")
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching data: {e}")
    except IOError as e:
        logger.error(f"Error saving file: {e}")

if __name__ == "__main__":
    fetch_dune_data()