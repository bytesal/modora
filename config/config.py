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
    
    # Database names
    DB_NAME = "modmail_db"
    
    # Collection names
    COLL_GUILDS = "guild_configs"
    COLL_TICKETS = "tickets"
    COLL_LOGS = "logs"

config = Config()
