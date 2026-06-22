import logging
import os
import sys

def setup_logger(name: str = "trader", log_file: str = "trader.log", level: int = logging.INFO) -> logging.Logger:
    """Configures and returns a logger that logs to both console and file."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent adding duplicate handlers if setup_logger is called multiple times
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] (%(filename)s:%(lineno)d) - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler
    try:
        # Save logs in the same directory as the script or workspace directory
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Failed to set up log file '{log_file}': {e}", file=sys.stderr)

    return logger

# Create a default logger instance
logger = setup_logger()
