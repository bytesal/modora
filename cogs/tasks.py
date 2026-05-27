import discord
from discord.ext import commands, tasks
from services.ticket_service import TicketService
from services.guild_config_service import GuildConfigService
from services.log_service import LogService
from utils.logger import get_logger
from datetime import datetime, timedelta
import asyncio

logger = get_logger(__name__)

class TasksCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.ticket_service = TicketService(bot.db)
        self.config_service = GuildConfigService(bot.db)
        self.log_service = LogService(bot)
        self.auto_close_loop.start()
    
    def cog_unload(self):
        self.auto_close_loop.cancel()
    
    @tasks.loop(minutes=1.0)
    async def auto_close_loop(self):
        """Background task to close inactive tickets."""
        await self.bot.wait_until_ready()
        logger.debug("Running auto-close check...")
        
        # Get all open tickets from all guilds
        open_tickets = await self.ticket_service.get_all_open_tickets()
        
        for ticket in open_tickets:
            # Get guild config for auto-close setting
            config = await self.config_service.get_config(ticket.guild_id)
            if not config.auto_close_minutes or config.auto_close_minutes <= 0:
                continue  # Auto-close disabled
            
            # Check if last activity is older than auto_close_minutes
            last_active = ticket.last_activity
            if not last_active:
                last_active = ticket.created_at
            
            cutoff = datetime.utcnow() - timedelta(minutes=config.auto_close_minutes)
            if last_active < cutoff:
                # Ticket is inactive - close it
                logger.info(f"Auto-closing ticket {ticket.ticket_id} due to inactivity")
                
                # Get guild and channel
                guild = self.bot.get_guild(ticket.guild_id)
                if not guild:
                    continue
                
                channel = guild.get_channel(ticket.channel_id)
                if channel:
                    # Send notification before closing
                    try:
                        await channel.send("⏰ This ticket is being closed due to inactivity.")
                        await asyncio.sleep(2)
                    except:
                        pass
                    
                    # Delete the channel
                    try:
                        await channel.delete()
                    except Exception as e:
                        logger.error(f"Failed to delete channel {ticket.channel_id}: {e}")
                
                # Close ticket in database
                await self.ticket_service.close_ticket(ticket, closed_by=None)
                
                # Send log
                await self.log_service.log_auto_close(ticket.guild_id, ticket, "Inactivity")
    
    @auto_close_loop.before_loop
    async def before_auto_close(self):
        await self.bot.wait_until_ready()

async def setup(bot: commands.Bot):
    await bot.add_cog(TasksCog(bot))
