import os
import asyncio
import aiohttp
import json
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv('.env.local')

# Initialize Supabase client
supabase: Client = create_client(
    os.getenv('NEXT_PUBLIC_SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

# Token addresses from our config
TOKEN_ADDRESSES = {
    'WIF': 'HFX1SvzjctqHgA3MdPKiJJ4UG1UhYsGUCqVe6TF2kPWL',
    'POPCAT': '5zqtEQpwRXqLtoQGADRoUbTxTLYuJNwR3obFhxkP6rbz',
    'PNUT': '6QBFX7KvyfQAFxqG4YNuHLs8GQHR3cpoc1VLGMXtYGPZ',
    'MEW': '4GZE3qZGYsdAAUnf3qn7kKQfQYQEEVjw1xqNwB4GQZH6',
    'GOAT': '8CzsSyYQR4rcQGLDYGVZ4TgYKVwXxW5K8sMKaQf2YvGq',
    'MOODENG': 'MooNPwuNcQYWHxKD3GJGHvhY3vLmX8MpJvJkKJm8Kf6',
    'CHILLGUY': 'CHiLLGUYxx7zsXWfnuBQ8YKKHxJZCn2AGRVxvpQZKvn4',
    'BRETT': 'BRETTnEb4o1s4cqvZ7j1AZHzqGCUTvaqP3KCLDzdCPf7'
}

class MetricData:
    def __init__(
        self,
        symbol: str,
        mark_price: float,
        funding_rate: float,
        open_interest: float,
        volume_24h: float,
        price_change_24h: float,
        total_supply: float,
        market_cap: float,
        liquidity: float,
        spot_price: float,
        spot_volume_24h: float,
        txns_24h: int,
        holder_count: Optional[int] = None
    ):
        self.symbol = symbol
        self.timestamp = datetime.utcnow().isoformat()
        self.mark_price = mark_price
        self.funding_rate = funding_rate
        self.open_interest = open_interest
        self.volume_24h = volume_24h
        self.price_change_24h = price_change_24h
        self.total_supply = total_supply
        self.market_cap = market_cap
        self.liquidity = liquidity
        self.spot_price = spot_price
        self.spot_volume_24h = spot_volume_24h
        self.txns_24h = txns_24h
        self.holder_count = holder_count

    def to_dict(self) -> dict:
        return {
            'symbol': self.symbol,
            'timestamp': self.timestamp,
            'mark_price': self.mark_price,
            'funding_rate': self.funding_rate,
            'open_interest': self.open_interest,
            'volume_24h': self.volume_24h,
            'price_change_24h': self.price_change_24h,
            'total_supply': self.total_supply,
            'market_cap': self.market_cap,
            'liquidity': self.liquidity,
            'spot_price': self.spot_price,
            'spot_volume_24h': self.spot_volume_24h,
            'txns_24h': self.txns_24h,
            'holder_count': self.holder_count
        }

async def fetch_birdeye_data(session: aiohttp.ClientSession, address: str) -> Dict:
    url = f"https://public-api.birdeye.so/v1/token/price?address={address}"
    headers = {
        'X-API-KEY': os.getenv('BIRDEYE_API_KEY'),
        'Accept': 'application/json'
    }
    
    async with session.get(url, headers=headers) as response:
        if response.status != 200:
            raise Exception(f"Birdeye API error: {response.status}")
        data = await response.json()
        return data['data'] if data.get('success') else {}

async def process_token(session: aiohttp.ClientSession, symbol: str, address: str) -> Optional[MetricData]:
    try:
        print(f"Processing {symbol}...")
        data = await fetch_birdeye_data(session, address)
        
        return MetricData(
            symbol=symbol,
            mark_price=data.get('price', 0),
            funding_rate=data.get('funding_rate', 0),
            open_interest=data.get('open_interest', 0),
            volume_24h=data.get('volume24h', 0),
            price_change_24h=data.get('priceChange24h', 0),
            total_supply=data.get('total_supply', 0),
            market_cap=data.get('market_cap', 0),
            liquidity=data.get('liquidity', 0),
            spot_price=data.get('price', 0),
            spot_volume_24h=data.get('volume24h', 0),
            txns_24h=data.get('txns24h', 0),
            holder_count=data.get('holder_count')
        )
    except Exception as e:
        print(f"Error processing {symbol}: {str(e)}")
        return None

async def main():
    async with aiohttp.ClientSession() as session:
        tasks = [
            process_token(session, symbol, address)
            for symbol, address in TOKEN_ADDRESSES.items()
        ]
        
        results = await asyncio.gather(*tasks)
        metrics = [r.to_dict() for r in results if r is not None]
        
        if metrics:
            try:
                response = supabase.table('perpetual_metrics').insert(metrics).execute()
                print(f"Successfully ingested {len(metrics)} metrics")
            except Exception as e:
                print(f"Error inserting metrics: {str(e)}")
        else:
            print("No metrics to ingest")

if __name__ == "__main__":
    asyncio.run(main()) 