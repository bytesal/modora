from database.mongo import MongoDB
from config.config import config as app_config
import logging

logger = logging.getLogger(__name__)

class BlacklistManager:
    """Manage global blacklist for users and guilds."""
    
    def __init__(self, db: MongoDB):
        self.db = db
        self.collection_name = "blacklist"
    
    async def _get_collection(self):
        return await self.db.get_collection(self.collection_name)
    
    async def add_blacklist(self, item_id: int, item_type: str, reason: str = None, moderator_id: int = None):
        """Add a user or guild to blacklist."""
        collection = await self._get_collection()
        data = {
            "_id": item_id,
            "type": item_type,
            "reason": reason,
            "moderator_id": moderator_id,
            "created_at": datetime.utcnow()
        }
        await collection.update_one({"_id": item_id}, {"$set": data}, upsert=True)
        logger.info(f"Blacklisted {item_type} {item_id}: {reason}")
    
    async def remove_blacklist(self, item_id: int):
        """Remove a user or guild from blacklist."""
        collection = await self._get_collection()
        result = await collection.delete_one({"_id": item_id})
        if result.deleted_count:
            logger.info(f"Removed blacklist for {item_id}")
        return result.deleted_count > 0
    
    async def is_blacklisted(self, item_id: int, item_type: str = None) -> bool:
        """Check if a user or guild is blacklisted. If item_type provided, check specific type."""
        collection = await self._get_collection()
        query = {"_id": item_id}
        if item_type:
            query["type"] = item_type
        doc = await collection.find_one(query)
        return doc is not None
    
    async def get_all_blacklisted(self, item_type: str = None) -> list:
        """Get all blacklisted items, optionally filtered by type."""
        collection = await self._get_collection()
        query = {}
        if item_type:
            query["type"] = item_type
        cursor = collection.find(query)
        results = []
        async for doc in cursor:
            results.append({
                "id": doc["_id"],
                "type": doc["type"],
                "reason": doc.get("reason"),
                "moderator_id": doc.get("moderator_id"),
                "created_at": doc.get("created_at")
            })
        return results

from datetime import datetime
