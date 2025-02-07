import requests
import json
import sys
import os
from typing import Dict, Any

def fetch_birdeye_data(address: str, api_key: str) -> Dict[str, Any]:
    url = f"https://public-api.birdeye.so/v1/defi/token_overview?address={address}"
    
    headers = {
        "accept": "application/json",
        "x-api-key": api_key,
        "x-chain": "solana"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching Birdeye data: {e}", file=sys.stderr)
        return None

def fetch_hyperliquid_data(symbol: str) -> Dict[str, Any]:
    url = "https://api.hyperliquid.xyz/info"
    
    payload = {
        "type": "meta_and_asset_ctx"
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        
        # Extract relevant market data for the symbol
        asset_ctx = next((ctx for ctx in data.get('assetCtxs', []) 
                         if ctx.get('name') == symbol), None)
        
        if asset_ctx:
            return {
                "funding_rate": float(asset_ctx.get('funding', 0)),
                "mark_price": float(asset_ctx.get('markPx', 0)),
                "open_interest": float(asset_ctx.get('openInterest', 0)),
                "volume_24h": float(asset_ctx.get('dayNtlVlm', 0))
            }
        return None
    except Exception as e:
        print(f"Error fetching HyperLiquid data: {e}", file=sys.stderr)
        return None

def main():
    if len(sys.argv) != 4:
        print("Usage: python fetch_market_data.py <symbol> <address> <birdeye_api_key>")
        sys.exit(1)
    
    symbol = sys.argv[1]
    address = sys.argv[2]
    api_key = sys.argv[3]
    
    # Fetch data from both sources
    birdeye_data = fetch_birdeye_data(address, api_key)
    hyperliquid_data = fetch_hyperliquid_data(symbol)
    
    # Combine the data
    result = {
        "birdeye": birdeye_data,
        "hyperliquid": hyperliquid_data
    }
    
    # Print JSON output for Node.js to parse
    print(json.dumps(result))

if __name__ == "__main__":
    main() 