from typing import Optional, Dict, Any, List
from samsung_auto_trader.config import Config
from samsung_auto_trader.api_client import KISApiClient
from samsung_auto_trader.logger import logger

class AccountService:
    """Service to retrieve account balance and holdings from KIS Open API (Mock Trading)."""

    def __init__(self, api_client: Optional[KISApiClient] = None) -> None:
        self.client = api_client or KISApiClient()

    def get_balance_and_holdings(self, stock_code: str = Config.STOCK_CODE) -> Dict[str, Any]:
        """
        Retrieves total deposit/cash balance and holdings for the specified stock code.
        
        Endpoint: /uapi/domestic-stock/v1/trading/inquire-balance
        TR ID: VTTC8434R (for Mock Trading)
        """
        path = "/uapi/domestic-stock/v1/trading/inquire-balance"
        tr_id = "VTTC8434R"  # Mock trading TR ID for balance inquiry

        # Query parameters required for inquire-balance
        params = {
            "CANO": Config.CANO,
            "ACNT_PRDT_CD": Config.ACNT_PRDT_CD,
            "AFHR_FLPR_YN": "N",            # N: No single price after hours
            "OFL_YN": "",                   # Leave blank or "N"
            "INQR_DVSN": "01",              # 01: By loan date (standard) or 02: By stock
            "UNPR_DVSN": "01",              # 01: Average unit price
            "FUND_STTL_ICLD_YN": "N",       # N: Exclude fund settlement
            "FNCG_AMT_AUTO_EXTN_YN": "N",   # N: Exclude auto credit extension
            "PRCS_DVSN": "00",              # 00: Standard process
            "CTX_AREA_FK100": "",           # Blank for first page
            "CTX_AREA_NK100": ""            # Blank for first page
        }

        try:
            res = self.client.get(path, tr_id=tr_id, params=params)
            
            if res.get("rt_cd") != "0":
                raise RuntimeError(f"Balance check failed: {res.get('msg1')} (Code: {res.get('msg_cd')})")

            # Extract holdings (output1 is typically the list of holding items)
            output1: List[Dict[str, Any]] = res.get("output1", [])
            
            # Find matching stock holding
            target_holding = {
                "stock_code": stock_code,
                "holding_qty": 0,
                "pchs_avg_pric": 0.0,
                "evlu_amt": 0
            }

            for item in output1:
                # pdno is stock symbol/code (e.g. '005930')
                # Remove any whitespace or special characters
                pdno = item.get("pdno", "").strip()
                if pdno == stock_code:
                    target_holding["holding_qty"] = int(item.get("hldg_qty", 0))
                    target_holding["pchs_avg_pric"] = float(item.get("pchs_avg_pric", 0.0))
                    target_holding["evlu_amt"] = int(item.get("evlu_amt", 0))
                    break

            # Extract account balance totals (output2 contains total figures)
            output2_list = res.get("output2", [])
            output2: Dict[str, Any] = {}
            if isinstance(output2_list, list) and len(output2_list) > 0:
                output2 = output2_list[0]
            elif isinstance(output2_list, dict):
                output2 = output2_list

            # dnca_tot_amt is 예수금총액 (deposit total amount)
            # nass_amt is 순자산금액 (net asset amount)
            # prvs_rcvs_amt is 가수수금 (available cash in some contexts, but dnca_tot_amt is more standard)
            try:
                cash_balance = int(output2.get("dnca_tot_amt", 0))
            except (ValueError, TypeError):
                # Fallback to alternative fields if dnca_tot_amt is not found or empty
                cash_balance = int(output2.get("nass_amt", 0))

            logger.info(
                f"Account Checked - Total Cash: {cash_balance:,} KRW | "
                f"Holding Qty: {target_holding['holding_qty']} shares "
                f"(Avg Price: {target_holding['pchs_avg_pric']:,} KRW)"
            )

            return {
                "cash_balance": cash_balance,
                "holding": target_holding,
                "raw_response": res
            }

        except Exception as e:
            logger.error(f"Error occurred while checking account balance and holdings: {e}")
            raise
