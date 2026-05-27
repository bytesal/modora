import logging
import sys
from config.config import config

def setup_logger(name: str = "modmail_bot") -> logging.Logger:
    """Configure and return a logger with console and optional webhook handler."""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, config.LOG_LEVEL.upper(), logging.INFO))
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(console_handler)
    
    # Optional webhook handler (will be added later in main when bot is ready)
    # For now, just console
    
    return logger

def get_logger(name: str = None) -> logging.Logger:
    """Get a logger instance."""
    if name:
        return logging.getLogger(f"modmail_bot.{name}")
    return logging.getLogger("modmail_bot")
