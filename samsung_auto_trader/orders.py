from typing import Optional, Dict, Any
from samsung_auto_trader.config import Config
from samsung_auto_trader.api_client import KISApiClient
from samsung_auto_trader.logger import logger

class OrderService:
    """Service to submit and manage stock orders via KIS Open API (Mock Trading)."""

    def __init__(self, api_client: Optional[KISApiClient] = None) -> None:
        self.client = api_client or KISApiClient()

    def place_order(
        self,
        stock_code: str,
        qty: int,
        price: int,
        is_buy: bool
    ) -> Dict[str, Any]:
        """
        Places a domestic cash order (Limit Order).
        
        Endpoint: /uapi/domestic-stock/v1/trading/order-cash
        TR IDs (Mock Trading):
          - Cash Buy: VTTC0012U
          - Cash Sell: VTTC0011U
        """
        path = "/uapi/domestic-stock/v1/trading/order-cash"
        
        # Determine TR ID based on action
        if is_buy:
            tr_id = "VTTC0012U"  # Mock cash buy
            action_name = "BUY"
        else:
            tr_id = "VTTC0011U"  # Mock cash sell
            action_name = "SELL"

        # KIS expects ORD_QTY and ORD_UNPR as string representations
        payload = {
            "CANO": Config.CANO,
            "ACNT_PRDT_CD": Config.ACNT_PRDT_CD,
            "PDNO": stock_code,
            "ORD_DVSN": "00",           # 00: Limit Order (지정가)
            "ORD_QTY": str(qty),
            "ORD_UNPR": str(price)
        }

        logger.info(
            f"Placing Cash {action_name} Order - Symbol: {stock_code}, "
            f"Qty: {qty}, Price: {price:,} KRW (tr_id: {tr_id})"
        )

        try:
            res = self.client.post(path, tr_id=tr_id, json_data=payload)
            
            rt_cd = res.get("rt_cd")
            msg = res.get("msg1", "").strip()
            msg_cd = res.get("msg_cd", "")

            if rt_cd != "0":
                logger.error(
                    f"Order Submission Failed - Type: {action_name}, "
                    f"Code: {msg_cd}, Message: '{msg}'"
                )
                return {
                    "success": False,
                    "order_no": "",
                    "message": msg,
                    "response": res
                }

            output = res.get("output", {})
            odno = output.get("ODNO", "").strip()  # Order number

            logger.info(
                f"Order Successfully Submitted - Type: {action_name}, "
                f"Order No: '{odno}', Message: '{msg}'"
            )

            return {
                "success": True,
                "order_no": odno,
                "message": msg,
                "response": res
            }

        except Exception as e:
            logger.error(f"Exception raised during {action_name} order placement: {e}")
            raise
class OrderServiceMock(OrderService):
    """Mock OrderService that doesn't place actual orders, useful for dry-run testing."""
    
    def place_order(
        self,
        stock_code: str,
        qty: int,
        price: int,
        is_buy: bool
    ) -> Dict[str, Any]:
        action_name = "BUY" if is_buy else "SELL"
        logger.info(
            f"[MOCK ORDER] Placing Cash {action_name} Order - Symbol: {stock_code}, "
            f"Qty: {qty}, Price: {price:,} KRW"
        )
        return {
            "success": True,
            "order_no": "MOCK_ORDER_123456",
            "message": "Mock order placed successfully",
            "response": {"rt_cd": "0", "msg1": "정상처리(모의)"}
        }
