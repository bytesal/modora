import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN not set in environment")
    
    MONGO_URI = os.getenv("MONGO_URI")
    if not MONGO_URI:
        raise ValueError("MONGO_URI not set in environment")
    
    BOT_PREFIX = os.getenv("BOT_PREFIX", "/")
    BOT_ACTIVITY = os.getenv("BOT_ACTIVITY", "ModMail | /help")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    ERROR_WEBHOOK_URL = os.getenv("ERROR_WEBHOOK_URL")
    
    DB_NAME = os.getenv("DB_NAME", "modmail_db")
    COLL_GUILDS = "guild_configs"
    COLL_TICKETS = "tickets"
    COLL_LOGS = "logs"
    
    MONGO_MAX_POOL_SIZE = int(os.getenv("MONGO_MAX_POOL_SIZE", "10"))
    MONGO_MIN_POOL_SIZE = int(os.getenv("MONGO_MIN_POOL_SIZE", "1"))
    MONGO_MAX_IDLE_TIME_MS = int(os.getenv("MONGO_MAX_IDLE_TIME_MS", "10000"))
    
    # Railway provides PORT, default to 8080
    HEALTH_CHECK_PORT = int(os.getenv("PORT", "8080"))
    
    MAX_MESSAGES_CACHE = int(os.getenv("MAX_MESSAGES_CACHE", "1000"))
    DISABLE_VOICE = os.getenv("DISABLE_VOICE", "True").lower() == "true"

config = Config()
