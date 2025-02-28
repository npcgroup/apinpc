import requests
import os
from datetime import datetime
import logging
from typing import List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_dune_queries(api_key: str, query_ids: List[int]):
    """Fetch data from multiple Dune queries and save as CSV files"""
    
    # Create data directory if it doesn't exist
    data_dir = "data/dune"
    os.makedirs(data_dir, exist_ok=True)
    
    headers = {
        "X-Dune-API-Key": api_key
    }
    
    for query_id in query_ids:
        try:
            url = f"https://api.dune.com/api/v1/query/{query_id}/results/csv?limit=1000"
            
            # Make the request
            logger.info(f"Fetching data for query {query_id}...")
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{data_dir}/dune_query_{query_id}_{timestamp}.csv"
            
            # Write the response content to a CSV file
            with open(filename, 'wb') as f:
                f.write(response.content)
                
            logger.info(f"Data successfully saved to {filename}")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching data for query {query_id}: {e}")
        except IOError as e:
            logger.error(f"Error saving file for query {query_id}: {e}")

if __name__ == "__main__":
    api_key = "7nUl1BMrzLhXj7NrgAD4D1G7cBS1xvSz"
    query_ids = [3084466, 3084516]  # Add your query IDs here
    fetch_dune_queries(api_key, query_ids)