import time
from datetime import datetime, time as dt_time
from typing import Optional, Dict, Any
from samsung_auto_trader.config import Config
from samsung_auto_trader.logger import logger
from samsung_auto_trader.api_client import KISApiClient
from samsung_auto_trader.market_data import MarketDataService
from samsung_auto_trader.account import AccountService
from samsung_auto_trader.orders import OrderService

class Trader:
    """Orchestrates the auto-trading loop, timing, and trading logic."""

    def __init__(
        self,
        market_service: Optional[MarketDataService] = None,
        account_service: Optional[AccountService] = None,
        order_service: Optional[OrderService] = None
    ) -> None:
        api_client = KISApiClient()
        self.market_service = market_service or MarketDataService(api_client)
        self.account_service = account_service or AccountService(api_client)
        self.order_service = order_service or OrderService(api_client)

    def _parse_time(self, time_str: str) -> dt_time:
        """Parses "HH:MM" string to a datetime.time object."""
        parts = time_str.split(":")
        return dt_time(int(parts[0]), int(parts[1]))

    def get_trading_window(self) -> tuple[dt_time, dt_time]:
        """Returns the configured start and end times for trading."""
        start = self._parse_time(Config.TRADING_WINDOW_START)
        end = self._parse_time(Config.TRADING_WINDOW_END)
        return start, end

    def is_within_trading_window(self) -> bool:
        """Checks if the current local time falls within the configured trading window."""
        now = datetime.now()
        
        # Check weekday (Monday = 0, Friday = 4, Saturday = 5, Sunday = 6)
        if now.weekday() >= 5:
            logger.debug("Market is closed on weekends.")
            return False

        current_time = now.time()
        start, end = self.get_trading_window()
        return start <= current_time <= end

    def is_after_trading_window(self) -> bool:
        """Checks if the current local time is after the trading window (for automatic shutdown)."""
        now = datetime.now()
        
        # Weekends are considered outside/after normal trading flow for safety shutdown
        if now.weekday() >= 5:
            return True
            
        current_time = now.time()
        _, end = self.get_trading_window()
        return current_time > end

    def execute_trading_cycle(self) -> None:
        """Performs a single cycle of checking price, balance, placing orders, and confirming execution."""
        logger.info("--- Starting New Trading Cycle ---")

        # 1. Check current market price
        try:
            current_price = self.market_service.get_current_price(Config.STOCK_CODE)
        except Exception as e:
            logger.error(f"Cycle aborted: Failed to fetch market price due to: {e}")
            return

        # 2. Check holdings and balance before orders
        try:
            account_info_before = self.account_service.get_balance_and_holdings(Config.STOCK_CODE)
        except Exception as e:
            logger.error(f"Cycle aborted: Failed to fetch account state due to: {e}")
            return

        cash_before = account_info_before["cash_balance"]
        holding_qty_before = account_info_before["holding"]["holding_qty"]

        # Calculate target prices based on offset
        buy_price = current_price - Config.ORDER_PRICE_OFFSET
        sell_price = current_price + Config.ORDER_PRICE_OFFSET

        # Order quantity to submit
        order_qty = 1

        placed_buy = False
        placed_sell = False

        # 3. Place Buy Order (Only if we have enough cash)
        # Note: In Korea, stock trading requires cash to cover the transaction.
        required_buy_cash = buy_price * order_qty
        if cash_before >= required_buy_cash:
            try:
                buy_res = self.order_service.place_order(
                    stock_code=Config.STOCK_CODE,
                    qty=order_qty,
                    price=buy_price,
                    is_buy=True
                )
                placed_buy = buy_res.get("success", False)
            except Exception as e:
                logger.error(f"Error placing buy order: {e}")
        else:
            logger.warning(
                f"Insufficient cash to buy {order_qty} share(s) at {buy_price:,} KRW. "
                f"Available Cash: {cash_before:,} KRW. Skipping buy order."
            )

        # 4. Place Sell Order (Only if we have the holdings to sell)
        if holding_qty_before >= order_qty:
            try:
                sell_res = self.order_service.place_order(
                    stock_code=Config.STOCK_CODE,
                    qty=order_qty,
                    price=sell_price,
                    is_buy=False
                )
                placed_sell = sell_res.get("success", False)
            except Exception as e:
                logger.error(f"Error placing sell order: {e}")
        else:
            logger.info(
                f"No holdings of {Config.STOCK_CODE} available to sell. "
                f"Current Holdings: {holding_qty_before} shares. Skipping sell order."
            )

        # 5. Check balance and holdings after placing orders to verify execution
        if placed_buy or placed_sell:
            # Short sleep to allow the broker system to process/update (mock trading can have a tiny delay)
            time.sleep(2)
            
            try:
                account_info_after = self.account_service.get_balance_and_holdings(Config.STOCK_CODE)
                cash_after = account_info_after["cash_balance"]
                holding_qty_after = account_info_after["holding"]["holding_qty"]

                # Log results of execution check
                cash_diff = cash_after - cash_before
                holding_diff = holding_qty_after - holding_qty_before

                if holding_diff > 0:
                    logger.info(
                        f"Execution confirmed! Buy order filled. "
                        f"Holdings increased: {holding_qty_before} -> {holding_qty_after} (+{holding_diff}). "
                        f"Cash spent: {abs(cash_diff):,} KRW."
                    )
                elif holding_diff < 0:
                    logger.info(
                        f"Execution confirmed! Sell order filled. "
                        f"Holdings decreased: {holding_qty_before} -> {holding_qty_after} ({holding_diff}). "
                        f"Cash received: {cash_diff:,} KRW."
                    )
                else:
                    logger.info(
                        "Orders placed, but no immediate execution detected. "
                        "Orders remain pending in the order book."
                    )

            except Exception as e:
                logger.error(f"Failed to verify execution status: {e}")
        else:
            logger.info("No orders were placed in this cycle.")

    def run(self) -> None:
        """Starts the auto-trading loop."""
        logger.info("Initializing KIS Auto-Trader...")
        start, end = self.get_trading_window()
        logger.info(f"Target Stock: {Config.STOCK_CODE}")
        logger.info(f"Trading Window: {Config.TRADING_WINDOW_START} - {Config.TRADING_WINDOW_END}")
        logger.info(f"Polling Interval: {Config.POLLING_INTERVAL_SECONDS} seconds")

        while True:
            # Check if we are past the trading window for automatic shutdown
            if self.is_after_trading_window():
                logger.info(
                    f"Current time is past the trading window end time ({Config.TRADING_WINDOW_END}). "
                    "Stopping the program automatically."
                )
                break

            # Check if we are currently inside the trading window
            if self.is_within_trading_window():
                try:
                    self.execute_trading_cycle()
                except Exception as e:
                    logger.critical(f"Unhandled exception in trading cycle: {e}")
                
                logger.info(f"Sleeping for {Config.POLLING_INTERVAL_SECONDS} seconds...")
                time.sleep(Config.POLLING_INTERVAL_SECONDS)
            else:
                # Outside the trading window but before it starts (e.g. early morning or weekend)
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                logger.info(
                    f"[{now_str}] Outside trading window ({Config.TRADING_WINDOW_START} - {Config.TRADING_WINDOW_END}). "
                    "Waiting..."
                )
                # Sleep for 1 minute before checking the time again to minimize logs
                time.sleep(60)
        
        logger.info("Auto-Trader has shut down.")
