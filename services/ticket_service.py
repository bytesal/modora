import discord
from typing import Optional, List
from datetime import datetime
from database.mongo import MongoDB
from models.ticket import Ticket, TicketStatus
from models.guild_config import GuildConfig
from config.config import config as app_config
from utils.helpers import generate_ticket_id
import logging

logger = logging.getLogger(__name__)

class TicketService:
    def __init__(self, db: MongoDB):
        self.db = db
        self.collection_name = app_config.COLL_TICKETS

    async def _get_collection(self):
        return await self.db.get_collection(self.collection_name)

    async def create_ticket(self, user_id: int, guild_id: int, channel_id: int) -> Ticket:
        """Create a new ticket document in database."""
        collection = await self._get_collection()
        ticket = Ticket(user_id, guild_id)
        ticket.ticket_id = generate_ticket_id()
        ticket.channel_id = channel_id
        ticket.status = TicketStatus.OPEN
        await collection.insert_one(ticket.to_dict())
        return ticket

    async def create_ticket_channel(self, guild: discord.Guild, user: discord.User, config: GuildConfig) -> Optional[discord.TextChannel]:
        """Create a private text channel for the ticket."""
        if not config.category_id:
            logger.error(f"No category set for guild {guild.id}")
            return None
        
        category = guild.get_channel(config.category_id)
        if not category or not isinstance(category, discord.CategoryChannel):
            logger.error(f"Invalid category ID {config.category_id} for guild {guild.id}")
            return None
        
        # Channel name: ticket-username or ticket-userid
        name = f"ticket-{user.name.lower().replace(' ', '-')[:80]}-{user.discriminator if user.discriminator != '0' else user.id}"
        name = name[:100]  # Discord limit
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True, embed_links=True),
        }
        # Add staff roles
        for role_id in config.staff_role_ids:
            role = guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        
        try:
            channel = await guild.create_text_channel(name, category=category, overwrites=overwrites)
            # Create database entry
            ticket = await self.create_ticket(user.id, guild.id, channel.id)
            return channel
        except Exception as e:
            logger.error(f"Failed to create ticket channel: {e}")
            return None

    async def get_open_ticket(self, user_id: int, guild_id: int = None) -> Optional[Ticket]:
        """Get an open ticket for a user (optionally in specific guild)."""
        collection = await self._get_collection()
        query = {"user_id": user_id, "status": {"$in": ["open", "claimed", "reopened"]}}
        if guild_id:
            query["guild_id"] = guild_id
        data = await collection.find_one(query)
        if data:
            return Ticket(data["user_id"], data.get("guild_id"), data)
        return None

    async def get_ticket_by_channel(self, channel_id: int) -> Optional[Ticket]:
        """Get ticket by channel ID."""
        collection = await self._get_collection()
        data = await collection.find_one({"channel_id": channel_id})
        if data:
            return Ticket(data["user_id"], data["guild_id"], data)
        return None

    async def get_ticket_by_id(self, ticket_id: str) -> Optional[Ticket]:
        """Get a ticket by its unique ticket ID."""
        collection = await self._get_collection()
        data = await collection.find_one({"ticket_id": ticket_id})
        if data:
            return Ticket(data["user_id"], data["guild_id"], data)
        return None

    async def get_all_open_tickets(self) -> List[Ticket]:
        """Get all tickets with status open, claimed, or reopened."""
        collection = await self._get_collection()
        cursor = collection.find({"status": {"$in": ["open", "claimed", "reopened"]}})
        tickets = []
        async for data in cursor:
            tickets.append(Ticket(data["user_id"], data["guild_id"], data))
        return tickets

    async def update_activity(self, ticket_id: str):
        """Update last_activity timestamp for a ticket."""
        collection = await self._get_collection()
        await collection.update_one(
            {"ticket_id": ticket_id},
            {"$set": {"last_activity": datetime.utcnow()}}
        )

    async def claim_ticket(self, ticket_id: str, staff_id: int):
        """Claim a ticket."""
        collection = await self._get_collection()
        await collection.update_one(
            {"ticket_id": ticket_id},
            {"$set": {"staff_id": staff_id, "status": TicketStatus.CLAIMED.value}}
        )

    async def close_ticket(self, ticket: Ticket, closed_by: Optional[int] = None):
        """Mark ticket as closed (but keep in database)."""
        collection = await self._get_collection()
        await collection.update_one(
            {"ticket_id": ticket.ticket_id},
            {"$set": {"status": TicketStatus.CLOSED.value, "closed_at": datetime.utcnow()}}
        )
