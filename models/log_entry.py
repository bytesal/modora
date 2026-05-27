from enum import Enum
from datetime import datetime
from typing import Optional

class LogType(str, Enum):
    TICKET_CREATE = "ticket_create"
    TICKET_CLOSE = "ticket_close"
    TICKET_REOPEN = "ticket_reopen"
    TICKET_CLAIM = "ticket_claim"
    STAFF_REPLY = "staff_reply"
    USER_REPLY = "user_reply"
    TRANSCRIPT = "transcript"
    ERROR = "error"
    COMMAND = "command"

class LogEntry:
    """Schema for log entries."""
    def __init__(self, guild_id: int, log_type: LogType, data: dict):
        self.guild_id = guild_id
        self.log_type = log_type
        self.data = data
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> dict:
        return {
            "guild_id": self.guild_id,
            "log_type": self.log_type.value,
            "data": self.data,
            "timestamp": self.timestamp,
        }
