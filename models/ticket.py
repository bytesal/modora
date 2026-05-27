from enum import Enum
from datetime import datetime
from typing import Optional

class TicketStatus(str, Enum):
    OPEN = "open"
    CLAIMED = "claimed"
    CLOSED = "closed"
    REOPENED = "reopened"

class Ticket:
    """Schema for a ModMail ticket."""
    def __init__(self, user_id: int, guild_id: int, data: dict = None):
        if data:
            self.ticket_id = data.get("ticket_id")
            self.user_id = data.get("user_id")
            self.guild_id = data.get("guild_id")
            self.channel_id = data.get("channel_id")
            self.staff_id = data.get("staff_id")
            self.status = TicketStatus(data.get("status", "open"))
            self.created_at = data.get("created_at")
            self.last_activity = data.get("last_activity")
            self.closed_at = data.get("closed_at")
            self.transcript_url = data.get("transcript_url")
        else:
            self.ticket_id = None
            self.user_id = user_id
            self.guild_id = guild_id
            self.channel_id = None
            self.staff_id = None
            self.status = TicketStatus.OPEN
            now = datetime.utcnow()
            self.created_at = now
            self.last_activity = now
            self.closed_at = None
            self.transcript_url = None

    def to_dict(self) -> dict:
        return {
            "ticket_id": self.ticket_id,
            "user_id": self.user_id,
            "guild_id": self.guild_id,
            "channel_id": self.channel_id,
            "staff_id": self.staff_id,
            "status": self.status.value,
            "created_at": self.created_at,
            "last_activity": self.last_activity,
            "closed_at": self.closed_at,
            "transcript_url": self.transcript_url,
        }
