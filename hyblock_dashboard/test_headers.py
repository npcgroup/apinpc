import os
import sys
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("Script is starting...")

# API configuration
API_BASE_URL = "https://api1.hyblockcapital.com/v1"
API_KEY = os.getenv("HYBLOCK_API_KEY", "")
BEARER_TOKEN = os.getenv("HYBLOCK_BEARER_TOKEN", "")
CLIENT_ID = os.getenv("HYBLOCK_CLIENT_ID", "")

print(f"API_KEY: {API_KEY[:4]}...{API_KEY[-4:] if len(API_KEY) > 8 else ''}")
print(f"BEARER_TOKEN: {BEARER_TOKEN[:10]}...{BEARER_TOKEN[-10:] if len(BEARER_TOKEN) > 20 else ''}")

def test_headers():
    """Test different header formats"""
    print("Testing different header formats...")
    
    # Endpoint and parameters
    endpoint = "/openInterest"
    params = {
        "coin": "BTC",
        "timeframe": "15m",
        "exchange": "BINANCE",
        "sort": "asc",
        "limit": 50
    }
    
    # Test different header formats
    header_formats = [
        # Format 1: Using f-string (from test_curl.py)
        {
            "name": "f-string",
            "headers": {
                "accept": "application/json",
                "authorization": f"Bearer {BEARER_TOKEN}",
                "x-api-key": API_KEY
            }
        },
        # Format 2: Using string concatenation with space
        {
            "name": "string concatenation with space",
            "headers": {
                "accept": "application/json",
                "authorization": "Bearer " + BEARER_TOKEN,
                "x-api-key": API_KEY
            }
        },
        # Format 3: Using string formatting with space
        {
            "name": "string formatting with space",
            "headers": {
                "accept": "application/json",
                "authorization": "Bearer {}".format(BEARER_TOKEN),
                "x-api-key": API_KEY
            }
        },
        # Format 4: Using string concatenation with no space
        {
            "name": "string concatenation with no space",
            "headers": {
                "accept": "application/json",
                "authorization": "Bearer" + BEARER_TOKEN,
                "x-api-key": API_KEY
            }
        }
    ]
    
    # Make requests with different header formats
    url = f"{API_BASE_URL}{endpoint}"
    
    for format_info in header_formats:
        name = format_info["name"]
        headers = format_info["headers"]
        
        print(f"\nTesting format: {name}")
        print(f"Headers: {headers}")
        
        try:
            response = requests.get(url, params=params, headers=headers)
            
            print(f"Status code: {response.status_code}")
            
            if response.status_code == 200:
                print("Request successful!")
                print(f"Response: {response.text[:200]}...")
            else:
                print(f"Request failed: {response.text}")
        
        except Exception as e:
            print(f"Exception: {e}")

# Run the test
print("Running header tests...")
test_headers()
print("Script completed.") 