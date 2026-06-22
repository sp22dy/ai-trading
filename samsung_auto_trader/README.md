# Samsung Electronics KIS Auto-Trader

A modular, REST-only mock trading program for Samsung Electronics (`005930`) using the Korea Investment & Securities (KIS) Open API.

## Prerequisites

1. **Korea Investment & Securities Mock Trading Account**:
   - Apply for mock trading (모의투자) on the KIS Developer Portal/App.
   - Obtain your **Mock Trading App Key** and **App Secret**.
   - Note your 10-digit **Mock Trading Account Number**.

2. **Environment Variables**:
   Create a `.env` file in the root of the project or export the following variables in your terminal:
   ```env
   GH_ACCOUNT="1234567801"      # 10-digit mock trading account number
   GH_APPKEY="your_mock_app_key"
   GH_APPSECRET="your_mock_secret"
   ```

## Directory Structure

```
samsung_auto_trader/
├── main.py              # Entry point
├── config.py            # Environment validation and settings
├── logger.py            # Log setup
├── auth.py              # OAuth token retrieval and caching
├── api_client.py        # KIS base API client
├── market_data.py       # Stock price fetching
├── account.py           # Account balance and holdings check
├── orders.py            # Order placement (buy/sell)
├── trader.py            # Main trading orchestrator
├── token_cache.json     # Token cache (auto-generated)
└── requirements.txt     # Dependencies
```

## How to Run

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Program**:
   ```bash
   python main.py
   ```

## Trading Logic & Parameters

- **Target Stock**: Samsung Electronics (`005930`)
- **Trading Window**: `09:10 AM` to `03:30 PM` (15:30)
- **Strategy**: 
  - Submits a Buy Limit Order at `Current Price - 2,000 KRW`
  - Submits a Sell Limit Order at `Current Price + 2,000 KRW`
  - Verifies holdings and updates status in a loop.
- **Polling Interval**: Defaults to **30 seconds** to comply with mock-trading API limits.
- **Configurability**: Offset price and polling interval can be customized in `config.py`.
