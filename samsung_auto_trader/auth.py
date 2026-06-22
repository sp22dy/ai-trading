import json
import os
import time
from datetime import datetime
from typing import Optional, Dict, Any
import requests
from samsung_auto_trader.config import Config
from samsung_auto_trader.logger import logger

class TokenManager:
    """Manages the generation, reuse, and disk caching of KIS OAuth Access Tokens."""

    def __init__(self, cache_file: str = Config.TOKEN_CACHE_FILE) -> None:
        # Resolve cache path relative to this file's folder to ensure consistency
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.cache_path = os.path.join(base_dir, cache_file)

    def _load_cache(self) -> Optional[Dict[str, Any]]:
        """Loads cached token info from disk if it exists and is valid JSON."""
        if not os.path.exists(self.cache_path):
            return None
        try:
            with open(self.cache_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to read token cache file: {e}. Re-authenticating.")
            return None

    def _save_cache(self, token_data: Dict[str, Any]) -> None:
        """Saves token info to disk."""
        try:
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(token_data, f, ensure_ascii=False, indent=2)
            logger.info("Access token successfully cached locally.")
        except Exception as e:
            logger.warning(f"Failed to write token cache file: {e}")

    def _is_token_valid(self, cache_data: Dict[str, Any]) -> bool:
        """Checks if the cached token is valid and has not expired."""
        access_token = cache_data.get("access_token")
        expires_at_str = cache_data.get("expires_at")  # Format: "YYYY-MM-DD HH:MM:SS"

        if not access_token or not expires_at_str:
            return False

        try:
            # KIS expires_at is given in local KST timezone
            expiry_dt = datetime.strptime(expires_at_str, "%Y-%m-%d %H:%M:%S")
            # Subtract a 5-minute safety buffer
            now = datetime.now()
            is_valid = expiry_dt > now
            if not is_valid:
                logger.info(f"Cached token has expired. Expiry: {expires_at_str}, Current Time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
            return is_valid
        except Exception as e:
            logger.error(f"Error parsing token expiration datetime: {e}")
            return False

    def get_token(self) -> str:
        """Returns a valid access token. Uses cache if valid, otherwise requests a new one."""
        cache_data = self._load_cache()

        if cache_data and self._is_token_valid(cache_data):
            logger.info("Reusing cached OAuth access token.")
            return cache_data["access_token"]

        logger.info("Requesting a new KIS OAuth access token...")
        url = f"{Config.BASE_URL}/oauth2/tokenP"
        headers = {"content-type": "application/json"}
        payload = {
            "grant_type": "client_credentials",
            "appkey": Config.APP_KEY,
            "appsecret": Config.APP_SECRET
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()

            access_token = data.get("access_token")
            # The API returns token expiration time in 'access_token_token_expired'
            expires_at = data.get("access_token_token_expired")

            if not access_token or not expires_at:
                raise ValueError(f"Invalid auth response schema: {data}")

            # Cache the token
            self._save_cache({
                "access_token": access_token,
                "expires_at": expires_at
            })

            logger.info("Successfully fetched new OAuth access token.")
            return access_token

        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP request error during token issuance: {e}")
            # If the server is down or we got a temporary network error,
            # try to fallback to the cached token if one exists even if technically expired
            if cache_data and cache_data.get("access_token"):
                logger.warning("Network error, attempting to fallback to expired cached token as last resort.")
                return cache_data["access_token"]
            raise
        except Exception as e:
            logger.error(f"Token generation failed: {e}")
            raise
