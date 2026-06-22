import sys
import traceback
from samsung_auto_trader.config import Config, ConfigError
from samsung_auto_trader.logger import logger
from samsung_auto_trader.trader import Trader

def main() -> None:
    logger.info("=== Korea Investment Open API Samsung Electronics Auto-Trader ===")
    
    try:
        # Load and validate credentials from environmental variables/dotenv
        Config.load_and_validate()
        logger.info("Configuration loaded and validated successfully.")
        
        # Log active configuration settings (hiding secret values)
        logger.info(f"Active Settings: {Config.to_dict()}")

    except ConfigError as ce:
        logger.critical(f"Configuration Error: {ce}")
        logger.critical(
            "Please ensure you have configured your .env file or environment variables: "
            "GH_ACCOUNT, GH_APPKEY, GH_APPSECRET"
        )
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error loading configuration: {e}")
        sys.exit(1)

    # Initialize and run the trader
    try:
        trader = Trader()
        trader.run()
    except KeyboardInterrupt:
        logger.info("Auto-Trader terminated by user (KeyboardInterrupt).")
    except Exception as e:
        logger.critical(f"Fatal error occurred in the execution loop: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
