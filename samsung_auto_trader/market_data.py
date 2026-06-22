from typing import Optional
from samsung_auto_trader.config import Config
from samsung_auto_trader.api_client import KISApiClient
from samsung_auto_trader.logger import logger

class MarketDataService:
    """Service to query market data from KIS Open API."""

    def __init__(self, api_client: Optional[KISApiClient] = None) -> None:
        self.client = api_client or KISApiClient()

    def get_current_price(self, stock_code: str = Config.STOCK_CODE) -> int:
        """
        Retrieves the current market price for a given stock code.
        
        Endpoint: /uapi/domestic-stock/v1/quotations/inquire-price
        TR ID: FHKST01010100
        """
        path = "/uapi/domestic-stock/v1/quotations/inquire-price"
        tr_id = "FHKST01010100"
        
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",  # J: Stock/ETF
            "FID_INPUT_ISCD": stock_code
        }

        try:
            res = self.client.get(path, tr_id=tr_id, params=params)
            
            # Check response code
            if res.get("rt_cd") != "0":
                raise RuntimeError(f"Failed to fetch market price: {res.get('msg1')}")
            
            output = res.get("output", {})
            stck_prpr = output.get("stck_prpr")
            
            if not stck_prpr:
                raise ValueError(f"stck_prpr field is missing in KIS response output: {output}")

            price = int(stck_prpr)
            logger.info(f"Market Price Checked - Symbol: {stock_code}, Price: {price:,} KRW")
            return price

        except Exception as e:
            logger.error(f"Error occurred while fetching current price for {stock_code}: {e}")
            raise
