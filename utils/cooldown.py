import time
from database.mongo import MongoDB
from config.config import config as app_config

class CooldownManager:
    """MongoDB-based cooldown tracker for ticket creation."""
    
    def __init__(self, db: MongoDB):
        self.db = db
        self.collection_name = "cooldowns"
    
    async def _get_collection(self):
        return await self.db.get_collection(self.collection_name)
    
    async def check_cooldown(self, user_id: int, guild_id: int, cooldown_seconds: int) -> bool:
        """
        Check if user is on cooldown.
        Returns True if on cooldown, False otherwise.
        Also updates the cooldown if not on cooldown.
        """
        if cooldown_seconds <= 0:
            return False  # Cooldown disabled
        
        collection = await self._get_collection()
        key = f"{guild_id}:{user_id}"
        now = time.time()
        
        doc = await collection.find_one({"_id": key})
        if doc and doc["expires_at"] > now:
            return True  # Still on cooldown
        
        # Set new cooldown
        expires_at = now + cooldown_seconds
        await collection.update_one(
            {"_id": key},
            {"$set": {"expires_at": expires_at}},
            upsert=True
        )
        return False
    
    async def get_remaining_cooldown(self, user_id: int, guild_id: int, cooldown_seconds: int) -> int:
        """Get remaining cooldown seconds (0 if not on cooldown)."""
        if cooldown_seconds <= 0:
            return 0
        
        collection = await self._get_collection()
        key = f"{guild_id}:{user_id}"
        now = time.time()
        
        doc = await collection.find_one({"_id": key})
        if doc and doc["expires_at"] > now:
            return int(doc["expires_at"] - now)
        return 0
    
    async def clear_cooldown(self, user_id: int, guild_id: int):
        """Manually clear cooldown for a user (admin command)."""
        collection = await self._get_collection()
        key = f"{guild_id}:{user_id}"
        await collection.delete_one({"_id": key})
