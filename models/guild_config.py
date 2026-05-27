from typing import List, Optional
from datetime import datetime

class GuildConfig:
    """Schema for guild configuration."""
    def __init__(self, guild_id: int, data: dict = None):
        self.guild_id = guild_id
        if data:
            self.category_id = data.get("category_id")
            self.staff_role_ids = data.get("staff_role_ids", [])
            self.logs_channel_id = data.get("logs_channel_id")
            self.transcripts_channel_id = data.get("transcripts_channel_id")
            self.panel_channel_id = data.get("panel_channel_id")
            self.panel_message_id = data.get("panel_message_id")
            self.auto_close_minutes = data.get("auto_close_minutes", 30)
            self.cooldown_seconds = data.get("cooldown_seconds", 300)
            self.created_at = data.get("created_at", datetime.utcnow())
            self.updated_at = data.get("updated_at", datetime.utcnow())
        else:
            self.category_id = None
            self.staff_role_ids = []
            self.logs_channel_id = None
            self.transcripts_channel_id = None
            self.panel_channel_id = None
            self.panel_message_id = None
            self.auto_close_minutes = 30
            self.cooldown_seconds = 300
            self.created_at = datetime.utcnow()
            self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        return {
            "guild_id": self.guild_id,
            "category_id": self.category_id,
            "staff_role_ids": self.staff_role_ids,
            "logs_channel_id": self.logs_channel_id,
            "transcripts_channel_id": self.transcripts_channel_id,
            "panel_channel_id": self.panel_channel_id,
            "panel_message_id": self.panel_message_id,
            "auto_close_minutes": self.auto_close_minutes,
            "cooldown_seconds": self.cooldown_seconds,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
