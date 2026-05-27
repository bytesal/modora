import logging
import sys
from config.config import config
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for Railway logs."""
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)

def setup_logger(name: str = "modmail_bot") -> logging.Logger:
    """Configure and return a logger with console handler."""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, config.LOG_LEVEL.upper(), logging.INFO))
    
    # Console handler with JSON formatter for Railway (better parsing)
    console_handler = logging.StreamHandler(sys.stdout)
    
    # Use JSON formatter on Railway, otherwise simple text
    if config.LOG_LEVEL.upper() == "DEBUG":
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
    else:
        console_handler.setFormatter(JSONFormatter())
    
    logger.addHandler(console_handler)
    
    return logger

def get_logger(name: str = None) -> logging.Logger:
    """Get a logger instance."""
    if name:
        return logging.getLogger(f"modmail_bot.{name}")
    return logging.getLogger("modmail_bot")
