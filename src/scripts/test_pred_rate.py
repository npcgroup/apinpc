import os
import requests
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

url = "https://api.coinalyze.net/v1/predicted-funding-rate/symbols=BTCUSDT_PERP"
headers = {
    "X-API-KEY": os.getenv("COINALYZE_API_KEY")  # Changed to match their API spec
}

response = requests.get(url, headers=headers)

if response.status_code == 200:
    predicted_funding_rates = response.json()
    print(predicted_funding_rates)
else:
    print(f"Error {response.status_code}: {response.text}")