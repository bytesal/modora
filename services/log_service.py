import discord
from typing import Optional
from datetime import datetime
from services.guild_config_service import GuildConfigService
from models.ticket import Ticket
from utils.logger import get_logger

logger = get_logger(__name__)

class LogService:
    def __init__(self, bot):
        self.bot = bot
        self.config_service = GuildConfigService(bot.db)
    
    async def send_log(self, guild_id: int, embed: discord.Embed):
        """Send a log embed to the guild's configured logs channel."""
        config = await self.config_service.get_config(guild_id)
        if not config.logs_channel_id:
            return
        
        channel = self.bot.get_channel(config.logs_channel_id)
        if not channel:
            try:
                channel = await self.bot.fetch_channel(config.logs_channel_id)
            except:
                logger.warning(f"Logs channel {config.logs_channel_id} not found for guild {guild_id}")
                return
        
        try:
            await channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Failed to send log to channel {config.logs_channel_id}: {e}")
    
    async def log_ticket_create(self, guild_id: int, user: discord.User, ticket: Ticket, channel: discord.TextChannel):
        """Log when a ticket is created."""
        embed = discord.Embed(
            title="📬 Ticket Created",
            description=f"**User:** {user.mention} ({user.id})\n**Channel:** {channel.mention}\n**Ticket ID:** `{ticket.ticket_id}`",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text=f"User: {user.name}", icon_url=user.display_avatar.url)
        await self.send_log(guild_id, embed)
    
    async def log_ticket_close(self, guild_id: int, user: discord.User, ticket: Ticket, closed_by: discord.User, transcript_url: Optional[str] = None):
        """Log when a ticket is closed."""
        embed = discord.Embed(
            title="🔒 Ticket Closed",
            description=f"**User:** {user.mention} ({user.id})\n**Closed by:** {closed_by.mention}\n**Ticket ID:** `{ticket.ticket_id}`",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        if transcript_url:
            embed.add_field(name="Transcript", value=f"[Click here]({transcript_url})", inline=False)
        await self.send_log(guild_id, embed)
    
    async def log_ticket_claim(self, guild_id: int, ticket: Ticket, staff: discord.User):
        """Log when a ticket is claimed."""
        embed = discord.Embed(
            title="✅ Ticket Claimed",
            description=f**"Ticket ID:** `{ticket.ticket_id}`\n**Channel:** <#{ticket.channel_id}>\n**Claimed by:** {staff.mention}",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        await self.send_log(guild_id, embed)
    
    async def log_ticket_rename(self, guild_id: int, ticket: Ticket, old_name: str, new_name: str, staff: discord.User):
        """Log when a ticket channel is renamed."""
        embed = discord.Embed(
            title="✏️ Ticket Renamed",
            description=f**"Ticket ID:** `{ticket.ticket_id}`\n**Old name:** `{old_name}`\n**New name:** `{new_name}`\n**Renamed by:** {staff.mention}",
            color=discord.Color.gold(),
            timestamp=datetime.utcnow()
        )
        await self.send_log(guild_id, embed)
    
    async def log_user_reply(self, guild_id: int, ticket: Ticket, user: discord.User, content: str):
        """Log when a user replies via DM."""
        embed = discord.Embed(
            title="💬 User Reply",
            description=f**"Ticket ID:** `{ticket.ticket_id}`\n**User:** {user.mention}\n**Message:** {content[:500]}",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        await self.send_log(guild_id, embed)
    
    async def log_staff_reply(self, guild_id: int, ticket: Ticket, staff: discord.User, content: str):
        """Log when a staff replies in ticket channel."""
        embed = discord.Embed(
            title="📨 Staff Reply",
            description=f**"Ticket ID:** `{ticket.ticket_id}`\n**Staff:** {staff.mention}\n**Message:** {content[:500]}",
            color=discord.Color.teal(),
            timestamp=datetime.utcnow()
        )
        await self.send_log(guild_id, embed)
    
    async def log_auto_close(self, guild_id: int, ticket: Ticket, reason: str = "Inactivity"):
        """Log when a ticket is auto-closed due to inactivity."""
        embed = discord.Embed(
            title="⏰ Auto-Closed Ticket",
            description=f**"Ticket ID:** `{ticket.ticket_id}`\n**User:** <@{ticket.user_id}>\n**Channel:** <#{ticket.channel_id}>\n**Reason:** {reason}",
            color=discord.Color.dark_red(),
            timestamp=datetime.utcnow()
        )
        await self.send_log(guild_id, embed)
