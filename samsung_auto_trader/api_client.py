import time
from typing import Dict, Any, Optional
import requests
from samsung_auto_trader.config import Config
from samsung_auto_trader.auth import TokenManager
from samsung_auto_trader.logger import logger

class KISApiClient:
    """Base API client for interacting with the Korea Investment & Securities REST API."""

    def __init__(self, token_manager: Optional[TokenManager] = None) -> None:
        self.token_manager = token_manager or TokenManager()

    def _get_headers(self, tr_id: str) -> Dict[str, str]:
        """Prepares standard headers required by KIS Open API."""
        token = self.token_manager.get_token()
        return {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {token}",
            "appkey": Config.APP_KEY,
            "appsecret": Config.APP_SECRET,
            "tr_id": tr_id,
            "custtype": "P"  # P: Individual customer
        }

    def request(
        self,
        method: str,
        path: str,
        tr_id: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
        backoff_factor: float = 1.0,
        timeout: int = 10
    ) -> Dict[str, Any]:
        """Performs an HTTP request with automatic headers, logging, and retry logic."""
        url = f"{Config.BASE_URL}{path}"
        headers = self._get_headers(tr_id)
        
        # Safe logging (do not log sensitive headers)
        logger.debug(f"Sending {method} request to {url} with tr_id: {tr_id}")

        for attempt in range(1, max_retries + 1):
            try:
                if method.upper() == "GET":
                    # KIS requires GET parameters to be query strings, and headers to have tr_id
                    response = requests.get(url, headers=headers, params=params, timeout=timeout)
                elif method.upper() == "POST":
                    response = requests.post(url, headers=headers, json=json_data, timeout=timeout)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                # Check if it was successful (2xx)
                response.raise_for_status()
                response_json = response.json()

                # Korea Investment API returns error codes inside JSON responses even with HTTP 200.
                # Usually, rt_cd != '0' (or not present/successful) indicates failure.
                # Let's inspect KIS specific return codes: 'rt_cd' ('0' is success, others are error)
                rt_cd = response_json.get("rt_cd")
                msg_code = response_json.get("msg_cd")
                msg = response_json.get("msg1", "")

                if rt_cd is not None and rt_cd != "0":
                    logger.error(
                        f"API logical error response: Code={msg_code}, Message='{msg}' (tr_id: {tr_id})"
                    )
                    # We still return the JSON since callers might want to parse error specifics
                    return response_json

                return response_json

            except requests.exceptions.RequestException as e:
                logger.warning(
                    f"Request attempt {attempt}/{max_retries} failed for {url}: {e}."
                )
                if attempt == max_retries:
                    logger.error(f"Max retries reached for {url}.")
                    raise
                
                # Exponential backoff sleep
                sleep_time = backoff_factor * (2 ** (attempt - 1))
                logger.info(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)

        raise RuntimeError("Unexpected end of retry loop")

    def get(self, path: str, tr_id: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Helper for GET requests."""
        return self.request("GET", path, tr_id, params=params)

    def post(self, path: str, tr_id: str, json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Helper for POST requests."""
        return self.request("POST", path, tr_id, json_data=json_data)
