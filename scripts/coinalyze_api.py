from typing import List, Dict, Any, Optional
import time
import requests
from dataclasses import dataclass
from urllib.parse import urljoin

@dataclass
class HistoricalParams:
    symbols: List[str]
    interval: str
    from_timestamp: int
    to_timestamp: int
    convert_to_usd: bool = False


 
class CoinAlyzeAPI:
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.coinalyze.net/v1/",
        rate_limit: int = 40
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.rate_limit = rate_limit
        self.last_request_time = 0

    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Base request handler with rate limiting
        """
        now = time.time() * 1000  # Convert to milliseconds
        time_since_last = now - self.last_request_time

        # Enforce rate limit (40 requests/minute)
        if time_since_last < 1500:  # 60s/40 = 1.5s between requests
            time.sleep((1500 - time_since_last) / 1000)  # Convert back to seconds

        url = urljoin(self.base_url, endpoint)

        if params:
            # Convert list parameters to comma-separated strings
            processed_params = {
                k: ','.join(v) if isinstance(v, list) else str(v)
                for k, v in params.items()
            }
        else:
            processed_params = {}

        headers = {
            'x-api-key': self.api_key,
            'Content-Type': 'application/json'
        }

        response = requests.get(url, headers=headers, params=processed_params)
        self.last_request_time = time.time() * 1000

        if not response.ok:
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', '60'))
                time.sleep(retry_after)
                return self._make_request(endpoint, params)
            raise Exception(f"API Error {response.status_code}: {response.text}")

        return response.json()

    def get_supported_exchanges(self) -> List[Dict[str, str]]:
        """
        Get list of supported exchanges
        """
        return self._make_request('exchanges')

    def get_current_funding_rates(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """
        Get current funding rates for specified symbols
        """
        return self._make_request('funding-rate', {'symbols': symbols})

    def get_ohlcv_history(self, params: HistoricalParams) -> List[Dict[str, Any]]:
        """
        Get OHLCV history for specified parameters
        """
        request_params = {
            'symbols': params.symbols,
            'interval': params.interval,
            'from': params.from_timestamp,
            'to': params.to_timestamp
        }
        return self._make_request('ohlcv-history', request_params)

    def get_open_interest_history(self, params: HistoricalParams) -> List[Dict[str, Any]]:
        """
        Get open interest history for specified parameters
        """
        request_params = {
            'symbols': params.symbols,
            'interval': params.interval,
            'from': params.from_timestamp,
            'to': params.to_timestamp,
            'convert_to_usd': str(params.convert_to_usd).lower()
        }
        return self._make_request('open-interest-history', request_params) 
print(CoinAlyzeAPI.get_current_funding_rates(['BTCUSDT_PERP']))