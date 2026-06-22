import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load .env file if it exists in the current directory or parent directories
load_dotenv()

class ConfigError(ValueError):
    """Exception raised when configuration is invalid or missing."""
    pass

class Config:
    # KIS API Credentials
    APP_KEY: str = ""
    APP_SECRET: str = ""
    ACCOUNT_NO: str = ""
    CANO: str = ""
    ACNT_PRDT_CD: str = ""

    # KIS API URL Settings (Mock Trading Only)
    BASE_URL: str = "https://openapivts.koreainvestment.com:29443"

    # Trading Parameters
    STOCK_CODE: str = "005930"  # Samsung Electronics
    ORDER_PRICE_OFFSET: int = 2000  # Offset in KRW for buy/sell orders (current_price +/- offset)
    POLLING_INTERVAL_SECONDS: int = 30  # Safety interval to prevent mock trading rate limiting

    # Trading Window Settings
    TRADING_WINDOW_START: str = "09:10"  # HH:MM
    TRADING_WINDOW_END: str = "21:30"    # HH:MM

    # Cache File Path
    TOKEN_CACHE_FILE: str = "token_cache.json"

    @classmethod
    def load_and_validate(cls) -> None:
        """Loads and validates all environment credentials."""
        cls.APP_KEY = os.getenv("GH_APPKEY", "").strip()
        cls.APP_SECRET = os.getenv("GH_APPSECRET", "").strip()
        cls.ACCOUNT_NO = os.getenv("GH_ACCOUNT", "").strip()

        if not cls.APP_KEY:
            raise ConfigError("Missing environment variable: GH_APPKEY")
        if not cls.APP_SECRET:
            raise ConfigError("Missing environment variable: GH_APPSECRET")
        if not cls.ACCOUNT_NO:
            raise ConfigError("Missing environment variable: GH_ACCOUNT")

        # Validate and parse Account Number (Must be 8 or 10 digits)
        # Remove any dashes if present
        clean_acc = cls.ACCOUNT_NO.replace("-", "")
        if not clean_acc.isdigit():
            raise ConfigError(
                f"Invalid GH_ACCOUNT format: '{cls.ACCOUNT_NO}'. "
                "Must be a numeric account number."
            )
        
        if len(clean_acc) == 8:
            cls.CANO = clean_acc
            cls.ACNT_PRDT_CD = "01"  # Default product code for stock accounts
        elif len(clean_acc) == 10:
            cls.CANO = clean_acc[:8]          # First 8 digits (종합계좌번호)
            cls.ACNT_PRDT_CD = clean_acc[8:]   # Last 2 digits (계좌상품코드)
        else:
            raise ConfigError(
                f"Invalid GH_ACCOUNT length: '{cls.ACCOUNT_NO}'. "
                "Must be either an 8-digit or 10-digit numeric account number."
            )

    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """Returns non-sensitive configuration parameters for logging."""
        return {
            "BASE_URL": cls.BASE_URL,
            "STOCK_CODE": cls.STOCK_CODE,
            "ORDER_PRICE_OFFSET": cls.ORDER_PRICE_OFFSET,
            "POLLING_INTERVAL_SECONDS": cls.POLLING_INTERVAL_SECONDS,
            "TRADING_WINDOW_START": cls.TRADING_WINDOW_START,
            "TRADING_WINDOW_END": cls.TRADING_WINDOW_END,
            "CANO": cls.CANO,
            "ACNT_PRDT_CD": cls.ACNT_PRDT_CD
        }
