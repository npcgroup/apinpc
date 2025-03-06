import os
import sys
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API configuration
API_BASE_URL = "https://api1.hyblockcapital.com/v1"
API_KEY = os.getenv("HYBLOCK_API_KEY", "")
BEARER_TOKEN = os.getenv("HYBLOCK_BEARER_TOKEN", "")
CLIENT_ID = os.getenv("HYBLOCK_CLIENT_ID", "")

def test_curl():
    """Test the curl command directly using the requests library"""
    print("Testing curl command directly...")
    
    # Endpoint and parameters
    endpoint = "/openInterest"
    params = {
        "coin": "BTC",
        "timeframe": "15m",
        "exchange": "BINANCE",
        "sort": "asc",
        "limit": 50
    }
    
    # Headers
    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {BEARER_TOKEN}",
        "x-api-key": API_KEY
    }
    
    # Make the request
    url = f"{API_BASE_URL}{endpoint}"
    print(f"URL: {url}")
    print(f"Params: {params}")
    print(f"Headers: {headers}")
    
    try:
        response = requests.get(url, params=params, headers=headers)
        
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text[:500]}...")
        
        if response.status_code == 200:
            print("Request successful!")
            return True
        else:
            print("Request failed!")
            return False
    
    except Exception as e:
        print(f"Exception: {e}")
        return False

if __name__ == "__main__":
    test_curl() 