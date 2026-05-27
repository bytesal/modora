from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from config.config import config
import logging
import asyncio

logger = logging.getLogger(__name__)

class MongoDB:
    client: AsyncIOMotorClient = None
    db: AsyncIOMotorDatabase = None

    async def connect(self):
        """Establish connection to MongoDB with retry logic."""
        retries = 5
        for i in range(retries):
            try:
                self.client = AsyncIOMotorClient(
                    config.MONGO_URI,
                    maxPoolSize=config.MONGO_MAX_POOL_SIZE,
                    minPoolSize=config.MONGO_MIN_POOL_SIZE,
                    maxIdleTimeMS=config.MONGO_MAX_IDLE_TIME_MS,
                    retryWrites=True,
                    retryReads=True
                )
                # Ping the database to verify connection
                await self.client.admin.command('ping')
                self.db = self.client[config.DB_NAME]
                logger.info("Connected to MongoDB")
                
                # Create indexes for performance
                await self._create_indexes()
                return
            except Exception as e:
                logger.error(f"Failed to connect to MongoDB (attempt {i+1}/{retries}): {e}")
                if i < retries - 1:
                    await asyncio.sleep(5)
                else:
                    raise

    async def disconnect(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")

    async def _create_indexes(self):
        """Create necessary indexes for collections."""
        # Guild configs: unique guild ID
        await self.db[config.COLL_GUILDS].create_index("guild_id", unique=True)
        # Tickets: user ID + guild ID for duplicate checks
        await self.db[config.COLL_TICKETS].create_index([("user_id", 1), ("guild_id", 1)])
        await self.db[config.COLL_TICKETS].create_index("channel_id")
        await self.db[config.COLL_TICKETS].create_index("status")
        await self.db[config.COLL_TICKETS].create_index("last_activity")
        # Logs: timestamp
        await self.db[config.COLL_LOGS].create_index("timestamp")
        # Cooldowns: expires_at for TTL (optional, but we'll manage manually)
        await self.db["cooldowns"].create_index("expires_at", expireAfterSeconds=0)

    async def get_collection(self, collection_name: str):
        """Get a collection from the database."""
        if self.db is None:
            raise RuntimeError("Database not connected")
        return self.db[collection_name]

    async def ensure_connection(self):
        """Ensure database is connected; if not, reconnect."""
        if self.client is None or self.db is None:
            await self.connect()

# Global instance
mongo = MongoDB()
