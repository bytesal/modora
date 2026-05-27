from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from config.config import config
import logging

logger = logging.getLogger(__name__)

class MongoDB:
    client: AsyncIOMotorClient = None
    db: AsyncIOMotorDatabase = None

    async def connect(self):
        """Establish connection to MongoDB."""
        try:
            self.client = AsyncIOMotorClient(config.MONGO_URI)
            # Ping the database to verify connection
            await self.client.admin.command('ping')
            self.db = self.client[config.DB_NAME]
            logger.info("Connected to MongoDB")
            
            # Create indexes for performance
            await self._create_indexes()
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
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
        # Logs: timestamp
        await self.db[config.COLL_LOGS].create_index("timestamp")

    async def get_collection(self, collection_name: str):
        """Get a collection from the database."""
        if self.db is None:
            raise RuntimeError("Database not connected")
        return self.db[collection_name]

# Global instance
mongo = MongoDB()
