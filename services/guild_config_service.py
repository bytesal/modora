from typing import Optional, List
from database.mongo import MongoDB
from models.guild_config import GuildConfig
from config.config import config as app_config
import logging

logger = logging.getLogger(__name__)

class GuildConfigService:
    def __init__(self, db: MongoDB):
        self.db = db
        self.collection_name = app_config.COLL_GUILDS

    async def _get_collection(self):
        return await self.db.get_collection(self.collection_name)

    async def get_config(self, guild_id: int) -> GuildConfig:
        """Retrieve guild configuration, return default if not found."""
        collection = await self._get_collection()
        data = await collection.find_one({"guild_id": guild_id})
        if data:
            return GuildConfig(guild_id, data)
        return GuildConfig(guild_id)

    async def update_config(self, guild_id: int, update_data: dict) -> GuildConfig:
        """Update guild configuration with given fields."""
        collection = await self._get_collection()
        update_data["updated_at"] = datetime.utcnow()
        await collection.update_one(
            {"guild_id": guild_id},
            {"$set": update_data},
            upsert=True
        )
        return await self.get_config(guild_id)

    async def set_category(self, guild_id: int, category_id: int):
        config = await self.get_config(guild_id)
        config.category_id = category_id
        await self.update_config(guild_id, {"category_id": category_id})

    async def add_staff_role(self, guild_id: int, role_id: int):
        config = await self.get_config(guild_id)
        if role_id not in config.staff_role_ids:
            config.staff_role_ids.append(role_id)
            await self.update_config(guild_id, {"staff_role_ids": config.staff_role_ids})

    async def remove_staff_role(self, guild_id: int, role_id: int):
        config = await self.get_config(guild_id)
        if role_id in config.staff_role_ids:
            config.staff_role_ids.remove(role_id)
            await self.update_config(guild_id, {"staff_role_ids": config.staff_role_ids})

    async def set_logs_channel(self, guild_id: int, channel_id: int):
        await self.update_config(guild_id, {"logs_channel_id": channel_id})

    async def set_transcripts_channel(self, guild_id: int, channel_id: int):
        await self.update_config(guild_id, {"transcripts_channel_id": channel_id})

    async def set_panel_channel(self, guild_id: int, channel_id: int):
        await self.update_config(guild_id, {"panel_channel_id": channel_id})

    async def set_panel_message(self, guild_id: int, message_id: int):
        await self.update_config(guild_id, {"panel_message_id": message_id})

    async def reset_config(self, guild_id: int):
        collection = await self._get_collection()
        await collection.delete_one({"guild_id": guild_id})

from datetime import datetime
