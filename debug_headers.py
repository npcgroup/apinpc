import os
import sys
import json
import requests
from dotenv import load_dotenv

print("Script is starting...")

# Load environment variables
load_dotenv()

print("Environment variables loaded.")

# API configuration
API_BASE_URL = "https://api1.hyblockcapital.com/v1"
API_KEY = os.getenv("HYBLOCK_API_KEY", "")
BEARER_TOKEN = os.getenv("HYBLOCK_BEARER_TOKEN", "")
CLIENT_ID = os.getenv("HYBLOCK_CLIENT_ID", "")

# Print masked versions of the credentials
if API_KEY:
    print(f"API_KEY: {API_KEY[:4]}...{API_KEY[-4:] if len(API_KEY) > 8 else ''}")
else:
    print("API_KEY is not set")

if BEARER_TOKEN:
    print(f"BEARER_TOKEN: {BEARER_TOKEN[:10]}...{BEARER_TOKEN[-10:] if len(BEARER_TOKEN) > 20 else ''}")
else:
    print("BEARER_TOKEN is not set")

if CLIENT_ID:
    print(f"CLIENT_ID: {CLIENT_ID[:4]}...{CLIENT_ID[-4:] if len(CLIENT_ID) > 8 else ''}")
else:
    print("CLIENT_ID is not set")

def compare_headers():
    """Compare the exact headers between the working and non-working implementations"""
    print("Comparing headers between implementations...")
    
    # Endpoint and parameters
    endpoint = "/openInterest"
    params = {
        "coin": "BTC",
        "timeframe": "15m",
        "exchange": "BINANCE",
        "sort": "asc",
        "limit": 50
    }
    
    # Working headers from test_curl.py
    working_headers = {
        "accept": "application/json",
        "authorization": f"Bearer {BEARER_TOKEN}",
        "x-api-key": API_KEY
    }
    
    # Non-working headers from hyblock_api.py
    non_working_headers = {
        "accept": "application/json",
        "authorization": "Bearer " + BEARER_TOKEN,
        "x-api-key": API_KEY
    }
    
    # Print the exact headers for comparison
    print("\nWorking headers:")
    for key, value in working_headers.items():
        print(f"{key}: {value}")
    
    print("\nNon-working headers:")
    for key, value in non_working_headers.items():
        print(f"{key}: {value}")
    
    # Compare the headers character by character
    print("\nComparing authorization headers character by character:")
    working_auth = working_headers["authorization"]
    non_working_auth = non_working_headers["authorization"]
    
    print(f"Working auth length: {len(working_auth)}")
    print(f"Non-working auth length: {len(non_working_auth)}")
    
    # Find the first difference
    for i in range(min(len(working_auth), len(non_working_auth))):
        if working_auth[i] != non_working_auth[i]:
            print(f"First difference at position {i}:")
            print(f"Working: '{working_auth[i]}' (ASCII: {ord(working_auth[i])})")
            print(f"Non-working: '{non_working_auth[i]}' (ASCII: {ord(non_working_auth[i])})")
            break
    
    # Test both headers
    url = f"{API_BASE_URL}{endpoint}"
    
    print("\nTesting working headers:")
    try:
        response = requests.get(url, params=params, headers=working_headers)
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            print("Request successful!")
        else:
            print(f"Request failed: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")
    
    print("\nTesting non-working headers:")
    try:
        response = requests.get(url, params=params, headers=non_working_headers)
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            print("Request successful!")
        else:
            print(f"Request failed: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    compare_headers() 